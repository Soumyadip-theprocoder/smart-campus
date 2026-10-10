"""
Views for the Scheduler app.
"""

import datetime

from django.http import HttpResponse
from django_q.tasks import async_task, fetch
from icalendar import Calendar, Event
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Room, Subject, TimeSlot, TimetableEntry, InstitutionSettings, TimetableVersion, AbsenceReport, Notification, TimetableSwapRequest, Department, Amenity, Resource, BlackoutDate
from .serializers import (RoomSerializer, SubjectSerializer,
                          TimeSlotSerializer, TimetableEntrySerializer, InstitutionSettingsSerializer,
                          TimetableVersionSerializer, AbsenceReportSerializer, NotificationSerializer, TimetableSwapRequestSerializer, DepartmentSerializer, AmenitySerializer, ResourceSerializer)


class SubjectListView(generics.ListCreateAPIView):
    """List or create subjects."""

    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.select_related("faculty__user").all()


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a subject."""

    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.select_related("faculty__user").all()


class DepartmentListView(generics.ListCreateAPIView):
    """List or create departments."""
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Department.objects.all()


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a department."""
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Department.objects.all()


class AmenityListView(generics.ListCreateAPIView):
    """List or create amenities."""
    serializer_class = AmenitySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Amenity.objects.all()


class AmenityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an amenity."""
    serializer_class = AmenitySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Amenity.objects.all()


class ResourceListView(generics.ListCreateAPIView):
    """List or create resources."""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Resource.objects.all()


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a resource."""
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Resource.objects.all()


class RoomListView(generics.ListCreateAPIView):
    """List or create rooms."""

    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Room.objects.all()


class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a room."""

    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Room.objects.all()


class TimeSlotListView(generics.ListCreateAPIView):
    """List or create time slots."""

    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimeSlot.objects.all()


class TimeSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a time slot."""

    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimeSlot.objects.all()


class TimetableView(generics.ListAPIView):
    """Get the current timetable."""

    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = TimetableEntry.objects.select_related(
            "subject__faculty__user",
            "room",
            "time_slot",
            "version"
        ).all()
        version_id = self.request.query_params.get("version")
        if version_id:
            qs = qs.filter(version_id=version_id)
        else:
            # Fallback to published version
            published_version = TimetableVersion.objects.filter(is_published=True).first()
            if published_version:
                qs = qs.filter(version_id=published_version.id)
            else:
                qs = qs.none()
        return qs


class TimetableEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a timetable entry."""
    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimetableEntry.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        new_time_slot = serializer.validated_data.get("time_slot", instance.time_slot)
        new_room = serializer.validated_data.get("room", instance.room)
        
        # Check constraints if time_slot or room is changing
        if new_time_slot != instance.time_slot or new_room != instance.room:
            from rest_framework.exceptions import ValidationError
            # 1. Room conflict
            if TimetableEntry.objects.filter(time_slot=new_time_slot, room=new_room).exclude(id=instance.id).exists():
                raise ValidationError({"error": "Room conflict: Another class is scheduled in this room at this time."})
                
            # 2. Faculty conflict & Capacity
            if instance.subject:
                faculty = instance.subject.faculty
                if TimetableEntry.objects.filter(time_slot=new_time_slot, subject__faculty=faculty).exclude(id=instance.id).exists():
                    raise ValidationError({"error": "Faculty conflict: The faculty member is already teaching another class at this time."})
                    
                # 3. Max classes per day (hardcoded to 1 for manual move check to match default)
                subject = instance.subject
                day = new_time_slot.day
                classes_on_day = TimetableEntry.objects.filter(time_slot__day=day, subject=subject).exclude(id=instance.id).count()
                if classes_on_day >= 1:
                    raise ValidationError({"error": f"Max classes per day exceeded: {subject.code} already has a class on {new_time_slot.get_day_display()}."})

                # 4. Room capacity
                if new_room.capacity < subject.required_capacity:
                    raise ValidationError({"error": f"Room capacity ({new_room.capacity}) is less than required capacity ({subject.required_capacity})."})
                
        serializer.save()


class GenerateTimetableView(APIView):
    """
    Generate a new timetable using the CSP solver.

    Accepts optional configuration in the POST body:
        - subject_ids: list of subject IDs to include (default: all)
        - room_ids: list of room IDs to use (default: all)
        - timeslot_ids: list of time slot IDs to use (default: all)
        - locked_entries: list of {subject_id, room_id, time_slot_id} to lock in place
        - excluded_slots: dict of subject_id -> [time_slot_id, ...] to exclude per subject
        - preferred_room_types: dict of subject_id -> room_type to prefer
        - avoid_back_to_back: bool, if true, try to avoid back-to-back classes for faculty
        - max_classes_per_day: int, max classes per day per subject (default: 1)
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        config = request.data or {}

        # Enqueue the background task
        task_id = async_task("apps.scheduler.tasks.generate_timetable_task", config)

        from django.conf import settings

        if getattr(settings, "Q_CLUSTER", {}).get("sync", False):
            task = fetch(task_id)
            if task and task.success:
                result_data = task.result
                if isinstance(result_data, dict) and not result_data.get(
                    "success", True
                ):
                    return Response(
                        {"error": result_data.get("error", "Unknown error")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                new_entries = TimetableEntry.objects.select_related(
                    "subject__faculty__user", "room", "time_slot"
                ).all()
                serializer = TimetableEntrySerializer(new_entries, many=True)
                return Response(
                    {
                        "message": f"Successfully scheduled {len(new_entries)} sessions.",
                        "timetable": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            elif task and task.success is False:
                return Response(
                    {"error": str(task.result)}, status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {
                "message": "Timetable generation has been queued in the background.",
                "task_id": task_id,
                "status": "processing",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TaskStatusView(APIView):
    """Check the status of a background task."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        task = fetch(task_id)
        if not task:
            return Response({"status": "unknown"}, status=status.HTTP_404_NOT_FOUND)

        if task.success:
            return Response({"status": "completed", "result": task.result})
        elif task.success is False:
            return Response({"status": "failed", "error": task.result})
        else:
            return Response({"status": "processing"})


class InstitutionSettingsView(APIView):
    """Retrieve or update institution settings."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        settings, _ = InstitutionSettings.objects.get_or_create(id=1)
        serializer = InstitutionSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        settings, _ = InstitutionSettings.objects.get_or_create(id=1)
        serializer = InstitutionSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TimetableVersionListView(generics.ListCreateAPIView):
    serializer_class = TimetableVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimetableVersion.objects.all()

class TimetableVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TimetableVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimetableVersion.objects.all()

    def perform_update(self, serializer):
        # If publishing this version, unpublish all others
        if serializer.validated_data.get('is_published', False):
            TimetableVersion.objects.all().update(is_published=False)
        serializer.save()

class AbsenceReportListView(generics.ListCreateAPIView):
    serializer_class = AbsenceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = AbsenceReport.objects.select_related("faculty__user", "substitute__user").all()
        if not self.request.user.is_staff:
            # Faculty only sees their own or pending ones where they could substitute
            qs = qs.filter(faculty__user=self.request.user) | qs.filter(status="pending")
        return qs.distinct()
        
    def perform_create(self, serializer):
        faculty = self.request.user.faculty_profile
        report = serializer.save(faculty=faculty)
        # Mock broadcasting a push alert
        Notification.objects.create(
            recipient=self.request.user,
            message=f"You reported an absence for {report.date}. Substitute request broadcasted."
        )

class AbsenceReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AbsenceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AbsenceReport.objects.all()

    def perform_update(self, serializer):
        report = serializer.save()
        if report.status == "approved" and report.substitute and report.timetable_entry:
            # Update the timetable entry's subject faculty, or rather, if we can't easily swap subject faculty (since subject is tied to a faculty), we might just mock it for MVP or create a temporary override.
            # In our MVP, we can just send a notification and assume the UI/system knows.
            # But let's actually just notify the original faculty for now to fulfill the UAT.
            Notification.objects.create(
                recipient=report.faculty.user,
                message=f"Your absence request on {report.date} has been covered by {report.substitute.user.get_full_name()}."
            )
            Notification.objects.create(
                recipient=report.substitute.user,
                message=f"You have been assigned to cover a class on {report.date}."
            )

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class TimetableSwapRequestListView(generics.ListCreateAPIView):
    serializer_class = TimetableSwapRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        qs = TimetableSwapRequest.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(requester__user=self.request.user)
        return qs
        
    def perform_create(self, serializer):
        faculty = self.request.user.faculty_profile
        serializer.save(requester=faculty)

class TimetableSwapRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TimetableSwapRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimetableSwapRequest.objects.all()
    
    def perform_update(self, serializer):
        swap = serializer.save()
        if swap.status == "approved":
            # Update timetable entry
            swap.target_entry.time_slot = swap.requested_time_slot
            swap.target_entry.save()
            Notification.objects.create(
                recipient=swap.requester.user,
                message=f"Your swap request for {swap.target_entry.subject.code} to {swap.requested_time_slot} was approved!"
            )

class FindSmartSwapView(APIView):
    """
    Given a TimetableEntry ID, use the CSP solver to find valid alternative
    placements for that class.

    Returns two categories of suggestion:
    * ``direct_move``  – the class can be moved to a free slot with no other
                         changes required.
    * ``one_step_swap`` – moving the class displaces exactly one other class
                          which can itself be placed in an alternative slot.

    Query parameters
    ----------------
    version : int (optional)
        Restrict the search to a specific TimetableVersion.  Defaults to the
        version that contains the target entry.
    minimize_changes : bool (optional, default true)
        When a full solve is performed for one-step swaps, run the
        change-minimisation pass to keep the rest of the timetable as stable
        as possible.
    """

    permission_classes = [permissions.IsAuthenticated]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_csp_data(entries):
        """
        Convert a queryset of TimetableEntry objects into the plain-dict
        structures expected by ScheduleCSP.

        Returns (subjects, rooms, time_slots, locked_entries, var_map) where
        ``var_map`` maps TimetableEntry.id -> (subject_dict, session_index).
        """
        from .csp_solver import ScheduleCSP  # local import avoids circulars

        # Collect unique rooms and time slots — start from entries, then add
        # ALL rooms and time slots from the database so the CSP domain includes
        # empty (unused) slots as valid placements.
        room_map = {}
        ts_map = {}
        for entry in entries:
            r = entry.room
            if r.id not in room_map:
                room_map[r.id] = {
                    "id": r.id,
                    "room_number": r.room_number,
                    "capacity": r.capacity,
                    "room_type": getattr(r, "room_type", "lecture"),
                    "building": getattr(r, "building", ""),
                }
            ts = entry.time_slot
            if ts.id not in ts_map:
                ts_map[ts.id] = {
                    "id": ts.id,
                    "day": ts.day,
                    "start_time": str(ts.start_time),
                    "end_time": str(ts.end_time),
                }

        # Include every room and time slot in the DB so direct moves to empty
        # slots are discoverable.
        for r in Room.objects.all():
            if r.id not in room_map:
                room_map[r.id] = {
                    "id": r.id,
                    "room_number": r.room_number,
                    "capacity": r.capacity,
                    "room_type": getattr(r, "room_type", "lecture"),
                    "building": getattr(r, "building", ""),
                }
        for ts in TimeSlot.objects.all():
            if ts.id not in ts_map:
                ts_map[ts.id] = {
                    "id": ts.id,
                    "day": ts.day,
                    "start_time": str(ts.start_time),
                    "end_time": str(ts.end_time),
                }

        rooms = list(room_map.values())
        time_slots = list(ts_map.values())

        # Build one "subject" per unique (subject_id, faculty_id) pair and
        # count how many sessions each needs within this version.
        # We treat each TimetableEntry as a single session (sessions_per_week=1)
        # to keep domains small and the solve fast.
        subjects = []
        locked_entries = []
        var_map = {}  # entry.id -> var_idx (0-based)

        for idx, entry in enumerate(entries):
            fid = entry.subject.faculty_id if entry.subject else (
                entry.faculty_id if entry.faculty else 0
            )
            subj_dict = {
                "id": entry.id,          # use entry id as unique subject key
                "code": entry.subject.code if entry.subject else (
                    entry.event_title or f"entry_{entry.id}"
                ),
                "name": entry.subject.name if entry.subject else (
                    entry.event_title or ""
                ),
                "faculty_id": fid,
                "required_capacity": (
                    entry.subject.required_capacity if entry.subject else 1
                ),
                "sessions_per_week": 1,
            }
            subjects.append(subj_dict)
            var_map[entry.id] = idx  # var index in ScheduleCSP.variables

            if entry.is_locked:
                locked_entries.append({
                    "subject_id": entry.id,
                    "room_id": entry.room_id,
                    "time_slot_id": entry.time_slot_id,
                })

        return subjects, rooms, time_slots, locked_entries, var_map

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------

    def get(self, request, entry_id):
        from .csp_solver import ScheduleCSP

        # ---- 1. Fetch target entry ----------------------------------------
        try:
            target_entry = TimetableEntry.objects.select_related(
                "subject__faculty", "room", "time_slot", "version"
            ).get(id=entry_id)
        except TimetableEntry.DoesNotExist:
            return Response(
                {"error": "Entry not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_entry.is_locked:
            return Response(
                {"error": "This entry is locked and cannot be rescheduled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- 2. Fetch all entries in the same version ----------------------
        version = target_entry.version
        all_entries = list(
            TimetableEntry.objects.select_related(
                "subject__faculty", "room", "time_slot"
            ).filter(version=version)
        )

        if not all_entries:
            return Response(
                {"error": "No entries found for this timetable version."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---- 3. Build CSP data structures ----------------------------------
        subjects, rooms, time_slots, locked_entries, var_map = (
            self._build_csp_data(all_entries)
        )

        target_var_idx = var_map[entry_id]
        target_ts_id = target_entry.time_slot_id
        target_room_id = target_entry.room_id

        # Build the original assignment (var_idx -> (ts_id, room_id)).
        original_assignment = {
            var_map[e.id]: (e.time_slot_id, e.room_id) for e in all_entries
        }

        # ---- 4. Find direct moves ------------------------------------------
        # Build a CSP with everyone locked except the target entry.
        locked_all_but_target = [
            le for le in locked_entries
            if le["subject_id"] != entry_id
        ]
        # Also lock every *other* non-locked entry so only the target is free.
        for e in all_entries:
            if e.id == entry_id:
                continue
            if not e.is_locked:
                locked_all_but_target.append({
                    "subject_id": e.id,
                    "room_id": e.room_id,
                    "time_slot_id": e.time_slot_id,
                })

        csp_direct = ScheduleCSP(
            subjects=subjects,
            rooms=rooms,
            time_slots=time_slots,
            locked_entries=locked_all_but_target,
        )

        direct_moves = []
        # Iterate over the target's domain and collect consistent values.
        for val in csp_direct.domains[target_var_idx]:
            ts_id, room_id = val
            # Skip the current placement.
            if ts_id == target_ts_id and room_id == target_room_id:
                continue

            saved = csp_direct.assignment.get(target_var_idx)
            if target_var_idx in csp_direct.assignment:
                del csp_direct.assignment[target_var_idx]

            if csp_direct.is_consistent(target_var_idx, val):
                ts_info = next(
                    (t for t in time_slots if t["id"] == ts_id), None
                )
                room_info = next(
                    (r for r in rooms if r["id"] == room_id), None
                )
                if ts_info and room_info:
                    direct_moves.append({
                        "type": "direct_move",
                        "target_slot_id": ts_id,
                        "target_slot_str": (
                            f"{ts_info['day']} {ts_info['start_time']}"
                            f"–{ts_info['end_time']}"
                        ),
                        "target_room_id": room_id,
                        "target_room_str": room_info["room_number"],
                        "description": (
                            f"Move to {ts_info['day']} "
                            f"{ts_info['start_time']}–{ts_info['end_time']} "
                            f"in {room_info['room_number']} "
                            f"(no other changes needed)"
                        ),
                    })

            if saved is not None:
                csp_direct.assignment[target_var_idx] = saved

        # ---- 5. Find 1-step swaps ------------------------------------------
        # For each other *unlocked* entry that occupies a slot the target
        # could use, check whether the displaced entry can go somewhere else.
        one_step_swaps = []

        # Gather occupied (ts_id, room_id) pairs that block the target.
        # We only care about slots that are in the target's domain.
        target_domain_vals = set(csp_direct.domains[target_var_idx])

        for other_entry in all_entries:
            if other_entry.id == entry_id or other_entry.is_locked:
                continue

            other_val = (other_entry.time_slot_id, other_entry.room_id)
            if other_val not in target_domain_vals:
                continue  # this entry doesn't occupy a slot the target wants

            other_var_idx = var_map[other_entry.id]

            # Build a CSP where we free both target and the candidate entry.
            locked_for_swap = [
                le for le in locked_all_but_target
                if le["subject_id"] != other_entry.id
            ]

            csp_swap = ScheduleCSP(
                subjects=subjects,
                rooms=rooms,
                time_slots=time_slots,
                locked_entries=locked_for_swap,
            )

            # Check: can target go into other_val?
            if target_var_idx in csp_swap.assignment:
                del csp_swap.assignment[target_var_idx]
            if other_var_idx in csp_swap.assignment:
                del csp_swap.assignment[other_var_idx]

            if not csp_swap.is_consistent(target_var_idx, other_val):
                continue  # still blocked even if we free other_entry

            # Tentatively assign target to the freed slot.
            csp_swap.assignment[target_var_idx] = other_val

            # Now check whether other_entry can go somewhere else.
            alt_for_other = None
            for alt_val in csp_swap.domains[other_var_idx]:
                if alt_val == other_val:
                    continue
                if csp_swap.is_consistent(other_var_idx, alt_val):
                    alt_for_other = alt_val
                    break

            # Clean up temporary assignment.
            del csp_swap.assignment[target_var_idx]

            if alt_for_other is None:
                continue  # no room for displaced entry — not a valid swap

            ts_info = next(
                (t for t in time_slots if t["id"] == other_val[0]), None
            )
            room_info = next(
                (r for r in rooms if r["id"] == other_val[1]), None
            )
            alt_ts_info = next(
                (t for t in time_slots if t["id"] == alt_for_other[0]), None
            )
            alt_room_info = next(
                (r for r in rooms if r["id"] == alt_for_other[1]), None
            )

            if ts_info and room_info and alt_ts_info and alt_room_info:
                other_code = (
                    other_entry.subject.code
                    if other_entry.subject
                    else (other_entry.event_title or f"entry_{other_entry.id}")
                )
                one_step_swaps.append({
                    "type": "one_step_swap",
                    "target_slot_id": other_val[0],
                    "target_slot_str": (
                        f"{ts_info['day']} {ts_info['start_time']}"
                        f"–{ts_info['end_time']}"
                    ),
                    "target_room_id": other_val[1],
                    "target_room_str": room_info["room_number"],
                    "displaced_entry_id": other_entry.id,
                    "displaced_entry_code": other_code,
                    "displaced_new_slot_id": alt_for_other[0],
                    "displaced_new_slot_str": (
                        f"{alt_ts_info['day']} {alt_ts_info['start_time']}"
                        f"–{alt_ts_info['end_time']}"
                    ),
                    "displaced_new_room_id": alt_for_other[1],
                    "displaced_new_room_str": alt_room_info["room_number"],
                    "description": (
                        f"Move to {ts_info['day']} "
                        f"{ts_info['start_time']}–{ts_info['end_time']} "
                        f"in {room_info['room_number']}; "
                        f"displace {other_code} to "
                        f"{alt_ts_info['day']} "
                        f"{alt_ts_info['start_time']}–{alt_ts_info['end_time']} "
                        f"in {alt_room_info['room_number']}"
                    ),
                })

        # ---- 6. Respond -----------------------------------------------------
        suggestions = direct_moves + one_step_swaps
        return Response(
            {
                "entry_id": entry_id,
                "current_slot": str(target_entry.time_slot),
                "current_room": target_entry.room.room_number,
                "total_suggestions": len(suggestions),
                "direct_moves": len(direct_moves),
                "one_step_swaps": len(one_step_swaps),
                "suggestions": suggestions,
            }
        )


class BlackoutDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlackoutDate
        fields = "__all__"

class BlackoutDateListView(generics.ListCreateAPIView):
    queryset = BlackoutDate.objects.all()
    serializer_class = BlackoutDateSerializer
    permission_classes = [permissions.IsAuthenticated]

class BlackoutDateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlackoutDate.objects.all()
    serializer_class = BlackoutDateSerializer
    permission_classes = [permissions.IsAuthenticated]


class ICalFeedView(APIView):
    permission_classes = [] # Public for simple webcal syncing

    def get(self, request, user_id):
        # We find faculty matching user_id
        from .models import Faculty
        try:
            faculty = Faculty.objects.get(user_id=user_id)
        except Faculty.DoesNotExist:
            return HttpResponse("User not found or not a faculty", status=404)

        cal = Calendar()
        cal.add('prodid', '-//Smart Campus Scheduler//EN')
        cal.add('version', '2.0')

        # Get published version
        from .models import TimetableVersion
        from django.db import models
        published_version = TimetableVersion.objects.filter(is_published=True).first()
        if not published_version:
            return HttpResponse(cal.to_ical(), content_type="text/calendar")

        entries = TimetableEntry.objects.filter(
            version=published_version
        ).filter(
            models.Q(subject__faculty=faculty) | models.Q(faculty=faculty)
        )

        # Generate recurring events for the current semester
        # For MVP, assume semester starts from today for 16 weeks
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(weeks=16)

        day_map = {
            'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
        }

        for entry in entries:
            event = Event()
            title = entry.subject.code if entry.subject else (entry.event_title or "Class")
            event.add('summary', title)
            event.add('location', entry.room.room_number)

            # Find the first date matching the day of the week
            day_offset = day_map[entry.time_slot.day] - start_date.weekday()
            if day_offset < 0:
                day_offset += 7
            first_date = start_date + datetime.timedelta(days=day_offset)

            dtstart = datetime.datetime.combine(first_date, entry.time_slot.start_time)
            dtend = datetime.datetime.combine(first_date, entry.time_slot.end_time)

            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            event.add('rrule', {'freq': 'weekly', 'until': end_date})
            
            # Exclude blackout dates
            blackout_dates = BlackoutDate.objects.all()
            exdates = []
            for bd in blackout_dates:
                if bd.date.weekday() == day_map[entry.time_slot.day]:
                    exdt = datetime.datetime.combine(bd.date, entry.time_slot.start_time)
                    exdates.append(exdt)
            if exdates:
                event.add('exdate', exdates)

            cal.add_component(event)

        response = HttpResponse(cal.to_ical(), content_type="text/calendar")
        response['Content-Disposition'] = f'attachment; filename="schedule_{user_id}.ics"'
        return response


class AccreditationAnalyticsView(APIView):
    """
    Generate accreditation analytics for published timetables.
    Returns JSON mapping for faculty workload, room utilization, and resource usage.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.scheduler.models import TimetableEntry, Room
        from apps.accounts.models import Faculty
        import csv
        from django.http import HttpResponse
        
        # Only look at published versions
        entries = TimetableEntry.objects.filter(version__is_published=True)
        
        # 1. Faculty Workload (max hours per week)
        faculty_workload = []
        for faculty in Faculty.objects.select_related("user").all():
            count = entries.filter(faculty=faculty).count()
            # 1 session = 1 hour roughly
            faculty_workload.append({
                "faculty_name": f"{faculty.user.first_name} {faculty.user.last_name}",
                "department": faculty.department,
                "sessions_per_week": count,
                "max_hours": faculty.max_hours_per_week,
                "compliance": "Pass" if count <= faculty.max_hours_per_week else "Fail"
            })
            
        # 2. Room Utilization
        # Assuming 6 days * 11 slots = 66 slots per week
        total_slots = 66 
        room_utilization = []
        for room in Room.objects.all():
            count = entries.filter(room=room).count()
            rate = (count / total_slots) * 100 if total_slots > 0 else 0
            room_utilization.append({
                "room_number": room.room_number,
                "building": room.building,
                "sessions_used": count,
                "utilization_rate": round(rate, 2)
            })

        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="accreditation_report.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['--- Faculty Workload ---'])
            writer.writerow(['Name', 'Department', 'Sessions', 'Max Hours', 'Compliance'])
            for f in faculty_workload:
                writer.writerow([f['faculty_name'], f['department'], f['sessions_per_week'], f['max_hours'], f['compliance']])
                
            writer.writerow([])
            writer.writerow(['--- Room Utilization ---'])
            writer.writerow(['Room', 'Building', 'Sessions Used', 'Utilization %'])
            for r in room_utilization:
                writer.writerow([r['room_number'], r['building'], r['sessions_used'], f"{r['utilization_rate']}%"])
                
            return response

        return Response({
            "faculty_workload": faculty_workload,
            "room_utilization": room_utilization,
        })


class ForecastingAnalyticsView(APIView):
    """
    Forecasting endpoint to predict future capacity needs based on simulated growth.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from apps.scheduler.models import TimetableEntry, Subject, Room
        import math
        
        growth_pct = float(request.data.get("enrollment_growth_pct", 0))
        multiplier = 1 + (growth_pct / 100.0)
        
        # Analyze current state
        entries = TimetableEntry.objects.filter(version__is_published=True)
        current_classes = entries.count()
        
        # Extrapolate needs
        projected_classes = math.ceil(current_classes * multiplier)
        additional_classes = projected_classes - current_classes
        
        # Estimate faculty gap (assume 1 faculty can teach 15 classes/week)
        additional_faculty_needed = math.ceil(additional_classes / 15.0)
        
        # Estimate room slots gap
        rooms_count = Room.objects.count()
        total_slots_available = rooms_count * 66 # 6 days * 11 slots
        
        room_deficit = max(0, projected_classes - total_slots_available)
        additional_rooms_needed = math.ceil(room_deficit / 66.0)
        
        # TA needs
        total_tas_currently_required = sum([
            s.required_tas * s.sessions_per_week 
            for s in Subject.objects.all()
        ])
        projected_ta_slots = math.ceil(total_tas_currently_required * multiplier)
        additional_tas_needed = math.ceil((projected_ta_slots - total_tas_currently_required) / 10.0)

        return Response({
            "growth_assumptions": {
                "enrollment_growth_pct": growth_pct,
                "multiplier": multiplier
            },
            "current_metrics": {
                "active_classes": current_classes,
                "total_room_slots": total_slots_available
            },
            "projected_needs": {
                "projected_classes": projected_classes,
                "additional_faculty_needed": additional_faculty_needed,
                "additional_rooms_needed": additional_rooms_needed,
                "additional_tas_needed": additional_tas_needed,
            }
        })



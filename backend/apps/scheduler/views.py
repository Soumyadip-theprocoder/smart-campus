"""
Views for the Scheduler app.
"""

import datetime

from django.http import HttpResponse
from django_q.tasks import async_task, fetch
from icalendar import Calendar, Event
from collections import defaultdict
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import Student

from .models import (
    Room, Subject, TimeSlot, TimetableEntry, InstitutionSettings,
    TimetableVersion, AbsenceReport, Notification, TimetableSwapRequest,
    Department, Amenity, Resource, BlackoutDate, StudentElectiveEnrollment,
    SchedulerTaskProgress
)
from .serializers import (
    RoomSerializer, SubjectSerializer,
    TimeSlotSerializer, TimetableEntrySerializer, InstitutionSettingsSerializer,
    TimetableVersionSerializer, AbsenceReportSerializer, NotificationSerializer,
    TimetableSwapRequestSerializer, DepartmentSerializer, AmenitySerializer,
    ResourceSerializer, StudentElectiveEnrollmentSerializer
)


from django.db.models import Q
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class SubjectListView(generics.ListCreateAPIView):
    """List or create subjects."""

    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter]
    search_fields = [
        "name",
        "code",
        "faculty__user__first_name",
        "faculty__user__last_name",
        "faculty__department__name",
        "faculty__department__dept_id",
        "departments__name",
        "departments__dept_id",
    ]

    def get_queryset(self):
        qs = (
            Subject.objects.select_related("faculty__user", "faculty__department")
            .prefetch_related("departments", "amenities")
            .all()
            .order_by("code")
        )

        degree = self.request.query_params.get("degree")
        if degree:
            qs = qs.filter(
                Q(departments__program_type__iexact=degree)
                | Q(departments__name__istartswith=degree)
                | Q(departments__name__icontains=degree)
                | Q(faculty__department__program_type__iexact=degree)
                | Q(faculty__department__name__istartswith=degree)
                | Q(faculty__department__name__icontains=degree)
            ).distinct()

        dept_id = self.request.query_params.get("department")
        if dept_id:
            qs = qs.filter(
                Q(departments__id=dept_id) | Q(faculty__department_id=dept_id)
            ).distinct()

        block = self.request.query_params.get("block")
        if block:
            block_dept_ids = Department.objects.filter(
                rooms__building__icontains=block
            ).values_list("id", flat=True).distinct()
            if block_dept_ids:
                qs = qs.filter(departments__id__in=block_dept_ids).distinct()

        subject_type = self.request.query_params.get("subject_type")
        if subject_type:
            qs = qs.filter(subject_type=subject_type)

        faculty_id = self.request.query_params.get("faculty")
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)

        has_faculty = self.request.query_params.get("has_faculty")
        if has_faculty == "true":
            qs = qs.filter(faculty__isnull=False)
        elif has_faculty == "false":
            qs = qs.filter(faculty__isnull=True)

        year_param = self.request.query_params.get("year")
        if year_param:
            try:
                y = int(year_param)
                year_sems = [y * 2 - 1, y * 2]
                qs = qs.filter(semester__in=year_sems)
            except ValueError:
                pass

        semester = self.request.query_params.get("semester")
        if semester:
            qs = qs.filter(semester=semester)

        term = self.request.query_params.get("term")
        if term == "odd":
            qs = qs.filter(semester__in=[1, 3, 5, 7, 9])
        elif term == "even":
            qs = qs.filter(semester__in=[2, 4, 6, 8, 10])

        semesters = self.request.query_params.get("semesters")
        if semesters:
            sem_list = [int(s) for s in semesters.split(",") if s.strip().isdigit()]
            if sem_list:
                qs = qs.filter(semester__in=sem_list)

        credits_param = self.request.query_params.get("credits")
        if credits_param:
            if credits_param == "1-2":
                qs = qs.filter(credits__lte=2.0)
            elif credits_param == "3":
                qs = qs.filter(credits=3.0)
            elif credits_param == "4-5":
                qs = qs.filter(credits__gte=4.0, credits__lte=5.0)
            elif credits_param == "6+":
                qs = qs.filter(credits__gte=6.0)
            else:
                try:
                    qs = qs.filter(credits=float(credits_param))
                except ValueError:
                    pass

        is_elective = self.request.query_params.get("is_elective")
        if is_elective is not None:
            qs = qs.filter(is_elective=is_elective.lower() in ["true", "1"])

        elective_group = self.request.query_params.get("elective_group")
        if elective_group:
            qs = qs.filter(elective_group=elective_group)

        ordering = self.request.query_params.get("ordering")
        if ordering:
            ordering_map = {
                "code": "code",
                "-code": "-code",
                "name": "name",
                "-name": "-name",
                "semester": "semester",
                "-semester": "-semester",
                "credits": "credits",
                "-credits": "-credits",
                "required_capacity": "required_capacity",
                "-required_capacity": "-required_capacity",
                "sessions_per_week": "sessions_per_week",
                "-sessions_per_week": "-sessions_per_week",
                "subject_type": "subject_type",
                "-subject_type": "-subject_type",
                "is_elective": "is_elective",
                "-is_elective": "-is_elective",
                "department": "departments__name",
                "-department": "-departments__name",
                "faculty": "faculty__user__first_name",
                "-faculty": "-faculty__user__first_name",
                "faculty_name": "faculty__user__first_name",
                "-faculty_name": "-faculty__user__first_name",
                "id": "id",
                "-id": "-id",
            }
            mapped_ordering = ordering_map.get(ordering)
            if mapped_ordering:
                qs = qs.order_by(mapped_ordering)
            else:
                qs = qs.order_by("code")

        return qs

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("all", "false").lower() == "true":
            return None
        return super().paginate_queryset(queryset)


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a subject."""

    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = (
        Subject.objects.select_related("faculty__user", "faculty__department")
        .prefetch_related("departments", "amenities")
        .all()
    )

class DepartmentListView(generics.ListCreateAPIView):
    """List or create departments."""
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["name", "dept_id", "core_department"]

    def get_queryset(self):
        from django.db.models import Count, Subquery, OuterRef, IntegerField
        from django.db.models.functions import Coalesce
        from apps.accounts.models import Student, Faculty
        from apps.scheduler.models import Subject

        stu_sub = Student.objects.filter(department=OuterRef("pk")).values("department").annotate(c=Count("id")).values("c")
        fac_sub = Faculty.objects.filter(department=OuterRef("pk")).values("department").annotate(c=Count("id")).values("c")
        sub_sub = Subject.objects.filter(departments=OuterRef("pk")).values("departments").annotate(c=Count("id")).values("c")

        qs = Department.objects.annotate(
            student_count=Coalesce(Subquery(stu_sub, output_field=IntegerField()), 0),
            faculty_count=Coalesce(Subquery(fac_sub, output_field=IntegerField()), 0),
            subject_count=Coalesce(Subquery(sub_sub, output_field=IntegerField()), 0),
        ).order_by("dept_id", "name")
        program_type = self.request.query_params.get("program_type")
        if program_type:
            qs = qs.filter(program_type=program_type)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            ordering_map = {
                "dept_id": "dept_id",
                "-dept_id": "-dept_id",
                "name": "name",
                "-name": "-name",
                "program_type": "program_type",
                "-program_type": "-program_type",
                "core_department": "core_department",
                "-core_department": "-core_department",
                "student_count": "student_count",
                "-student_count": "-student_count",
                "faculty_count": "faculty_count",
                "-faculty_count": "-faculty_count",
                "subject_count": "subject_count",
                "-subject_count": "-subject_count",
                "id": "id",
                "-id": "-id",
            }
            mapped_ordering = ordering_map.get(ordering)
            if mapped_ordering:
                qs = qs.order_by(mapped_ordering)
        return qs

    def paginate_queryset(self, queryset):
        if self.request.query_params.get('all', 'false').lower() == 'true':
            return None
        return super().paginate_queryset(queryset)


class NextDepartmentIDView(APIView):
    """Get the next suggested standardized Department ID."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import re
        existing_ids = Department.objects.exclude(dept_id__isnull=True).values_list("dept_id", flat=True)
        max_num = 0
        for did in existing_ids:
            m = re.match(r"^DEP-(\d+)$", str(did))
            if m:
                max_num = max(max_num, int(m.group(1)))
        next_id = f"DEP-{(max_num + 1):04d}"
        return Response({"next_id": next_id})


class DepartmentProgramTypesView(APIView):
    """Return distinct program types currently present in departments with their counts."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Count
        types_data = (
            Department.objects.exclude(program_type__isnull=True)
            .exclude(program_type="")
            .values("program_type")
            .annotate(count=Count("id"))
            .order_by("-count", "program_type")
        )
        return Response(list(types_data))


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a department."""
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Count
        return Department.objects.annotate(
            student_count=Count("students", distinct=True),
            faculty_count=Count("faculty_members", distinct=True),
            subject_count=Count("subjects", distinct=True),
        ).all()


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
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter]
    search_fields = ["room_number", "building", "room_type"]

    def get_queryset(self):
        qs = Room.objects.all().order_by("room_number")
        building = self.request.query_params.get("building") or self.request.query_params.get("block")
        if building:
            qs = qs.filter(Q(building__iexact=building) | Q(building__icontains=building))
        room_type = self.request.query_params.get("room_type")
        if room_type:
            qs = qs.filter(room_type=room_type)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            ordering_map = {
                "room_number": "room_number",
                "-room_number": "-room_number",
                "building": "building",
                "-building": "-building",
                "room_type": "room_type",
                "-room_type": "-room_type",
                "capacity": "capacity",
                "-capacity": "-capacity",
                "id": "id",
                "-id": "-id",
            }
            mapped = ordering_map.get(ordering)
            if mapped:
                qs = qs.order_by(mapped)
        return qs

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("all", "false").lower() == "true":
            return None
        return super().paginate_queryset(queryset)


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


class TimetableView(generics.ListCreateAPIView):
    """Get the current timetable or create a custom entry."""

    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_admin_user = bool(
            user.is_staff or
            user.is_superuser or
            getattr(user, "role", "") == "admin" or
            getattr(user, "is_admin", False)
        )

        qs = TimetableEntry.objects.select_related(
            "subject__faculty__user",
            "room",
            "time_slot",
            "version"
        ).prefetch_related(
            "subject__departments",
            "teaching_assistants__user"
        )

        version_id = self.request.query_params.get("version")
        if is_admin_user and version_id:
            qs = qs.filter(version_id=version_id)
        else:
            published_qs = TimetableVersion.objects.filter(is_published=True)
            if version_id:
                published_qs = published_qs.filter(id=version_id)
            published_version = published_qs.first()
            if published_version:
                qs = qs.filter(version_id=published_version.id)
            elif is_admin_user and version_id:
                qs = qs.filter(version_id=version_id)
            else:
                qs = qs.none()

        from django.db.models import Q

        is_faculty = getattr(user, "role", "") == "faculty" or getattr(user, "is_faculty", False)
        is_student = getattr(user, "role", "") == "student" or getattr(user, "is_student", False)

        # 1. Faculty restriction: only sessions they teach or substitute for
        if not is_admin_user and is_faculty:
            faculty = getattr(user, "faculty_profile", None)
            if not faculty:
                return qs.none()

            from apps.scheduler.models import AbsenceReport
            sub_entry_ids = list(AbsenceReport.objects.filter(
                substitute=faculty,
                status="approved"
            ).values_list("timetable_entry_id", flat=True))

            qs = qs.filter(
                Q(faculty=faculty) |
                Q(subject__faculty=faculty) |
                Q(id__in=sub_entry_ids)
            ).distinct()

        # 2. Student restriction: only enrolled core, electives, and TA classes
        elif not is_admin_user and is_student:
            student = getattr(user, "student_profile", None)
            if not student:
                return qs.none()

            student_dept = student.department
            student_sem = student.semester

            core_filter = Q(
                subject__departments=student_dept,
                subject__semester=student_sem,
                subject__is_elective=False
            ) if (student_dept and student_sem) else Q(pk__in=[])

            from apps.scheduler.models import StudentElectiveEnrollment
            enrolled_subject_ids = list(StudentElectiveEnrollment.objects.filter(
                student=student
            ).values_list("subject_id", flat=True))
            elective_filter = Q(subject_id__in=enrolled_subject_ids) if enrolled_subject_ids else Q(pk__in=[])

            ta_filter = Q(teaching_assistants=student) if getattr(student, "is_ta", False) else Q(pk__in=[])

            qs = qs.filter(core_filter | elective_filter | ta_filter).distinct()

        elif not is_admin_user:
            return qs.none()

        block = self.request.query_params.get("block")
        if block:
            qs = qs.filter(room__building__icontains=block)

        dept_id = self.request.query_params.get("department")
        if dept_id:
            qs = qs.filter(subject__departments__id=dept_id)

        semester = self.request.query_params.get("semester")
        if semester:
            qs = qs.filter(subject__semester=semester)

        return qs

    def paginate_queryset(self, queryset):
        user = self.request.user
        is_admin_user = bool(
            user.is_staff or
            user.is_superuser or
            getattr(user, "role", "") == "admin" or
            getattr(user, "is_admin", False)
        )
        if not is_admin_user or self.request.query_params.get("all", "false").lower() == "true" or self.request.query_params.get("version"):
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can create timetable entries.")
        from rest_framework.exceptions import ValidationError
        version_id = self.request.data.get("version") or self.request.query_params.get("version")
        if version_id:
            version = TimetableVersion.objects.filter(id=version_id).first()
        else:
            version = TimetableVersion.objects.filter(is_published=True).first()

        room = serializer.validated_data.get("room")
        time_slot = serializer.validated_data.get("time_slot")
        if room and time_slot and TimetableEntry.objects.filter(version=version, room=room, time_slot=time_slot).exists():
            raise ValidationError({"error": f"Room {room.room_number} is already occupied at this time slot."})

        serializer.save(version=version)


class TimetableEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a timetable entry."""
    serializer_class = TimetableEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TimetableEntry.objects.all()

    def perform_update(self, serializer):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can update timetable entries.")
        instance = self.get_object()
        new_time_slot = serializer.validated_data.get("time_slot", instance.time_slot)
        new_room = serializer.validated_data.get("room", instance.room)
        
        # Check constraints if time_slot or room is changing
        if new_time_slot != instance.time_slot or new_room != instance.room:
            from rest_framework.exceptions import ValidationError
            # 1. Room conflict (scoped to same version)
            if TimetableEntry.objects.filter(version=instance.version, time_slot=new_time_slot, room=new_room).exclude(id=instance.id).exists():
                raise ValidationError({"error": "Room conflict: Another class is scheduled in this room at this time."})
                
            # 2. Faculty conflict & Capacity (scoped to same version)
            if instance.subject and instance.subject.faculty:
                faculty = instance.subject.faculty
                if TimetableEntry.objects.filter(version=instance.version, time_slot=new_time_slot, subject__faculty=faculty).exclude(id=instance.id).exists():
                    raise ValidationError({"error": "Faculty conflict: The faculty member is already teaching another class at this time."})
                    
                # 3. Max classes per day (scoped to same version)
                subject = instance.subject
                day = new_time_slot.day
                classes_on_day = TimetableEntry.objects.filter(version=instance.version, time_slot__day=day, subject=subject).exclude(id=instance.id).count()
                if classes_on_day >= 1:
                    raise ValidationError({"error": f"Max classes per day exceeded: {subject.code} already has a class on {new_time_slot.get_day_display()}."})

                # 4. Room capacity
                if new_room and new_room.capacity < subject.required_capacity:
                    raise ValidationError({"error": f"Room capacity ({new_room.capacity}) is less than required capacity ({subject.required_capacity})."})
                
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can delete timetable entries.")
        instance.delete()


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
        user = request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can generate timetables.")

        import uuid
        import time
        from .tasks import estimate_generation_eta

        if hasattr(request.data, "dict"):
            config = request.data.dict()
        elif hasattr(request.data, "copy"):
            config = request.data.copy()
        else:
            config = dict(request.data or {})

        # Validate scope parameters if provided
        scope_type = config.get("scope_type", "department")
        department_id = config.get("department_id")
        if scope_type == "department" and not department_id:
            scope_type = "all"
            config["scope_type"] = "all"

        if scope_type not in ("all", "block", "department"):
            return Response(
                {"error": f"Invalid scope_type: {scope_type}. Must be 'all', 'block', or 'department'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Pre-compute ETA & load label
        eta_info = estimate_generation_eta(config)
        tracking_id = uuid.uuid4().hex
        config["tracking_id"] = tracking_id

        # Determine readable scope label
        if scope_type == "block":
            scope_label = config.get("block_name", "Academic Block")
        elif scope_type == "all":
            scope_label = "Whole Campus (Enterprise)"
        else:
            dept = Department.objects.filter(id=department_id).first()
            scope_label = dept.name if dept else f"Department #{department_id}"

        # Capture into debug middle layer before dispatching
        from .debug_layer import capture_generator_inputs
        capture_generator_inputs(request, endpoint="generate", tracking_id=tracking_id)

        # Initialize progress record in DB
        SchedulerTaskProgress.objects.create(
            task_id=tracking_id,
            status="queued",
            scope_type=scope_type,
            scope_label=scope_label,
            eta_remaining_seconds=eta_info["estimated_seconds"],
            start_time=time.time(),
            percent=0.0,
            current_wave_name="Queued in scheduler cluster...",
            input_payload=config,
        )

        # Enqueue the background task with no timeout cutoff
        q_task_id = async_task("apps.scheduler.tasks.generate_timetable_task", config, timeout=-1)

        from django.conf import settings

        if getattr(settings, "Q_CLUSTER", {}).get("sync", False):
            task = fetch(q_task_id)
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
                ).prefetch_related("subject__departments").all()
                serializer = TimetableEntrySerializer(new_entries, many=True)
                return Response(
                    {
                        "message": f"Successfully scheduled {len(new_entries)} sessions.",
                        "timetable": serializer.data,
                        "metadata": {
                            "cohort_stats": result_data.get("cohort_stats", 0) if isinstance(result_data, dict) else 0,
                            "merged_sessions_count": result_data.get("merged_sessions_count", 0) if isinstance(result_data, dict) else 0,
                            "lab_blocks_count": result_data.get("lab_blocks_count", 0) if isinstance(result_data, dict) else 0,
                        }
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
                "task_id": tracking_id,
                "q_task_id": q_task_id,
                "status": "processing",
                "eta": eta_info,
                "scope": {
                    "scope_type": scope_type,
                    "scope_label": scope_label,
                    "block_name": config.get("block_name"),
                    "department_id": department_id,
                    "semester": config.get("semester"),
                }
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TaskStatusView(APIView):
    """Check the status of a background task with live dynamic ETA and smooth wave progress."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        progress = SchedulerTaskProgress.objects.filter(task_id=task_id).first()

        if progress:
            if progress.status == "completed":
                return Response({
                    "status": "completed",
                    "result": progress.result_data,
                    "progress": {
                        "percent": 100.0,
                        "elapsed_seconds": progress.elapsed_seconds,
                        "eta_remaining_seconds": 0.0,
                        "sessions_scheduled": progress.sessions_scheduled,
                        "current_wave_name": "Completed successfully",
                        "current_wave": progress.current_wave,
                        "total_waves": progress.total_waves,
                        "scope_label": progress.scope_label,
                    }
                })
            elif progress.status == "failed":
                return Response({
                    "status": "failed",
                    "error": progress.error or "Generation failed",
                    "progress": {
                        "percent": progress.percent,
                        "elapsed_seconds": progress.elapsed_seconds,
                        "current_wave_name": "Failed",
                        "scope_label": progress.scope_label,
                    }
                })
            elif progress.status == "cancelled":
                return Response({
                    "status": "cancelled",
                    "error": progress.error or "Generation cancelled by user",
                    "progress": {
                        "percent": progress.percent,
                        "elapsed_seconds": progress.elapsed_seconds,
                        "eta_remaining_seconds": 0.0,
                        "sessions_scheduled": progress.sessions_scheduled,
                        "current_wave_name": "Generation cancelled by user",
                        "scope_label": progress.scope_label,
                    }
                })
            else:
                import time
                now = time.time()
                elapsed = round(now - progress.start_time, 1) if progress.start_time else 0.0

                # Compute dynamic ETA directly from live wave throughput for multi-wave tasks
                if progress.total_waves > 1 and progress.current_wave > 0:
                    waves_done = progress.current_wave
                    rem_waves = max(0, progress.total_waves - waves_done)
                    avg_wave_sec = max(1.2, elapsed / max(1, waves_done))
                    last_updated = progress.updated_at.timestamp() if progress.updated_at else now
                    time_in_current_wave = max(0.0, now - last_updated)

                    if rem_waves == 0:
                        dynamic_eta = 2.0
                    else:
                        dynamic_eta = max(2.0, round((rem_waves * avg_wave_sec) - time_in_current_wave, 1))

                    # Dynamically interpolate percent based on wave position and time in current wave
                    wave_span = 88.0 / max(1, progress.total_waves)
                    wave_fraction = min(0.90, time_in_current_wave / max(4.0, avg_wave_sec))
                    dynamic_pct = min(94.5, round(progress.percent + (wave_span * wave_fraction), 1))
                else:
                    base_eta = progress.eta_remaining_seconds if progress.eta_remaining_seconds > 0 else 10.0
                    last_updated = progress.updated_at.timestamp() if progress.updated_at else (progress.start_time or now)
                    time_since_update = max(0.0, now - last_updated)
                    dynamic_eta = max(1.0, round(base_eta - time_since_update, 1))

                    base_pct = progress.percent or 5.0
                    dur = max(3.0, base_eta)
                    single_fraction = min(0.92, time_since_update / dur)
                    dynamic_pct = min(92.0, round(base_pct + (single_fraction * (90.0 - base_pct)), 1))

                return Response({
                    "status": "processing",
                    "progress": {
                        "percent": dynamic_pct,
                        "current_wave": progress.current_wave,
                        "total_waves": progress.total_waves,
                        "current_wave_name": progress.current_wave_name or "Solving timetable...",
                        "sessions_scheduled": progress.sessions_scheduled,
                        "elapsed_seconds": elapsed,
                        "eta_remaining_seconds": dynamic_eta,
                        "scope_type": progress.scope_type,
                        "scope_label": progress.scope_label,
                    }
                })

        # Fallback to standard Django Q task lookup
        task = fetch(task_id)
        if not task:
            return Response({"status": "processing"})


class TaskCancelView(APIView):
    """Cancel an active timetable generation background task."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, task_id):
        progress = SchedulerTaskProgress.objects.filter(task_id=task_id).first()
        if not progress:
            return Response(
                {"error": f"Task {task_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if progress.status in ["completed", "failed", "cancelled"]:
            return Response(
                {"message": f"Task is already {progress.status}.", "status": progress.status},
                status=status.HTTP_200_OK,
            )

        import time
        now = time.time()
        elapsed = round(now - progress.start_time, 1) if progress.start_time else progress.elapsed_seconds

        progress.status = "cancelled"
        progress.error = "Generation cancelled by user"
        progress.current_wave_name = "Generation cancelled by user"
        progress.eta_remaining_seconds = 0.0
        progress.elapsed_seconds = elapsed
        progress.save(update_fields=["status", "error", "current_wave_name", "eta_remaining_seconds", "elapsed_seconds", "updated_at"])

        return Response(
            {
                "success": True,
                "message": "Timetable generation cancelled successfully.",
                "status": "cancelled",
            },
            status=status.HTTP_200_OK,
        )


class ActiveTaskStatusView(APIView):
    """Check if there is any active background timetable task running across the system."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import datetime
        active = SchedulerTaskProgress.objects.filter(
            status__in=["queued", "running"]
        ).order_by("-created_at").first()

        if active:
            return Response({
                "has_active_task": True,
                "task_id": active.task_id,
                "status": active.status,
            })

        # Check for recently completed/failed task (within last 15s) for smooth handoff
        cutoff = datetime.datetime.now() - datetime.timedelta(seconds=15)
        recent = SchedulerTaskProgress.objects.filter(
            status__in=["completed", "failed"],
            updated_at__gte=cutoff
        ).order_by("-updated_at").first()

        if recent:
            return Response({
                "has_active_task": True,
                "task_id": recent.task_id,
                "status": recent.status,
                "is_recent": True,
            })

        return Response({"has_active_task": False})

        if task.success:
            return Response({"status": "completed", "result": task.result})
        elif task.success is False:
            return Response({"status": "failed", "error": task.result})
        else:
            return Response({"status": "processing"})


class EstimateGenerationETAView(APIView):
    """Preview generation ETA and load category before launching task."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .tasks import estimate_generation_eta
        from .debug_layer import capture_generator_inputs
        config = request.data or {}
        capture_generator_inputs(request, endpoint="estimate-eta")
        eta_info = estimate_generation_eta(config)
        return Response(eta_info, status=status.HTTP_200_OK)


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

    def get_queryset(self):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        qs = TimetableVersion.objects.all().order_by("-created_at")
        if not is_admin_user:
            qs = qs.filter(is_published=True)
        return qs

    def paginate_queryset(self, queryset):
        if self.request.query_params.get("all", "false").lower() == "true":
            return None
        return super().paginate_queryset(queryset)

class TimetableVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TimetableVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            return TimetableVersion.objects.filter(is_published=True)
        return TimetableVersion.objects.all()

    def perform_update(self, serializer):
        user = self.request.user
        is_admin_user = bool(user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser)
        if not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can update or rename timetable versions.")
        # If publishing this version, unpublish all others
        if serializer.validated_data.get('is_published', False):
            TimetableVersion.objects.all().update(is_published=False)
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_staff or getattr(user, 'role', '') == 'admin' or user.is_superuser):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can delete timetable versions.")
        if instance.is_published:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete the active published timetable. Please unpublish or switch live version first.")
        instance.delete()


class TimetableVersionBulkDeleteView(APIView):
    """Bulk delete draft timetable versions."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not (user.is_staff or getattr(user, "role", "") == "admin" or user.is_superuser):
            return Response(
                {"error": "Only administrators can delete timetable versions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ids = request.data.get("ids") or request.data.get("version_ids", [])
        delete_all_drafts = request.data.get("delete_all_drafts", False)

        if delete_all_drafts:
            qs = TimetableVersion.objects.filter(is_published=False)
        elif ids:
            qs = TimetableVersion.objects.filter(id__in=ids, is_published=False)
        else:
            return Response(
                {"error": "No draft version IDs provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = qs.count()
        if count == 0:
            return Response(
                {"message": "No draft versions were found to delete.", "deleted_count": 0},
                status=status.HTTP_200_OK,
            )

        qs.delete()
        return Response(
            {
                "message": f"Successfully deleted {count} draft timetable(s).",
                "deleted_count": count,
            },
            status=status.HTTP_200_OK,
        )

class AbsenceReportListView(generics.ListCreateAPIView):
    serializer_class = AbsenceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        is_admin = bool(user.is_staff or user.is_superuser or getattr(user, "role", "") == "admin")
        qs = AbsenceReport.objects.select_related(
            "faculty__user", "faculty__department",
            "substitute__user", "substitute__department",
            "timetable_entry__subject", "timetable_entry__room", "timetable_entry__time_slot"
        ).all().order_by("-date", "-id")

        if not is_admin:
            faculty = getattr(user, "faculty_profile", None)
            if faculty:
                qs = qs.filter(Q(faculty=faculty) | Q(substitute=faculty) | Q(status="pending"))
            else:
                qs = qs.none()
        return qs.distinct()
        
    def perform_create(self, serializer):
        from apps.accounts.models import Faculty
        user = self.request.user
        is_admin = bool(user.is_staff or user.is_superuser or getattr(user, "role", "") == "admin")
        faculty = getattr(user, "faculty_profile", None)
        if not faculty and is_admin:
            faculty_id = self.request.data.get("faculty")
            if faculty_id:
                faculty = Faculty.objects.filter(id=faculty_id).first()
            if not faculty:
                faculty = Faculty.objects.first()
        elif not faculty:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only faculty members can report class absences.")

        target_sub_id = self.request.data.get("substitute") or self.request.data.get("substitute_id")
        target_substitute = None
        if target_sub_id:
            target_substitute = Faculty.objects.filter(id=target_sub_id).first()

        report = serializer.save(faculty=faculty, substitute=target_substitute, status="pending")

        entry = report.timetable_entry
        subj_name = entry.subject.code if (entry and entry.subject) else "Class"
        time_display = f"{entry.time_slot.day} {entry.time_slot.start_time.strftime('%H:%M')}" if (entry and entry.time_slot) else ""

        Notification.objects.create(
            recipient=user,
            message=f"You reported an absence for {subj_name} on {report.date} ({time_display}). Substitute request broadcasted."
        )

        if target_substitute and target_substitute.user:
            Notification.objects.create(
                recipient=target_substitute.user,
                message=f"Prof. {user.get_full_name()} requested you as a substitute for {subj_name} on {report.date} ({time_display})."
            )

class AbsenceReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AbsenceReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AbsenceReport.objects.all()

    def perform_update(self, serializer):
        from apps.accounts.models import Faculty
        user = self.request.user
        report = serializer.instance
        
        target_status = self.request.data.get("status") or serializer.validated_data.get("status", report.status)
        substitute = serializer.validated_data.get("substitute")

        if not substitute:
            sub_id = self.request.data.get("substitute_id") or self.request.data.get("substitute")
            if sub_id:
                substitute = Faculty.objects.filter(id=sub_id).first() or Faculty.objects.filter(user_id=sub_id).first()
            elif hasattr(user, "faculty_profile") and user.faculty_profile and target_status == "approved":
                substitute = user.faculty_profile

        if substitute and substitute == report.faculty:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "You cannot accept a substitution request for your own class."})

        updated_report = serializer.save(status=target_status, substitute=substitute or report.substitute)

        if updated_report.status == "approved" and updated_report.substitute:
            entry = updated_report.timetable_entry
            subj_title = entry.subject.code if (entry and entry.subject) else "Class"
            time_display = f"{entry.time_slot.day} {entry.time_slot.start_time.strftime('%H:%M')}" if (entry and entry.time_slot) else ""

            if updated_report.faculty and updated_report.faculty.user:
                Notification.objects.create(
                    recipient=updated_report.faculty.user,
                    message=f"Your absence request for {subj_title} on {updated_report.date} ({time_display}) has been accepted and covered by Prof. {updated_report.substitute.user.get_full_name()}."
                )
            if updated_report.substitute and updated_report.substitute.user:
                Notification.objects.create(
                    recipient=updated_report.substitute.user,
                    message=f"You are confirmed to cover {subj_title} for Prof. {updated_report.faculty.user.get_full_name()} on {updated_report.date} ({time_display})."
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
        from apps.accounts.models import Faculty
        faculty = getattr(self.request.user, "faculty_profile", None)
        if not faculty:
            faculty = Faculty.objects.first()
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

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------

    def get(self, request, entry_id):
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

        target_fac_id = target_entry.subject.faculty_id if target_entry.subject else target_entry.faculty_id
        target_req_cap = target_entry.subject.required_capacity if target_entry.subject else 1

        rooms = {r.id: r for r in Room.objects.all()}
        time_slots = {ts.id: ts for ts in TimeSlot.objects.all()}

        # ---- 3. Build fast lookup maps ----------------------------------
        # ts_id -> room_id -> entry
        room_usage = {}
        # ts_id -> fac_id -> entry
        fac_usage = {}

        for e in all_entries:
            room_usage.setdefault(e.time_slot_id, {})[e.room_id] = e
            fac_id = e.subject.faculty_id if e.subject else e.faculty_id
            if fac_id:
                fac_usage.setdefault(e.time_slot_id, {})[fac_id] = e

        def is_valid_placement(entry_to_place, ts_id, room_id, ignore_entries=None):
            if ignore_entries is None: ignore_entries = set()
            
            # Check capacity
            req_cap = entry_to_place.subject.required_capacity if entry_to_place.subject else 1
            if rooms[room_id].capacity < req_cap:
                return False

            # Check room conflict
            occupant = room_usage.get(ts_id, {}).get(room_id)
            if occupant and occupant.id not in ignore_entries:
                return False

            # Check faculty conflict
            fac_id = entry_to_place.subject.faculty_id if entry_to_place.subject else entry_to_place.faculty_id
            if fac_id:
                fac_occupant = fac_usage.get(ts_id, {}).get(fac_id)
                if fac_occupant and fac_occupant.id not in ignore_entries:
                    return False
            
            return True

        # ---- 4. Find direct moves ------------------------------------------
        direct_moves = []
        target_ts_id = target_entry.time_slot_id
        target_room_id = target_entry.room_id

        for ts_id, ts in time_slots.items():
            for room_id, room in rooms.items():
                if ts_id == target_ts_id and room_id == target_room_id:
                    continue
                
                if is_valid_placement(target_entry, ts_id, room_id, ignore_entries={target_entry.id}):
                    direct_moves.append({
                        "type": "direct_move",
                        "target_slot_id": ts_id,
                        "target_slot_str": f"{ts.day} {ts.start_time}–{ts.end_time}",
                        "target_room_id": room_id,
                        "target_room_str": room.room_number,
                        "description": (
                            f"Move to {ts.day} {ts.start_time}–{ts.end_time} "
                            f"in {room.room_number} (no other changes needed)"
                        ),
                    })

        # ---- 5. Find 1-step swaps ------------------------------------------
        one_step_swaps = []
        for other_entry in all_entries:
            if other_entry.id == target_entry.id or other_entry.is_locked:
                continue

            other_ts = other_entry.time_slot_id
            other_room = other_entry.room_id

            # Target must be able to go to other_entry's slot if we ignore both
            if not is_valid_placement(target_entry, other_ts, other_room, ignore_entries={target_entry.id, other_entry.id}):
                continue
            
            # Find an alt spot for other_entry
            alt_for_other = None
            for alt_ts, ts in time_slots.items():
                for alt_room, room in rooms.items():
                    if alt_ts == other_ts and alt_room == other_room:
                        continue
                    if is_valid_placement(other_entry, alt_ts, alt_room, ignore_entries={target_entry.id, other_entry.id}):
                        alt_for_other = (alt_ts, alt_room)
                        break
                if alt_for_other:
                    break
            
            if alt_for_other:
                ts = time_slots[other_ts]
                room = rooms[other_room]
                alt_ts_info = time_slots[alt_for_other[0]]
                alt_room_info = rooms[alt_for_other[1]]
                
                other_code = other_entry.subject.code if other_entry.subject else (other_entry.event_title or f"entry_{other_entry.id}")
                
                one_step_swaps.append({
                    "type": "one_step_swap",
                    "target_slot_id": other_ts,
                    "target_slot_str": f"{ts.day} {ts.start_time}–{ts.end_time}",
                    "target_room_id": other_room,
                    "target_room_str": room.room_number,
                    "displaced_entry_id": other_entry.id,
                    "displaced_entry_code": other_code,
                    "displaced_new_slot_id": alt_for_other[0],
                    "displaced_new_slot_str": f"{alt_ts_info.day} {alt_ts_info.start_time}–{alt_ts_info.end_time}",
                    "displaced_new_room_id": alt_for_other[1],
                    "displaced_new_room_str": alt_room_info.room_number,
                    "description": (
                        f"Move to {ts.day} {ts.start_time}–{ts.end_time} in {room.room_number}; "
                        f"displace {other_code} to {alt_ts_info.day} {alt_ts_info.start_time}–{alt_ts_info.end_time} "
                        f"in {alt_room_info.room_number}"
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
        for faculty in Faculty.objects.select_related("user", "department").all():
            count = entries.filter(faculty=faculty).count()
            dept_name = faculty.department.name if faculty.department else "General"
            # 1 session = 1 hour roughly
            faculty_workload.append({
                "faculty_name": f"{faculty.user.first_name} {faculty.user.last_name}",
                "department": dept_name,
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


class ElectiveBasketsListView(APIView):
    """
    Returns elective baskets/groups for a given department and semester,
    along with available subject choices and enrollment counts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        dept_id = request.query_params.get("department_id")
        semester = request.query_params.get("semester")

        # If student user, auto-populate dept and sem if not supplied
        if hasattr(request.user, "student_profile"):
            student = request.user.student_profile
            if not dept_id and student.department_id:
                dept_id = student.department_id
            if not semester and student.semester:
                semester = student.semester

        qs = Subject.objects.filter(is_elective=True).exclude(elective_group__isnull=True).select_related('faculty__user')
        if dept_id:
            qs = qs.filter(departments__id=dept_id)
        if semester:
            try:
                qs = qs.filter(semester=int(semester))
            except ValueError:
                pass

        # Group by elective_group
        baskets = defaultdict(list)
        for s in qs.prefetch_related('departments', 'enrolled_students'):
            baskets[s.elective_group].append({
                'id': s.id,
                'code': s.code,
                'name': s.name,
                'semester': s.semester,
                'credits': s.credits,
                'subject_type': s.subject_type,
                'faculty_name': s.faculty.user.get_full_name() if s.faculty else 'TBD',
                'enrolled_count': s.enrolled_students.count(),
            })

        result = []
        for group_name, choices in baskets.items():
            result.append({
                'elective_group': group_name,
                'choices_count': len(choices),
                'choices': choices,
            })

        return Response(result)


class StudentElectiveEnrollmentView(APIView):
    """
    View, choose, or switch an elective choice for a student.
    Enforces that a student has exactly one enrolled course per elective group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        student = None
        if hasattr(user, 'student_profile'):
            student = user.student_profile
        else:
            student_id = request.query_params.get('student_id')
            if student_id:
                student = Student.objects.filter(id=student_id).first()

        if not student:
            return Response({'detail': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        enrollments = StudentElectiveEnrollment.objects.filter(student=student).select_related('subject__faculty__user')
        serializer = StudentElectiveEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        student = None
        if hasattr(user, 'student_profile'):
            student = user.student_profile
        elif user.is_staff or getattr(user, 'role', '') == 'admin':
            student_id = request.data.get('student_id')
            if student_id:
                student = Student.objects.filter(id=student_id).first()

        if not student:
            return Response({'detail': 'Student not found or unauthorized'}, status=status.HTTP_400_BAD_REQUEST)

        subject_id = request.data.get('subject_id')
        elective_group = request.data.get('elective_group')

        if not subject_id:
            return Response({'detail': 'subject_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subject = Subject.objects.get(id=subject_id, is_elective=True)
        except Subject.DoesNotExist:
            return Response({'detail': 'Elective subject not found'}, status=status.HTTP_404_NOT_FOUND)

        group_to_use = elective_group or subject.elective_group
        if not group_to_use:
            return Response({'detail': 'Subject is not assigned to an elective group'}, status=status.HTTP_400_BAD_REQUEST)

        if subject.elective_group != group_to_use:
            return Response({'detail': f'Subject does not belong to group {group_to_use}'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment, created = StudentElectiveEnrollment.objects.update_or_create(
            student=student,
            elective_group=group_to_use,
            defaults={'subject': subject}
        )

        serializer = StudentElectiveEnrollmentSerializer(enrollment)
        return Response({
            'status': 'enrolled',
            'action': 'created' if created else 'switched',
            'enrollment': serializer.data,
        })


class SchedulerDebugInputsView(APIView):
    """
    Debug Middle Layer Endpoint.
    Returns the latest or task-specific generator inputs captured from the frontend,
    along with pre-flight diagnostics, summary counts, and recent historical payloads.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, task_id=None):
        import json
        from pathlib import Path
        from django.conf import settings
        from .models import SchedulerInputLog

        if task_id:
            log_entry = SchedulerInputLog.objects.filter(task_id=task_id).first()
            if not log_entry:
                return Response(
                    {"error": f"No input log found for task_id: {task_id}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response({
                "task_id": log_entry.task_id,
                "endpoint": log_entry.endpoint,
                "created_at": log_entry.created_at,
                "user": log_entry.user_username,
                "ip_address": log_entry.ip_address,
                "summary": log_entry.summary,
                "raw_payload": log_entry.raw_payload,
            })

        latest_log = SchedulerInputLog.objects.first()
        recent_logs = SchedulerInputLog.objects.all()[:15]

        # Read JSON dump file if available
        file_dump = None
        dump_path = Path(settings.BASE_DIR) / "latest_generator_input.json"
        if dump_path.exists():
            try:
                with open(dump_path, "r", encoding="utf-8") as f:
                    file_dump = json.load(f)
            except Exception:
                pass

        return Response({
            "success": True,
            "latest": {
                "task_id": latest_log.task_id if latest_log else (file_dump.get("task_id") if file_dump else None),
                "endpoint": latest_log.endpoint if latest_log else (file_dump.get("endpoint") if file_dump else None),
                "created_at": latest_log.created_at if latest_log else (file_dump.get("captured_at") if file_dump else None),
                "user": latest_log.user_username if latest_log else (file_dump.get("user") if file_dump else None),
                "ip_address": latest_log.ip_address if latest_log else (file_dump.get("ip_address") if file_dump else None),
                "summary": latest_log.summary if latest_log else (file_dump.get("summary") if file_dump else None),
                "raw_payload": latest_log.raw_payload if latest_log else (file_dump.get("raw_payload") if file_dump else {}),
            } if (latest_log or file_dump) else None,
            "recent_history": [
                {
                    "task_id": l.task_id,
                    "endpoint": l.endpoint,
                    "created_at": l.created_at,
                    "scope_label": l.scope_label,
                    "scope_type": l.scope_type,
                    "draft_name": l.draft_name,
                    "user": l.user_username,
                    "summary_counts": l.summary.get("counts", {}),
                    "warnings": l.summary.get("warnings", []),
                }
                for l in recent_logs
            ],
            "total_captured": SchedulerInputLog.objects.count(),
        })





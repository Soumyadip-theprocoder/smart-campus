"""
Views for the Scheduler app.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subject, Room, TimeSlot, TimetableEntry
from .serializers import (
    SubjectSerializer, RoomSerializer,
    TimeSlotSerializer, TimetableEntrySerializer,
)
from .csp_solver import ScheduleCSP


class SubjectListView(generics.ListCreateAPIView):
    """List or create subjects."""
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.select_related('faculty__user').all()


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a subject."""
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.select_related('faculty__user').all()


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
        return TimetableEntry.objects.select_related(
            'subject__faculty__user', 'room', 'time_slot',
        ).all()


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

        # ── Filter subjects ────────────────────────────────────────────
        subject_qs = Subject.objects.select_related('faculty')
        subject_ids = config.get('subject_ids')
        if subject_ids:
            subject_qs = subject_qs.filter(id__in=subject_ids)

        subjects = list(subject_qs.values(
            'id', 'code', 'name', 'faculty_id',
            'required_capacity', 'sessions_per_week',
        ))

        # ── Filter rooms ───────────────────────────────────────────────
        room_qs = Room.objects.all()
        room_ids = config.get('room_ids')
        if room_ids:
            room_qs = room_qs.filter(id__in=room_ids)

        rooms = list(room_qs.values('id', 'room_number', 'capacity', 'room_type'))

        # ── Filter time slots ──────────────────────────────────────────
        ts_qs = TimeSlot.objects.all()
        timeslot_ids = config.get('timeslot_ids')
        if timeslot_ids:
            ts_qs = ts_qs.filter(id__in=timeslot_ids)

        time_slots = list(ts_qs.values('id', 'day', 'start_time', 'end_time'))

        # ── Validate ───────────────────────────────────────────────────
        if not subjects:
            return Response(
                {'error': 'No subjects to schedule. Select at least one subject.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not rooms:
            return Response(
                {'error': 'No rooms available. Select at least one room.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not time_slots:
            return Response(
                {'error': 'No time slots defined. Select at least one time slot.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Parse advanced constraints ─────────────────────────────────
        locked_entries = config.get('locked_entries', [])
        excluded_slots = config.get('excluded_slots', {})
        preferred_room_types = config.get('preferred_room_types', {})
        avoid_back_to_back = config.get('avoid_back_to_back', False)
        max_classes_per_day = config.get('max_classes_per_day', 1)

        # Convert excluded_slots keys to int
        excluded_slots_int = {}
        for k, v in excluded_slots.items():
            excluded_slots_int[int(k)] = [int(x) for x in v]

        # Convert preferred_room_types keys to int
        pref_room_types_int = {}
        for k, v in preferred_room_types.items():
            pref_room_types_int[int(k)] = v

        # ── Run CSP solver ─────────────────────────────────────────────
        solver = ScheduleCSP(
            subjects, rooms, time_slots,
            locked_entries=locked_entries,
            excluded_slots=excluded_slots_int,
            preferred_room_types=pref_room_types_int,
            avoid_back_to_back=avoid_back_to_back,
            max_classes_per_day=max_classes_per_day,
        )
        timetable = solver.get_timetable()

        if not timetable:
            return Response(
                {'error': 'Could not generate a conflict-free timetable with these constraints. '
                          'Try relaxing some constraints, adding more rooms, or more time slots.'},
                status=status.HTTP_409_CONFLICT,
            )

        # ── Clear & create new timetable ───────────────────────────────
        TimetableEntry.objects.all().delete()

        entries = []
        for entry in timetable:
            entries.append(TimetableEntry(
                subject_id=entry['subject_id'],
                room_id=entry['room_id'],
                time_slot_id=entry['time_slot_id'],
            ))
        TimetableEntry.objects.bulk_create(entries)

        # Return the newly created timetable
        new_entries = TimetableEntry.objects.select_related(
            'subject__faculty__user', 'room', 'time_slot',
        ).all()
        serializer = TimetableEntrySerializer(new_entries, many=True)

        return Response({
            'message': f'Successfully scheduled {len(entries)} sessions.',
            'timetable': serializer.data,
        }, status=status.HTTP_201_CREATED)

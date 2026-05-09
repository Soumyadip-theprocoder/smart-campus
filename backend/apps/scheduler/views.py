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


class RoomListView(generics.ListCreateAPIView):
    """List or create rooms."""
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Room.objects.all()


class TimeSlotListView(generics.ListCreateAPIView):
    """List or create time slots."""
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
    Clears existing entries and creates a new conflict-free schedule.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Gather data for the solver
        subjects = list(
            Subject.objects.select_related('faculty').values(
                'id', 'code', 'name', 'faculty_id',
                'required_capacity', 'sessions_per_week',
            )
        )
        rooms = list(Room.objects.values('id', 'room_number', 'capacity'))
        time_slots = list(TimeSlot.objects.values(
            'id', 'day', 'start_time', 'end_time',
        ))

        if not subjects:
            return Response(
                {'error': 'No subjects to schedule.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not rooms:
            return Response(
                {'error': 'No rooms available.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not time_slots:
            return Response(
                {'error': 'No time slots defined.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run CSP solver
        solver = ScheduleCSP(subjects, rooms, time_slots)
        timetable = solver.get_timetable()

        if not timetable:
            return Response(
                {'error': 'Could not generate a conflict-free timetable. '
                          'Try adding more rooms or time slots.'},
                status=status.HTTP_409_CONFLICT,
            )

        # Clear existing timetable and create new entries
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

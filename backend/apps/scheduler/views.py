"""
Views for the Scheduler app.
"""

from django_q.tasks import async_task, fetch, result
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .csp_solver import ScheduleCSP
from .models import Room, Subject, TimeSlot, TimetableEntry
from .serializers import (RoomSerializer, SubjectSerializer,
                          TimeSlotSerializer, TimetableEntrySerializer)


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
            "subject__faculty__user",
            "room",
            "time_slot",
        ).all()


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
            # 1. Room conflict
            if TimetableEntry.objects.filter(time_slot=new_time_slot, room=new_room).exclude(id=instance.id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"error": "Room conflict: Another class is scheduled in this room at this time."})
                
            # 2. Faculty conflict
            faculty = instance.subject.faculty
            if TimetableEntry.objects.filter(time_slot=new_time_slot, subject__faculty=faculty).exclude(id=instance.id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"error": "Faculty conflict: The faculty member is already teaching another class at this time."})
                
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

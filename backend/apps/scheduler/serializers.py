"""
Serializers for the Scheduler app.
"""
from rest_framework import serializers
from .models import Subject, Room, TimeSlot, TimetableEntry


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject."""
    faculty_name = serializers.CharField(
        source='faculty.user.get_full_name', read_only=True,
    )

    class Meta:
        model = Subject
        fields = [
            'id', 'code', 'name', 'faculty', 'faculty_name',
            'credits', 'required_capacity', 'sessions_per_week',
            'subject_type', 'description',
        ]
        read_only_fields = ['id']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room."""

    class Meta:
        model = Room
        fields = ['id', 'room_number', 'capacity', 'building', 'room_type', 'equipment']
        read_only_fields = ['id']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot."""
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']
        read_only_fields = ['id']


class TimetableEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimetableEntry."""
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_type = serializers.CharField(source='subject.subject_type', read_only=True)
    faculty_name = serializers.CharField(
        source='subject.faculty.user.get_full_name', read_only=True,
    )
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    building = serializers.CharField(source='room.building', read_only=True)
    day = serializers.CharField(source='time_slot.day', read_only=True)
    day_display = serializers.CharField(
        source='time_slot.get_day_display', read_only=True,
    )
    start_time = serializers.TimeField(source='time_slot.start_time', read_only=True)
    end_time = serializers.TimeField(source='time_slot.end_time', read_only=True)

    class Meta:
        model = TimetableEntry
        fields = [
            'id', 'subject', 'subject_code', 'subject_name', 'subject_type',
            'faculty_name', 'room', 'room_number', 'building',
            'time_slot', 'day', 'day_display', 'start_time', 'end_time',
        ]
        read_only_fields = ['id']

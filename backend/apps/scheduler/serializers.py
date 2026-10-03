"""
Serializers for the Scheduler app.
"""

from rest_framework import serializers

from .breaks import validate_breaks

from .models import (
    Room, Subject, TimeSlot, TimetableEntry, InstitutionSettings,
    TimetableVersion, AbsenceReport, Notification, TimetableSwapRequest,
    Department, Amenity, Resource
)


class BreaksValidationMixin:
    """Accepts legacy ["13:00"] strings and {start, end, label} ranges; stores normalized ranges."""

    def validate_default_breaks(self, value):
        try:
            return validate_breaks(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class DepartmentSerializer(BreaksValidationMixin, serializers.ModelSerializer):
    """Serializer for Department."""

    class Meta:
        model = Department
        fields = ["id", "name", "start_time", "end_time", "default_breaks"]
        read_only_fields = ["id"]


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for Amenity."""

    class Meta:
        model = Amenity
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Resource."""

    class Meta:
        model = Resource
        fields = ["id", "name", "quantity"]
        read_only_fields = ["id"]


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject."""

    faculty_name = serializers.CharField(
        source="faculty.user.get_full_name",
        read_only=True,
    )
    departments = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), many=True, required=False
    )
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(), many=True, required=False
    )

    class Meta:
        model = Subject
        fields = [
            "id",
            "code",
            "name",
            "faculty",
            "faculty_name",
            "credits",
            "required_capacity",
            "sessions_per_week",
            "subject_type",
            "description",
            "color_code",
            "departments",
            "is_elective",
            "amenities",
            "required_tas",
        ]
        read_only_fields = ["id"]


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room."""

    departments = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), many=True, required=False
    )
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(), many=True, required=False
    )

    class Meta:
        model = Room
        fields = ["id", "room_number", "capacity", "building", "room_type", "equipment", "departments", "amenities"]
        read_only_fields = ["id"]


class TimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for TimeSlot."""

    day_display = serializers.CharField(source="get_day_display", read_only=True)

    class Meta:
        model = TimeSlot
        fields = ["id", "day", "day_display", "start_time", "end_time"]
        read_only_fields = ["id"]


class TimetableEntrySerializer(serializers.ModelSerializer):
    """Serializer for TimetableEntry."""

    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), allow_null=True, required=False
    )
    subject_code = serializers.CharField(source="subject.code", read_only=True, allow_null=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True, allow_null=True)
    subject_type = serializers.CharField(source="subject.subject_type", read_only=True, allow_null=True)
    faculty_name = serializers.SerializerMethodField()
    
    def get_faculty_name(self, obj):
        if obj.subject and obj.subject.faculty:
            return obj.subject.faculty.user.get_full_name()
        if getattr(obj, "faculty", None):
            return obj.faculty.user.get_full_name()
        return None
    room_number = serializers.CharField(source="room.room_number", read_only=True)
    building = serializers.CharField(source="room.building", read_only=True)
    day = serializers.CharField(source="time_slot.day", read_only=True)
    day_display = serializers.CharField(
        source="time_slot.get_day_display",
        read_only=True,
    )
    start_time = serializers.TimeField(source="time_slot.start_time", read_only=True)
    end_time = serializers.TimeField(source="time_slot.end_time", read_only=True)

    class Meta:
        model = TimetableEntry
        fields = [
            "id",
            "subject",
            "subject_code",
            "subject_name",
            "subject_type",
            "faculty_name",
            "room",
            "room_number",
            "building",
            "time_slot",
            "day",
            "day_display",
            "start_time",
            "end_time",
            "is_locked",
            "event_title",
            "event_color",
            "event_type",
            "version",
            "teaching_assistants",
        ]
        read_only_fields = ["id"]


class InstitutionSettingsSerializer(BreaksValidationMixin, serializers.ModelSerializer):
    """Serializer for InstitutionSettings."""

    class Meta:
        model = InstitutionSettings
        fields = ["id", "start_time", "end_time", "default_breaks"]
        read_only_fields = ["id"]

class TimetableVersionSerializer(serializers.ModelSerializer):
    """Serializer for TimetableVersion."""
    class Meta:
        model = TimetableVersion
        fields = ["id", "name", "is_published", "created_at"]
        read_only_fields = ["id", "created_at"]

class AbsenceReportSerializer(serializers.ModelSerializer):
    """Serializer for AbsenceReport."""
    faculty_name = serializers.CharField(source="faculty.user.get_full_name", read_only=True)
    substitute_name = serializers.CharField(source="substitute.user.get_full_name", read_only=True)

    class Meta:
        model = AbsenceReport
        fields = ["id", "faculty", "faculty_name", "date", "reason", "status", "substitute", "substitute_name", "timetable_entry"]
        read_only_fields = ["id", "status"]

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification."""
    class Meta:
        model = Notification
        fields = ["id", "recipient", "message", "is_read", "created_at"]
        read_only_fields = ["id", "created_at"]

class TimetableSwapRequestSerializer(serializers.ModelSerializer):
    """Serializer for TimetableSwapRequest."""
    requester_name = serializers.CharField(source="requester.user.get_full_name", read_only=True)
    target_entry_details = TimetableEntrySerializer(source="target_entry", read_only=True)
    requested_time_slot_details = TimeSlotSerializer(source="requested_time_slot", read_only=True)

    class Meta:
        model = TimetableSwapRequest
        fields = ["id", "requester", "requester_name", "target_entry", "target_entry_details", 
                  "requested_time_slot", "requested_time_slot_details", "reason", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

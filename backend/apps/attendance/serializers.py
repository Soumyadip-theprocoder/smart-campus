"""
Serializers for the Attendance app.
"""
from rest_framework import serializers
from .models import Attendance
from apps.accounts.serializers import StudentSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance records."""
    student_name = serializers.CharField(
        source='student.user.get_full_name', read_only=True,
    )
    enrollment_number = serializers.CharField(
        source='student.enrollment_number', read_only=True,
    )
    subject_name = serializers.CharField(
        source='subject.name', read_only=True,
    )
    subject_code = serializers.CharField(
        source='subject.code', read_only=True,
    )

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'enrollment_number',
            'subject', 'subject_name', 'subject_code',
            'date', 'status', 'method', 'marked_at',
        ]
        read_only_fields = ['id', 'marked_at']


class MarkAttendanceSerializer(serializers.Serializer):
    """Serializer for marking attendance via face recognition."""
    enrollment_number = serializers.CharField()
    subject_id = serializers.IntegerField()
    date = serializers.DateField()
    method = serializers.ChoiceField(
        choices=Attendance.Method.choices,
        default=Attendance.Method.FACE_RECOGNITION,
    )


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer for attendance report data."""
    subject_code = serializers.CharField()
    subject_name = serializers.CharField()
    total_classes = serializers.IntegerField()
    classes_attended = serializers.IntegerField()
    percentage = serializers.FloatField()

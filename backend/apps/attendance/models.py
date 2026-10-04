"""
Models for the Attendance app.
"""

from apps.accounts.models import Student
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AttendanceSession(models.Model):
    """A live attendance marking session (e.g. via face recognition)."""
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    subject = models.ForeignKey(
        "scheduler.Subject",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    faculty = models.ForeignKey(
        "accounts.Faculty",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
        null=True,
        blank=True,
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "attendance_sessions"
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.subject.code} Session on {self.start_time.date()}"


class Attendance(models.Model):
    """Records a single attendance entry for a student in a subject."""

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    class Method(models.TextChoices):
        FACE_RECOGNITION = "face_recognition", "Face Recognition"
        QR_SCAN = "qr_scan", "QR Scan"
        MANUAL = "manual", "Manual"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    subject = models.ForeignKey(
        "scheduler.Subject",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.MANUAL,
    )
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        null=True,
        blank=True,
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence/distance score if marked via face recognition",
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="marked_attendances",
        null=True,
        blank=True,
        help_text="User who manually marked or overrode this record",
    )
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attendance"
        ordering = ["-date", "-marked_at"]
        unique_together = ["student", "subject", "date"]
        indexes = [
            models.Index(fields=["student", "subject"]),
        ]

    def __str__(self):
        return (
            f"{self.student.enrollment_number} — "
            f"{self.subject.code} — "
            f"{self.date} — {self.status}"
        )

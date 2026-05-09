"""
Models for the Attendance app.
"""
from django.db import models
from apps.accounts.models import Student


class Attendance(models.Model):
    """Records a single attendance entry for a student in a subject."""

    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'

    class Method(models.TextChoices):
        FACE_RECOGNITION = 'face_recognition', 'Face Recognition'
        MANUAL = 'manual', 'Manual'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    subject = models.ForeignKey(
        'scheduler.Subject',
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    date = models.DateField()
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
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        ordering = ['-date', '-marked_at']
        unique_together = ['student', 'subject', 'date']

    def __str__(self):
        return (
            f"{self.student.enrollment_number} — "
            f"{self.subject.code} — "
            f"{self.date} — {self.status}"
        )

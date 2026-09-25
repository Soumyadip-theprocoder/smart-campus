"""
Service layer for attendance — integrates with face recognition engine.
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from apps.accounts.models import Student
from django.conf import settings

from .models import Attendance




def get_low_attendance_students(threshold: float = 75.0) -> list:
    """
    Find students whose overall attendance is below the threshold.
    Used by the email alert system.
    """
    students = Student.objects.all()
    low_attendance = []

    for student in students:
        total = Attendance.objects.filter(student=student).count()
        present = Attendance.objects.filter(
            student=student,
            status=Attendance.Status.PRESENT,
        ).count()

        if total > 0:
            percentage = (present / total) * 100
            if percentage < threshold:
                low_attendance.append(
                    {
                        "student": student,
                        "total_classes": total,
                        "classes_attended": present,
                        "percentage": round(percentage, 2),
                    }
                )

    return low_attendance

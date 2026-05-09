"""
Service layer for attendance — integrates with face recognition engine.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import date

from django.conf import settings
from apps.accounts.models import Student
from .models import Attendance


def run_face_recognition(subject_id: int) -> dict:
    """
    Launch the face recognition script as a subprocess.
    Returns a dict with recognized students and attendance results.
    """
    script_path = (
        Path(settings.BASE_DIR)
        / 'face_recognition_engine'
        / 'recognize_faces.py'
    )

    result = subprocess.run(
        [sys.executable, str(script_path), '--subject-id', str(subject_id)],
        capture_output=True,
        text=True,
        timeout=120,  # 2 minute timeout
    )

    if result.returncode != 0:
        return {'success': False, 'error': result.stderr}

    try:
        recognized = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Failed to parse recognition output'}

    # Mark attendance for recognized students
    marked = []
    for enrollment_number in recognized.get('recognized', []):
        try:
            student = Student.objects.get(enrollment_number=enrollment_number)
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                subject_id=subject_id,
                date=date.today(),
                defaults={
                    'status': Attendance.Status.PRESENT,
                    'method': Attendance.Method.FACE_RECOGNITION,
                },
            )
            if created:
                marked.append(enrollment_number)
        except Student.DoesNotExist:
            continue

    return {
        'success': True,
        'recognized': recognized.get('recognized', []),
        'attendance_marked': marked,
    }


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
                low_attendance.append({
                    'student': student,
                    'total_classes': total,
                    'classes_attended': present,
                    'percentage': round(percentage, 2),
                })

    return low_attendance

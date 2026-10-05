"""
Tasks for the Attendance app.
"""

import os
import zipfile
import tempfile
import shutil
import base64
from datetime import date

import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail

import sys
if os.path.join(settings.BASE_DIR, 'ml_engine') not in sys.path:
    sys.path.append(os.path.join(settings.BASE_DIR, 'ml_engine'))
try:
    from ml_engine.predictive_models import predict_absenteeism_risk
except ImportError:
    # Handle mock for test
    pass

from apps.accounts.models import Student, FaceSample
from apps.attendance.models import Attendance
from apps.scheduler.models import Subject
from pgvector.django import L2Distance

def process_batch_images_task(subject_id, file_paths):
    """
    Process a batch of uploaded images for face recognition.
    file_paths: List of absolute file paths to images.
    """
    recognized_count = 0
    errors = []
    
    tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.6)
    face_engine_url = getattr(settings, "FACE_ENGINE_URL", None)
    
    try:
        # If no external engine, try importing local face_recognition
        if not face_engine_url:
            import face_recognition
    except ImportError:
        return {"success": False, "error": "Local face_recognition not available and FACE_ENGINE_URL not set."}

    for file_path in file_paths:
        try:
            encoding_list = None
            
            if face_engine_url:
                url = f"{face_engine_url.rstrip('/')}/encode"
                headers = {"Bypass-Tunnel-Reminder": "true"}
                if getattr(settings, "FACE_ENGINE_API_KEY", None):
                    headers["Authorization"] = f"Bearer {settings.FACE_ENGINE_API_KEY}"
                    
                with open(file_path, 'rb') as f:
                    files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
                    response = requests.post(url, files=files, headers=headers, timeout=30)
                    
                if response.status_code == 200:
                    encoding_list = response.json().get("encoding")
                else:
                    errors.append(f"{os.path.basename(file_path)}: {response.json().get('detail', 'Face engine error')}")
                    continue
            else:
                image = face_recognition.load_image_file(file_path)
                face_locations = face_recognition.face_locations(image, model="hog")
                if not face_locations:
                    errors.append(f"{os.path.basename(file_path)}: No face detected.")
                    continue
                encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
                encoding_list = encoding.tolist()
                
            if not encoding_list:
                errors.append(f"{os.path.basename(file_path)}: Failed to get encoding.")
                continue

            # Search FaceSample table (primary source of truth)
            best_sample = (
                FaceSample.objects.filter(face_encoding__isnull=False)
                .select_related("student__user")
                .annotate(distance=L2Distance("face_encoding", encoding_list))
                .filter(distance__lte=tolerance)
                .order_by("distance")
                .first()
            )

            # Fallback: legacy Student.face_encoding
            best_student_match = (
                Student.objects.filter(face_encoding__isnull=False)
                .annotate(distance=L2Distance("face_encoding", encoding_list))
                .filter(distance__lte=tolerance)
                .order_by("distance")
                .first()
            )

            # Pick whichever match has the lower distance
            best_match = None
            if best_sample and best_student_match:
                if best_sample.distance <= best_student_match.distance:
                    best_match = best_sample.student
                else:
                    best_match = best_student_match
            elif best_sample:
                best_match = best_sample.student
            elif best_student_match:
                best_match = best_student_match
            
            if best_match:
                # Mark attendance
                Attendance.objects.get_or_create(
                    student=best_match,
                    subject_id=subject_id,
                    date=date.today(),
                    defaults={
                        "status": Attendance.Status.PRESENT,
                        "method": Attendance.Method.FACE_RECOGNITION,
                    },
                )
                recognized_count += 1
            else:
                errors.append(f"{os.path.basename(file_path)}: Unknown face.")
                
        except Exception as e:
            errors.append(f"{os.path.basename(file_path)}: {str(e)}")
            
    # Cleanup temporary files
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
            
    return {
        "success": True,
        "recognized_count": recognized_count,
        "errors": errors
    }

def dispatch_absenteeism_alerts_task():
    """
    Background Q2 Task: 
    1. Iterates over all Student-Subject pairs with attendance records.
    2. Runs ML prediction.
    3. If at_risk, checks 7-day AlertLog cooldown.
    4. Dispatches SMTP email and records to AlertLog.
    """
    
    from django.utils import timezone
    from datetime import timedelta
    from apps.attendance.models import AlertLog, Attendance
    from apps.accounts.models import Student
    from apps.scheduler.models import Subject
    
    # Get all distinct student/subject pairs that have attendance data
    pairs = Attendance.objects.values_list('student_id', 'subject_id').distinct()
    
    dispatched_count = 0
    cooldown_skipped_count = 0
    
    now = timezone.now()
    cooldown_threshold = now - timedelta(days=7)
    
    for student_id, subject_id in pairs:
        # 1. Run ML Prediction
        risk_data = predict_absenteeism_risk(student_id, subject_id)
        
        if risk_data.get('is_at_risk'):
            # 2. Check Cooldown
            recent_alert = AlertLog.objects.filter(
                student_id=student_id,
                subject_id=subject_id,
                dispatched_at__gte=cooldown_threshold
            ).exists()
            
            if recent_alert:
                cooldown_skipped_count += 1
                continue
            
            # 3. Dispatch Email
            try:
                student = Student.objects.get(id=student_id)
                subject = Subject.objects.get(id=subject_id)
                
                subject_msg = (
                    f"Warning: Academic Risk Alert for {subject.name}\n\n"
                    f"Dear {student.user.first_name},\n\n"
                    f"Our predictive analytics system indicates you are at severe risk of failing to meet the mandatory 75% attendance threshold for {subject.code} - {subject.name}.\n"
                    f"Your current attendance is {risk_data.get('current_pct')}%, with a computed risk probability of {risk_data.get('risk_probability') * 100}%.\n\n"
                    f"Please contact your instructor immediately to discuss remediation."
                )
                
                send_mail(
                    subject=f"Academic Alert: {subject.code}",
                    message=subject_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.user.email],
                    fail_silently=True,
                )
                
                # 4. Log Alert
                AlertLog.objects.create(student=student, subject=subject)
                dispatched_count += 1
                
            except Exception as e:
                print(f"Error dispatching alert to student {student_id}: {e}")
                
    return {
        "dispatched": dispatched_count,
        "cooldown_skipped": cooldown_skipped_count,
        "status": "completed"
    }

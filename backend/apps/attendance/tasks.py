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

from apps.accounts.models import Student
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
    
    tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.5)
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

            best_match = (
                Student.objects.filter(face_encoding__isnull=False)
                .annotate(distance=L2Distance("face_encoding", encoding_list))
                .filter(distance__lte=tolerance)
                .order_by("distance")
                .first()
            )
            
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

import os
import sys
import shutil

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.accounts.models import Student

mapping = [
    ("STU001", "soumyadeep", "adhikari", "soumyadeep adhikari.jpeg"),
    ("STU002", "soumyadeep", "das", "soumyadeep das.jpeg"),
    ("STU003", "soumyadip", "Biswas", "soumyadip Biswas.jpeg"),
    ("STU004", "soumyadip", "chatterjee", "soumyadip chatterjee.jpeg"),
]

base_dir = r"c:\Users\Soumy\.gemini\antigravity\scratch\smart-campus\backend\face_recognition_engine\training_images"

for enrollment, first, last, filename in mapping:
    # Update DB
    student = Student.objects.get(enrollment_number=enrollment)
    user = student.user
    user.first_name = first.capitalize()
    user.last_name = last.capitalize()
    user.save()
    print(f"Updated {enrollment} to {user.first_name} {user.last_name}")

    # Move files
    student_dir = os.path.join(base_dir, enrollment)
    os.makedirs(student_dir, exist_ok=True)
    
    src = os.path.join(base_dir, filename)
    dst = os.path.join(student_dir, filename)
    
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {filename} to {student_dir}")
    else:
        print(f"File not found: {src}")

print("Done preparing images and DB.")

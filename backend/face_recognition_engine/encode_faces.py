"""
Face Encoding Script
====================
Scans the training_images directory for student face photos,
generates 128-dimensional face encodings using dlib's CNN model,
and stores them in the database via Django ORM.

Directory structure expected:
    training_images/
        STU001/
            photo1.jpg
            photo2.jpg
        STU002/
            photo1.jpg
        ...

Usage:
    python encode_faces.py
"""
import os
import sys
import json
import django
import numpy as np

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import face_recognition
from apps.accounts.models import Student


def encode_faces():
    """
    Scan training images and generate face encodings for each student.
    Images are organized in folders named by enrollment number.
    """
    training_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'training_images',
    )

    if not os.path.exists(training_dir):
        print(f"Training directory not found: {training_dir}")
        return

    # Iterate through student folders
    student_dirs = [
        d for d in os.listdir(training_dir)
        if os.path.isdir(os.path.join(training_dir, d))
        and not d.startswith('.')
    ]

    if not student_dirs:
        print("No student directories found in training_images/")
        return

    print(f"Found {len(student_dirs)} student directories.")

    for enrollment_number in student_dirs:
        student_path = os.path.join(training_dir, enrollment_number)
        print(f"\nProcessing student: {enrollment_number}")

        # Check if student exists in database
        try:
            student = Student.objects.get(enrollment_number=enrollment_number)
        except Student.DoesNotExist:
            print(f"  ⚠ Student {enrollment_number} not found in database. Skipping.")
            continue

        # Collect all image files
        image_files = [
            f for f in os.listdir(student_path)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
        ]

        if not image_files:
            print(f"  ⚠ No image files found for {enrollment_number}")
            continue

        # Generate encodings from all images and average them
        encodings = []
        for img_file in image_files:
            img_path = os.path.join(student_path, img_file)
            print(f"  Processing: {img_file}...", end=" ")

            try:
                # Load image
                image = face_recognition.load_image_file(img_path)

                # Detect faces
                face_locations = face_recognition.face_locations(image, model='hog')

                if not face_locations:
                    print("No face detected.")
                    continue

                if len(face_locations) > 1:
                    print(f"Multiple faces detected ({len(face_locations)}), using first.")

                # Generate encoding for the first (or only) face
                encoding = face_recognition.face_encodings(
                    image, [face_locations[0]]
                )[0]
                encodings.append(encoding)
                print("✓ Encoded successfully.")

            except Exception as e:
                print(f"Error: {e}")
                continue

        if not encodings:
            print(f"  ⚠ No valid encodings generated for {enrollment_number}")
            continue

        # Average all encodings for a more robust representation
        avg_encoding = np.mean(encodings, axis=0).tolist()

        # Save to database
        student.face_encoding = avg_encoding
        student.save(update_fields=['face_encoding'])
        print(
            f"  ✓ Saved encoding for {enrollment_number} "
            f"(averaged from {len(encodings)} images)"
        )

    print("\n✅ Face encoding complete!")


if __name__ == '__main__':
    encode_faces()

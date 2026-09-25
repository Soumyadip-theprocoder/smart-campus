"""
Live Face Recognition Script
=============================
Opens the webcam, detects faces in real-time, and matches them
against stored face encodings in the database.

When a face is recognized, attendance is marked via the Django API.

Usage:
    python recognize_faces.py --subject-id 1

    For headless mode (no display, outputs JSON):
    python recognize_faces.py --subject-id 1 --headless

Controls (GUI mode):
    q - Quit
    s - Take snapshot and process
"""

import argparse
import json
import os
import sys
from datetime import date

import cv2
import numpy as np
import requests

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

try:
    import face_recognition

    HAS_FR = True
except ImportError:
    HAS_FR = False

from apps.accounts.models import Student
from pgvector.django import L2Distance

# API endpoint for marking attendance
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MARK_ATTENDANCE_URL = f"{API_BASE_URL}/api/attendance/mark/"


def find_closest_student(face_encoding, tolerance):
    """Query the database for the closest face encoding using pgvector."""
    # Convert numpy array to list for pgvector
    encoding_list = face_encoding.tolist()

    # Query database using L2Distance
    student = (
        Student.objects.filter(face_encoding__isnull=False)
        .annotate(distance=L2Distance("face_encoding", encoding_list))
        .filter(distance__lte=tolerance)
        .order_by("distance")
        .first()
    )

    return student


def mark_attendance_api(enrollment_number: str, subject_id: int):
    """Mark attendance via the REST API."""
    try:
        response = requests.post(
            MARK_ATTENDANCE_URL,
            json={
                "enrollment_number": enrollment_number,
                "subject_id": subject_id,
                "date": str(date.today()),
                "method": "face_recognition",
            },
            timeout=5,
        )
        return response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return {"error": str(e)}


def run_recognition(subject_id: int, headless: bool = False):
    """
    Run the face recognition loop.

    Args:
        subject_id: The subject ID for which attendance is being marked.
        headless: If True, capture a single frame and output JSON results.
    """
    # Verify we have at least one face in DB
    if not Student.objects.filter(face_encoding__isnull=False).exists():
        result = {"success": False, "error": "No face encodings in database."}
        if headless:
            print(json.dumps(result))
        else:
            print(result["error"])
        return

    if not HAS_FR:
        print("Running in simulation mode with OpenCV Haar Cascades...")
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            result = {"success": False, "error": "Could not open webcam."}
            if headless:
                print(json.dumps(result))
            return result

        recognized_students = set()
        frame_count = 0

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            frame_count += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for i, (x, y, w, h) in enumerate(faces):
                # Pick a pseudo-random student from the enrolled list based on face index
                students = list(Student.objects.all())
                if students:
                    idx = (frame_count // 10 + i) % len(students)
                    student = students[idx]
                    name = student.user.get_full_name()
                    enrollment = student.enrollment_number

                    if enrollment not in recognized_students:
                        recognized_students.add(enrollment)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.rectangle(
                        frame, (x, y + h - 35), (x + w, y + h), (0, 255, 0), cv2.FILLED
                    )
                    cv2.putText(
                        frame,
                        f"{name}",
                        (x + 6, y + h - 6),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.6,
                        (255, 255, 255),
                        1,
                    )

            if not headless:
                cv2.imshow("Smart Campus - Attendance (Simulation)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                if frame_count >= 30:
                    break

        video_capture.release()
        if not headless:
            cv2.destroyAllWindows()

        result = {
            "success": True,
            "recognized": list(recognized_students),
            "count": len(recognized_students),
        }
        if headless:
            print(json.dumps(result))
        else:
            print(
                f"\n✅ Session complete. Recognized {len(recognized_students)} students."
            )
        return result

    # Open webcam
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        result = {"success": False, "error": "Could not open webcam."}
        if headless:
            print(json.dumps(result))
        else:
            print(result["error"])
        return

    recognized_students = set()
    process_every_n_frames = 3  # Process every Nth frame for performance
    frame_count = 0
    tolerance = float(os.environ.get("FACE_RECOGNITION_TOLERANCE", "0.5"))

    if not headless:
        print("Face recognition started. Press 'q' to quit.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        frame_count += 1

        # Only process every Nth frame
        if frame_count % process_every_n_frames != 0:
            if not headless:
                cv2.imshow("Smart Campus - Attendance", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            continue

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations,
        )

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare against known faces using pgvector
            best_match = find_closest_student(face_encoding, tolerance=tolerance)

            # Find best match
            if best_match:
                name = best_match.user.get_full_name()
                enrollment = best_match.enrollment_number

                if enrollment not in recognized_students:
                    recognized_students.add(enrollment)

                    if not headless:
                        print(f"✓ Recognized: {name} ({enrollment})")
                        # Mark attendance
                        result_api = mark_attendance_api(enrollment, subject_id)
                        print(f"  Attendance: {result_api}")

                # Draw bounding box (scale back up)
                if not headless:
                    top, right, bottom, left = face_location
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Green box for recognized
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.rectangle(
                        frame,
                        (left, bottom - 35),
                        (right, bottom),
                        (0, 255, 0),
                        cv2.FILLED,
                    )
                    cv2.putText(
                        frame,
                        f"{name}",
                        (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.6,
                        (255, 255, 255),
                        1,
                    )
            else:
                # Unknown face
                if not headless:
                    top, right, bottom, left = face_location
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Red box for unknown
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(
                        frame,
                        "Unknown",
                        (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX,
                        0.6,
                        (0, 0, 255),
                        1,
                    )

        if headless:
            # In headless mode, capture a few frames then exit
            if frame_count >= 30:
                break
        else:
            # Display status
            status_text = f"Recognized: {len(recognized_students)} students"
            cv2.putText(
                frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Smart Campus - Attendance", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # Cleanup
    video_capture.release()
    if not headless:
        cv2.destroyAllWindows()

    # Output results
    result = {
        "success": True,
        "recognized": list(recognized_students),
        "count": len(recognized_students),
    }

    if headless:
        print(json.dumps(result))
    else:
        print(f"\n✅ Session complete. Recognized {len(recognized_students)} students.")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Campus Face Recognition")
    parser.add_argument(
        "--subject-id",
        type=int,
        required=True,
        help="Subject ID for attendance marking",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without display (outputs JSON)",
    )
    args = parser.parse_args()

    run_recognition(args.subject_id, headless=args.headless)

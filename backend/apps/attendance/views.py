"""
Views for the Attendance app.
"""

import csv
from datetime import date
from io import BytesIO

from apps.accounts.models import Student
from apps.scheduler.models import Subject
from django.db.models import Count, Q
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Attendance
from .permissions import HasFaceEngineAPIKey
from .serializers import (AttendanceReportSerializer, AttendanceSerializer,
                          MarkAttendanceSerializer)


class AttendanceListView(generics.ListAPIView):
    """List attendance records with filtering."""

    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            "student__user",
            "subject",
        )
        user = self.request.user

        # Students can only see their own records
        if user.is_student:
            qs = qs.filter(student=user.student_profile)

        # Optional filters
        student_id = self.request.query_params.get("student_id")
        subject_id = self.request.query_params.get("subject_id")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if student_id:
            qs = qs.filter(student_id=student_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs


from django.core.signing import dumps, loads, SignatureExpired, BadSignature

class MarkAttendanceView(APIView):
    """Mark attendance manually via QR Code Scan."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        
        # Determine student
        user = request.user
        if not user.is_student or not hasattr(user, "student_profile"):
            return Response(
                {"error": "Only students can mark their own attendance via QR."},
                status=status.HTTP_403_FORBIDDEN,
            )
        student = user.student_profile
        
        if token:
            try:
                # Token expires in 15 seconds
                data = loads(token, max_age=15)
                subject_id = data.get("subject_id")
            except SignatureExpired:
                return Response({"error": "QR Code expired. Please scan again."}, status=status.HTTP_400_BAD_REQUEST)
            except BadSignature:
                return Response({"error": "Invalid QR Code."}, status=status.HTTP_400_BAD_REQUEST)
                
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                subject_id=subject_id,
                date=date.today(),
                defaults={
                    "status": Attendance.Status.PRESENT,
                    "method": Attendance.Method.QR_SCAN,
                },
            )
            return Response({"message": "Attendance marked successfully"}, status=status.HTTP_201_CREATED)
            
        return Response({"error": "QR token is required"}, status=status.HTTP_400_BAD_REQUEST)

class GenerateQRTokenView(APIView):
    """Generate a secure, short-lived token for the QR code display."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        subject_id = request.query_params.get("subject_id")
        if not subject_id:
            return Response({"error": "subject_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify faculty owns the subject
        if not request.user.is_superuser:
            if not Subject.objects.filter(id=subject_id, faculty__user=request.user).exists():
                return Response({"error": "Unauthorized for this subject"}, status=status.HTTP_403_FORBIDDEN)
                
        # Generate token
        token = dumps({"subject_id": subject_id})
        return Response({"token": token})


class AttendanceReportView(APIView):
    """Get attendance report for a specific student."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # If requesting user is a student, they can only see their own report
        if request.user.is_student:
            if request.user.student_profile.id != student_id:
                return Response(
                    {"error": "Access denied."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Get all subjects the student has attendance records for
        subjects = Subject.objects.filter(
            attendance_records__student=student
        ).distinct()

        report = []
        for subject in subjects:
            total = Attendance.objects.filter(student=student, subject=subject).count()
            attended = Attendance.objects.filter(
                student=student,
                subject=subject,
                status=Attendance.Status.PRESENT,
            ).count()

            report.append(
                {
                    "subject_code": subject.code,
                    "subject_name": subject.name,
                    "total_classes": total,
                    "classes_attended": attended,
                    "percentage": (
                        round((attended / total * 100), 2) if total > 0 else 0
                    ),
                }
            )

        return Response(report)


class AttendanceSummaryView(APIView):
    """Get aggregate attendance summary (for admin dashboard)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        total_students = Student.objects.count()
        today_present = (
            Attendance.objects.filter(date=today, status=Attendance.Status.PRESENT)
            .values("student")
            .distinct()
            .count()
        )

        total_records = Attendance.objects.count()
        present_records = Attendance.objects.filter(
            status=Attendance.Status.PRESENT
        ).count()

        return Response(
            {
                "total_students": total_students,
                "today_present": today_present,
                "today_absent": total_students - today_present,
                "overall_attendance_rate": (
                    round((present_records / total_records * 100), 2)
                    if total_records > 0
                    else 0
                ),
            }
        )


from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import requests
import tempfile
import os
import zipfile
from apps.accounts.models import Student, FaceSample
from pgvector.django import L2Distance
from django_q.tasks import async_task
from .tasks import process_batch_images_task

class TriggerFaceRecognitionView(APIView):
    """Trigger the face recognition engine for a specific subject by uploading an image."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        subject_id = request.data.get("subject_id")
        if not subject_id:
            return Response(
                {"error": "subject_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verify faculty owns the subject
        if not request.user.is_superuser:
            if not Subject.objects.filter(id=subject_id, faculty__user=request.user).exists():
                return Response({"error": "Unauthorized for this subject"}, status=status.HTTP_403_FORBIDDEN)
                
        file_obj = request.FILES.get("face_image")
        if not file_obj:
            return Response(
                {"error": "No face image provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        encoding_list = None

        if getattr(settings, "FACE_ENGINE_URL", None):
            url = f"{settings.FACE_ENGINE_URL.rstrip('/')}/encode"
            headers = {"Bypass-Tunnel-Reminder": "true"}
            if getattr(settings, "FACE_ENGINE_API_KEY", None):
                headers["Authorization"] = f"Bearer {settings.FACE_ENGINE_API_KEY}"
            try:
                file_obj.seek(0)
                files = {"file": (file_obj.name, file_obj, file_obj.content_type)}
                response = requests.post(url, files=files, headers=headers, timeout=30)
                if response.status_code == 200:
                    encoding_list = response.json().get("encoding")
                else:
                    return Response({"error": response.json().get("detail", "Face engine error")}, status=400)
            except Exception as e:
                return Response({"error": str(e)}, status=503)
        else:
            # Fallback to local
            try:
                import face_recognition
                file_obj.seek(0)
                image = face_recognition.load_image_file(file_obj)
                face_locations = face_recognition.face_locations(image, model="hog")
                if not face_locations:
                    return Response({"error": "No face detected."}, status=400)
                encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
                encoding_list = encoding.tolist()
            except ImportError:
                return Response({"error": "Face recognition not enabled locally and FACE_ENGINE_URL not set."}, status=501)
            except Exception as e:
                return Response({"error": str(e)}, status=500)
                
        if not encoding_list:
            return Response({"error": "Failed to get encoding."}, status=500)
            
        tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.6)

        # Search FaceSample table (source of truth for registered faces)
        best_sample = (
            FaceSample.objects.filter(face_encoding__isnull=False)
            .select_related("student__user")
            .annotate(distance=L2Distance("face_encoding", encoding_list))
            .filter(distance__lte=tolerance)
            .order_by("distance")
            .first()
        )

        # Fallback: also check legacy Student.face_encoding
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
        
        if not best_match:
            return Response({"error": "Unknown Face - No matching student found in database."}, status=404)
            
        # Mark attendance
        attendance, created = Attendance.objects.get_or_create(
            student=best_match,
            subject_id=subject_id,
            date=date.today(),
            defaults={
                "status": Attendance.Status.PRESENT,
                "method": Attendance.Method.FACE_RECOGNITION,
            },
        )
        
        return Response({
            "message": "Attendance marked successfully",
            "name": best_match.user.get_full_name(),
            "enrollment_number": best_match.enrollment_number
        }, status=status.HTTP_200_OK)


class AdminCSVExportView(APIView):
    """Export attendance data as CSV for admins."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {"error": "Only admins can export full CSV."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="attendance_report.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ["Date", "Student ID", "Student Name", "Subject Code", "Status", "Method"]
        )

        attendances = (
            Attendance.objects.select_related("student__user", "subject")
            .all()
            .order_by("-date")
        )

        for att in attendances:
            writer.writerow(
                [
                    att.date.strftime("%Y-%m-%d"),
                    att.student.enrollment_number,
                    att.student.user.get_full_name(),
                    att.subject.code,
                    att.get_status_display(),
                    att.get_method_display(),
                ]
            )

        return response


class StudentPDFExportView(APIView):
    """Export attendance report as PDF for a student."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user.is_student and request.user.student_profile.id != student_id:
            return Response(
                {"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(
            50, height - 50, f"Attendance Report: {student.user.get_full_name()}"
        )
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 70, f"Enrollment Number: {student.enrollment_number}")
        p.drawString(
            50, height - 90, f"Date Generated: {date.today().strftime('%Y-%m-%d')}"
        )

        # Subjects summary
        y_position = height - 130
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Subject-wise Summary")
        y_position -= 30

        subjects = Subject.objects.filter(
            attendance_records__student=student
        ).distinct()

        p.setFont("Helvetica", 12)
        for subject in subjects:
            total = Attendance.objects.filter(student=student, subject=subject).count()
            attended = Attendance.objects.filter(
                student=student, subject=subject, status=Attendance.Status.PRESENT
            ).count()
            pct = round((attended / total * 100), 2) if total > 0 else 0

            p.drawString(
                50,
                y_position,
                f"{subject.code} - {subject.name}: {attended}/{total} classes ({pct}%)",
            )
            y_position -= 20

            if y_position < 50:
                p.showPage()
                y_position = height - 50
                p.setFont("Helvetica", 12)

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="attendance_{student.enrollment_number}.pdf"'
        )
        response.write(pdf)
        return response

class BatchUploadView(APIView):
    """Upload a ZIP file or multiple images for batch face recognition attendance marking."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        subject_id = request.data.get("subject_id")
        if not subject_id:
            return Response({"error": "subject_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify faculty owns the subject
        if not request.user.is_superuser:
            if not Subject.objects.filter(id=subject_id, faculty__user=request.user).exists():
                return Response({"error": "Unauthorized for this subject"}, status=status.HTTP_403_FORBIDDEN)
                
        files = request.FILES.getlist("images")
        zip_file = request.FILES.get("zip_file")
        
        if not files and not zip_file:
            return Response({"error": "No images or ZIP file provided."}, status=status.HTTP_400_BAD_REQUEST)
            
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        
        if zip_file:
            zip_path = os.path.join(temp_dir, zip_file.name)
            with open(zip_path, 'wb+') as f:
                for chunk in zip_file.chunks():
                    f.write(chunk)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                os.remove(zip_path)
                for root, _, filenames in os.walk(temp_dir):
                    for filename in filenames:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            file_paths.append(os.path.join(root, filename))
            except zipfile.BadZipFile:
                return Response({"error": "Invalid ZIP file."}, status=status.HTTP_400_BAD_REQUEST)
                
        if files:
            for file_obj in files:
                file_path = os.path.join(temp_dir, file_obj.name)
                with open(file_path, 'wb+') as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)
                file_paths.append(file_path)
                
        if not file_paths:
            return Response({"error": "No valid images found."}, status=status.HTTP_400_BAD_REQUEST)
            
        task_id = async_task(process_batch_images_task, subject_id, file_paths)
        return Response({"message": "Batch processing started.", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)

import base64
import numpy as np
from django.utils import timezone
from .models import AttendanceSession, Attendance

# Global cache for face encodings
_FACE_ENCODINGS_CACHE = None

def invalidate_face_encodings_cache():
    """Call this after new face registrations to force cache rebuild."""
    global _FACE_ENCODINGS_CACHE
    _FACE_ENCODINGS_CACHE = None

def get_face_encodings_cache():
    global _FACE_ENCODINGS_CACHE
    if _FACE_ENCODINGS_CACHE is None:
        from apps.accounts.models import FaceSample, Student
        cache = []
        # Primary source: FaceSample table
        samples = FaceSample.objects.select_related('student__user').all()
        seen_student_ids = set()
        for s in samples:
            if s.face_encoding:
                cache.append((np.array(s.face_encoding), s.student_id, s.student.user.get_full_name()))
                seen_student_ids.add(s.student_id)
        # Fallback: legacy Student.face_encoding for students without FaceSamples
        legacy_students = Student.objects.filter(
            face_encoding__isnull=False
        ).exclude(id__in=seen_student_ids).select_related('user')
        for st in legacy_students:
            cache.append((np.array(st.face_encoding), st.id, st.user.get_full_name()))
        _FACE_ENCODINGS_CACHE = cache
    return _FACE_ENCODINGS_CACHE


class AttendanceSessionStartView(APIView):
    """Start a live attendance session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not (request.user.is_superuser or request.user.is_faculty):
            return Response({"error": "Unauthorized"}, status=403)
            
        subject_id = request.data.get("subject_id")
        if not subject_id:
            return Response({"error": "subject_id required"}, status=400)
            
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({"error": "Subject not found"}, status=404)
            
        # Clear cache on session start to pick up new registrations
        global _FACE_ENCODINGS_CACHE
        _FACE_ENCODINGS_CACHE = None
        get_face_encodings_cache()
            
        faculty = None
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
        session = AttendanceSession.objects.create(
            subject=subject,
            faculty=faculty,
        )
        
        return Response({"message": "Session started", "session_id": session.id})


class AttendanceSessionEndView(APIView):
    """End a live attendance session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        if not (request.user.is_superuser or request.user.is_faculty):
            return Response({"error": "Unauthorized"}, status=403)
            
        try:
            session = AttendanceSession.objects.get(id=session_id)
            session.status = AttendanceSession.Status.COMPLETED
            session.end_time = timezone.now()
            session.save()
            return Response({"message": "Session ended"})
        except AttendanceSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)


class AttendanceSessionProcessFrameView(APIView):
    """Process a base64 video frame for a live session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        if not (request.user.is_superuser or request.user.is_faculty):
            return Response({"error": "Unauthorized"}, status=403)
            
        try:
            session = AttendanceSession.objects.get(id=session_id, status=AttendanceSession.Status.ACTIVE)
        except AttendanceSession.DoesNotExist:
            return Response({"error": "Active session not found"}, status=404)
            
        frame_data = request.data.get("frame")
        if not frame_data:
            return Response({"error": "No frame provided"}, status=400)
            
        try:
            import cv2
            import face_recognition
            
            # Decode base64 image
            if "," in frame_data:
                frame_data = frame_data.split(",")[1]
            image_bytes = base64.b64decode(frame_data)
            jpg_as_np = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(jpg_as_np, flags=1)
            
            if img is None:
                return Response({"error": "Invalid image"}, status=400)
                
            # Resize for faster processing
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(imgS)
            face_encodings = face_recognition.face_encodings(imgS, face_locations)
            
            cache = get_face_encodings_cache()
            if not cache:
                return Response({"error": "No registered faces in database"}, status=400)
                
            known_encodings = [item[0] for item in cache]
            known_student_ids = [item[1] for item in cache]
            known_names = [item[2] for item in cache]
            
            recognized_students = []
            unknown_faces = 0
            
            tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.6)
            margin = 0.05
            
            for encodeFace, faceLoc in zip(face_encodings, face_locations):
                faceDis = face_recognition.face_distance(known_encodings, encodeFace)
                if len(faceDis) == 0:
                    continue
                    
                # Find best and second best match
                sorted_indices = np.argsort(faceDis)
                best_idx = sorted_indices[0]
                best_dist = faceDis[best_idx]
                
                if len(sorted_indices) > 1:
                    second_best_dist = faceDis[sorted_indices[1]]
                else:
                    second_best_dist = 1.0
                
                # Check threshold and margin
                if best_dist <= tolerance and (second_best_dist - best_dist) >= margin:
                    student_id = known_student_ids[best_idx]
                    student_name = known_names[best_idx]
                    
                    # Mark attendance idempotently
                    att, created = Attendance.objects.get_or_create(
                        student_id=student_id,
                        subject=session.subject,
                        date=date.today(),
                        defaults={
                            "session": session,
                            "status": Attendance.Status.PRESENT,
                            "method": Attendance.Method.FACE_RECOGNITION,
                            "confidence": best_dist,
                            "marked_by": request.user
                        }
                    )
                    
                    # Return coordinates (scaled back up)
                    y1, x2, y2, x1 = faceLoc
                    recognized_students.append({
                        "name": student_name,
                        "student_id": student_id,
                        "box": [y1*4, x2*4, y2*4, x1*4],
                        "confidence": best_dist
                    })
                else:
                    unknown_faces += 1
                    
            return Response({
                "recognized": recognized_students,
                "unknown_count": unknown_faces
            })
            
        except ImportError:
            return Response({"error": "Local face recognition not installed"}, status=501)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AttendanceRiskView(APIView):
    """Predicts absenteeism risk for a student in a specific subject (Phase 13.1)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, student_id, subject_id):
        import sys
        import os
        from django.conf import settings
        sys.path.append(os.path.join(settings.BASE_DIR, 'ml_engine'))
        try:
            from ml_engine.predictive_models import predict_absenteeism_risk
        except ImportError as e:
            return Response({"error": f"ML Engine unavailable: {e}"}, status=503)
            
        # Ensure student is either checking their own risk, or admin/faculty
        if request.user.is_student and request.user.student_profile.id != int(student_id):
            return Response({"error": "Cannot view risk profile of other students."}, status=403)
            
        try:
            risk_data = predict_absenteeism_risk(int(student_id), int(subject_id))
            return Response(risk_data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AttendanceAlertsDispatchView(APIView):
    """Triggers the async background task to evaluate all students and dispatch warnings (Phase 13.2)."""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        from django_q.tasks import async_task
        from .tasks import dispatch_absenteeism_alerts_task
        
        task_id = async_task(dispatch_absenteeism_alerts_task)
        return Response({
            "message": "Background alerting engine triggered successfully.",
            "task_id": task_id
        }, status=status.HTTP_202_ACCEPTED)

class AttendanceRiskAssessmentListView(APIView):
    """Returns a list of students currently at risk across all subjects."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        import sys
        import os
        from django.conf import settings
        if os.path.join(settings.BASE_DIR, 'ml_engine') not in sys.path:
            sys.path.append(os.path.join(settings.BASE_DIR, 'ml_engine'))
        try:
            from ml_engine.predictive_models import predict_absenteeism_risk
        except ImportError as e:
            return Response({"error": f"ML Engine unavailable: {e}"}, status=503)

        # Get all distinct student/subject pairs
        pairs = Attendance.objects.values_list('student_id', 'student__user__first_name', 'student__user__last_name', 'student__enrollment_number', 'subject_id', 'subject__name').distinct()
        
        at_risk_list = []
        for student_id, first_name, last_name, enrollment, subject_id, subject_name in pairs:
            try:
                risk_data = predict_absenteeism_risk(student_id, subject_id)
                if risk_data.get("is_at_risk"):
                    at_risk_list.append({
                        "student_id": student_id,
                        "student_name": f"{first_name} {last_name}",
                        "enrollment_number": enrollment,
                        "subject_id": subject_id,
                        "subject_name": subject_name,
                        "current_pct": risk_data.get("current_pct"),
                        "risk_probability": risk_data.get("risk_probability")
                    })
            except Exception:
                continue

        return Response(at_risk_list, status=200)

class AttendanceForecastView(APIView):
    """Predicts final CGPA based on current attendance and past academic performance (Phase 14.3)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        import sys
        import os
        from django.conf import settings
        sys.path.append(os.path.join(settings.BASE_DIR, 'ml_engine'))
        try:
            from ml_engine.predictive_models import predict_cgpa_forecast
        except ImportError as e:
            return Response({"error": f"ML Engine unavailable: {e}"}, status=503)
            
        if request.user.is_student and request.user.student_profile.id != int(student_id):
            return Response({"error": "Cannot view forecast of other students."}, status=403)
            
        try:
            student = Student.objects.get(id=student_id)
            forecast = predict_cgpa_forecast(student)
            if forecast is None:
                return Response({"error": "Model prediction failed."}, status=500)
            return Response({"forecasted_cgpa": forecast}, status=200)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

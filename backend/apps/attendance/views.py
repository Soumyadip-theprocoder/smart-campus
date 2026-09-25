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
from apps.accounts.models import Student
from pgvector.django import L2Distance

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
            
        tolerance = getattr(settings, "FACE_RECOGNITION_TOLERANCE", 0.5)
        best_match = (
            Student.objects.filter(face_encoding__isnull=False)
            .annotate(distance=L2Distance("face_encoding", encoding_list))
            .filter(distance__lte=tolerance)
            .order_by("distance")
            .first()
        )
        
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

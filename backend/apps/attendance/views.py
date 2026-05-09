"""
Views for the Attendance app.
"""
from datetime import date
from django.db.models import Count, Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Student
from apps.scheduler.models import Subject
from .models import Attendance
from .serializers import (
    AttendanceSerializer, MarkAttendanceSerializer,
    AttendanceReportSerializer,
)


class AttendanceListView(generics.ListAPIView):
    """List attendance records with filtering."""
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'student__user', 'subject',
        )
        user = self.request.user

        # Students can only see their own records
        if user.is_student:
            qs = qs.filter(student=user.student_profile)

        # Optional filters
        student_id = self.request.query_params.get('student_id')
        subject_id = self.request.query_params.get('subject_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if student_id:
            qs = qs.filter(student_id=student_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        return qs


class MarkAttendanceView(APIView):
    """Mark attendance for a student (from face recognition or manual)."""
    permission_classes = [permissions.AllowAny]  # Face recognition system calls this

    def post(self, request):
        serializer = MarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            student = Student.objects.get(
                enrollment_number=serializer.validated_data['enrollment_number']
            )
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        attendance, created = Attendance.objects.get_or_create(
            student=student,
            subject_id=serializer.validated_data['subject_id'],
            date=serializer.validated_data['date'],
            defaults={
                'status': Attendance.Status.PRESENT,
                'method': serializer.validated_data.get(
                    'method', Attendance.Method.FACE_RECOGNITION
                ),
            },
        )

        if not created:
            return Response(
                {'message': 'Attendance already marked for today.'},
                status=status.HTTP_200_OK,
            )

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED,
        )


class AttendanceReportView(APIView):
    """Get attendance report for a specific student."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # If requesting user is a student, they can only see their own report
        if request.user.is_student:
            if request.user.student_profile.id != student_id:
                return Response(
                    {'error': 'Access denied.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Get all subjects the student has attendance records for
        subjects = Subject.objects.filter(
            attendance_records__student=student
        ).distinct()

        report = []
        for subject in subjects:
            total = Attendance.objects.filter(
                student=student, subject=subject
            ).count()
            attended = Attendance.objects.filter(
                student=student, subject=subject,
                status=Attendance.Status.PRESENT,
            ).count()

            report.append({
                'subject_code': subject.code,
                'subject_name': subject.name,
                'total_classes': total,
                'classes_attended': attended,
                'percentage': round((attended / total * 100), 2) if total > 0 else 0,
            })

        return Response(report)


class AttendanceSummaryView(APIView):
    """Get aggregate attendance summary (for admin dashboard)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        total_students = Student.objects.count()
        today_present = Attendance.objects.filter(
            date=today, status=Attendance.Status.PRESENT
        ).values('student').distinct().count()

        total_records = Attendance.objects.count()
        present_records = Attendance.objects.filter(
            status=Attendance.Status.PRESENT
        ).count()

        return Response({
            'total_students': total_students,
            'today_present': today_present,
            'today_absent': total_students - today_present,
            'overall_attendance_rate': round(
                (present_records / total_records * 100), 2
            ) if total_records > 0 else 0,
        })

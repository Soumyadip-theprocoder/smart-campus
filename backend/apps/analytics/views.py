from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Q, Avg
from apps.accounts.models import Student, Faculty
from apps.attendance.models import Attendance
from apps.scheduler.models import Subject, TimetableEntry
from datetime import date

class AnalyticsOverviewView(APIView):
    """Overview statistics for Admin Dashboard."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        
        total_students = Student.objects.count()
        total_faculty = Faculty.objects.count()
        
        # Today's active classes
        # Assuming we can find active classes by seeing which timetable entries match today's weekday
        # Django weekday: 1(Sunday) to 7(Saturday), but TimeSlot uses string days. Let's just count unique subjects that have attendance today for simplicity.
        today_active_classes = Attendance.objects.filter(date=today).values('subject_id').distinct().count()
        
        # Overall campus attendance
        total_records = Attendance.objects.count()
        present_records = Attendance.objects.filter(status=Attendance.Status.PRESENT).count()
        
        overall_attendance = 0
        if total_records > 0:
            overall_attendance = round((present_records / total_records) * 100, 1)
            
        return Response({
            "total_students": total_students,
            "total_faculty": total_faculty,
            "today_active_classes": today_active_classes,
            "overall_attendance": overall_attendance,
        })


class DepartmentTrendsView(APIView):
    """Average attendance grouped by department."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # We need to calculate attendance percentage for each department.
        # Students belong to departments.
        departments = Student.objects.values('department').distinct()
        
        trends = []
        for d in departments:
            dept = d['department']
            students_in_dept = Student.objects.filter(department=dept)
            
            total = Attendance.objects.filter(student__in=students_in_dept).count()
            present = Attendance.objects.filter(student__in=students_in_dept, status=Attendance.Status.PRESENT).count()
            
            percentage = 0
            if total > 0:
                percentage = round((present / total) * 100, 1)
                
            trends.append({
                "department": dept,
                "percentage": percentage
            })
            
        return Response(trends)


class SubjectAveragesView(APIView):
    """Average attendance per subject."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subjects = Subject.objects.all()
        averages = []
        
        for subject in subjects:
            total = Attendance.objects.filter(subject=subject).count()
            present = Attendance.objects.filter(subject=subject, status=Attendance.Status.PRESENT).count()
            
            percentage = 0
            if total > 0:
                percentage = round((present / total) * 100, 1)
                
            averages.append({
                "subject_code": subject.code,
                "subject_name": subject.name,
                "percentage": percentage
            })
            
        # Sort by percentage descending
        averages.sort(key=lambda x: x['percentage'], reverse=True)
        
        return Response(averages)

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
        departments = Student.objects.values('department', 'department__name').distinct()
        
        trends = []
        for d in departments:
            dept_id = d['department']
            dept_name = d.get('department__name', f"Dept {dept_id}")
            students_in_dept = Student.objects.filter(department=dept_id)
            
            total = Attendance.objects.filter(student__in=students_in_dept).count()
            present = Attendance.objects.filter(student__in=students_in_dept, status=Attendance.Status.PRESENT).count()
            
            percentage = 0
            if total > 0:
                percentage = round((present / total) * 100, 1)
                
            trends.append({
                "department": dept_name,
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

class StudentClustersView(APIView):
    """Gets behavioral profiles (clusters) for all students (Phase 14.3)."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        import sys
        import os
        from django.conf import settings
        sys.path.append(os.path.join(settings.BASE_DIR, 'ml_engine'))
        try:
            from ml_engine.predictive_models import get_student_cluster
        except ImportError as e:
            return Response({"error": f"ML Engine unavailable: {e}"}, status=503)
            
        students = Student.objects.select_related('user').all()
        clusters = []
        for student in students:
            try:
                cluster_data = get_student_cluster(student)
                if cluster_data:
                    clusters.append({
                        "student_id": student.id,
                        "enrollment_number": student.enrollment_number,
                        "name": student.user.get_full_name(),
                        "cluster_id": cluster_data["cluster_id"],
                        "profile_name": cluster_data["profile_name"]
                    })
            except Exception:
                continue
                
        return Response(clusters, status=200)

class DailyAttendanceTrendsView(APIView):
    """Overall campus attendance trend over the last 14 days."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=14)
        
        dates = Attendance.objects.filter(date__gte=start_date, date__lte=end_date).values('date').distinct().order_by('date')
        
        trends = []
        for d in dates:
            d_val = d['date']
            total = Attendance.objects.filter(date=d_val).count()
            present = Attendance.objects.filter(date=d_val, status=Attendance.Status.PRESENT).count()
            
            percentage = 0
            if total > 0:
                percentage = round((present / total) * 100, 1)
            
            trends.append({
                "date": d_val.strftime("%b %d"),
                "percentage": percentage
            })
            
        return Response(trends)

class DayOfWeekTrendsView(APIView):
    """Average attendance grouped by day of the week."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        # Django ExtractIsoWeekDay could be used, but since we have a small dataset, we can compute it manually or use ExtractWeekDay
        from django.db.models.functions import ExtractWeekDay
        
        records = Attendance.objects.annotate(weekday=ExtractWeekDay('date')).values('weekday').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status=Attendance.Status.PRESENT))
        ).order_by('weekday')
        
        # ExtractWeekDay returns 1 (Sunday) to 7 (Saturday)
        day_map = {2: 'Mon', 3: 'Tue', 4: 'Wed', 5: 'Thu', 6: 'Fri', 7: 'Sat', 1: 'Sun'}
        
        trends = []
        for r in records:
            day_num = r['weekday']
            total = r['total']
            present = r['present']
            
            if total > 0:
                percentage = round((present / total) * 100, 1)
                trends.append({
                    "day": day_map.get(day_num, 'Unknown'),
                    "percentage": percentage
                })
                
        # Sort by normal week order
        sort_order = {d: i for i, d in enumerate(days)}
        trends.sort(key=lambda x: sort_order.get(x['day'], 99))
        
        return Response(trends)

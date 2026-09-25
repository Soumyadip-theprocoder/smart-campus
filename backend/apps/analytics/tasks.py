from django.contrib.auth import get_user_model
from apps.accounts.models import Student
from apps.attendance.models import Attendance
from apps.communication.models import Notice
from datetime import date

User = get_user_model()

def flag_attendance_shortages():
    """
    Cron job task to flag students falling below 75% attendance.
    Runs daily at midnight.
    """
    students = Student.objects.all()
    shortage_list = []
    
    for student in students:
        total = Attendance.objects.filter(student=student).count()
        if total == 0:
            continue
            
        present = Attendance.objects.filter(student=student, status=Attendance.Status.PRESENT).count()
        percentage = (present / total) * 100
        
        if percentage < 75.0:
            shortage_list.append(f"{student.user.get_full_name()} ({student.enrollment_number}): {percentage:.1f}%")
            
    if shortage_list:
        # Create a single notice for faculty
        admin_user = User.objects.filter(is_superuser=True).first()
        content = "The following students have fallen below the 75% attendance threshold:\n\n" + "\n".join(shortage_list)
        
        # Avoid creating duplicates on the same day
        today_notice = Notice.objects.filter(
            title="Automated Attendance Alert", 
            created_at__date=date.today()
        ).exists()
        
        if not today_notice and admin_user:
            Notice.objects.create(
                title="Automated Attendance Alert",
                content=content,
                priority=Notice.Priority.URGENT,
                posted_by=admin_user,
                target_audience="faculty"
            )

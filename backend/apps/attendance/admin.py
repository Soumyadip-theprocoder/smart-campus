"""
Admin registration for Attendance models.
"""
from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject', 'date', 'status', 'method', 'marked_at',
    ]
    list_filter = ['status', 'method', 'date', 'subject']
    search_fields = [
        'student__enrollment_number',
        'student__user__first_name',
        'student__user__last_name',
    ]
    date_hierarchy = 'date'

"""
URL patterns for the Attendance app.
"""
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='list'),
    path('mark/', views.MarkAttendanceView.as_view(), name='mark'),
    path('report/<int:student_id>/', views.AttendanceReportView.as_view(), name='report'),
    path('summary/', views.AttendanceSummaryView.as_view(), name='summary'),
]

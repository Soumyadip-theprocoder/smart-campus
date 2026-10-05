from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("department-trends/", views.DepartmentTrendsView.as_view(), name="department-trends"),
    path("subject-averages/", views.SubjectAveragesView.as_view(), name="subject-averages"),
    path("overview/", views.AnalyticsOverviewView.as_view(), name="overview"),
    path("student-clusters/", views.StudentClustersView.as_view(), name="student-clusters"),
    path("daily-trends/", views.DailyAttendanceTrendsView.as_view(), name="daily-trends"),
    path("day-of-week-trends/", views.DayOfWeekTrendsView.as_view(), name="day-of-week-trends"),
]

from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("department-trends/", views.DepartmentTrendsView.as_view(), name="department-trends"),
    path("subject-averages/", views.SubjectAveragesView.as_view(), name="subject-averages"),
    path("overview/", views.AnalyticsOverviewView.as_view(), name="overview"),
]

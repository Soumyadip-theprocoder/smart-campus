"""
URL patterns for the Attendance app.
"""

from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.AttendanceListView.as_view(), name="list"),
    path("mark/", views.MarkAttendanceView.as_view(), name="mark"),
    path("generate-qr-token/", views.GenerateQRTokenView.as_view(), name="generate-qr-token"),
    path("recognize/", views.TriggerFaceRecognitionView.as_view(), name="recognize"),
    path(
        "report/<int:student_id>/", views.AttendanceReportView.as_view(), name="report"
    ),
    path("summary/", views.AttendanceSummaryView.as_view(), name="summary"),
    path(
        "export/admin/csv/", views.AdminCSVExportView.as_view(), name="export-admin-csv"
    ),
    path(
        "export/student/pdf/<int:student_id>/",
        views.StudentPDFExportView.as_view(),
        name="export-student-pdf",
    ),
]

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
    path("sessions/start/", views.AttendanceSessionStartView.as_view(), name="session-start"),
    path("sessions/<int:session_id>/process-frame/", views.AttendanceSessionProcessFrameView.as_view(), name="session-process-frame"),
    path("sessions/<int:session_id>/end/", views.AttendanceSessionEndView.as_view(), name="session-end"),
    path("batch-upload/", views.BatchUploadView.as_view(), name="batch-upload"),
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
    path(
        "risk/<int:student_id>/<int:subject_id>/",
        views.AttendanceRiskView.as_view(),
        name="attendance-risk",
    ),
    path(
        "alerts/dispatch/",
        views.AttendanceAlertsDispatchView.as_view(),
        name="alerts-dispatch",
    ),
    path(
        "risk-assessment/",
        views.AttendanceRiskAssessmentListView.as_view(),
        name="risk-assessment-list",
    ),
    path(
        "forecast/<int:student_id>/",
        views.AttendanceForecastView.as_view(),
        name="attendance-forecast",
    ),
]

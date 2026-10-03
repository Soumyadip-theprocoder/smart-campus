"""
URL patterns for the Scheduler app.
"""

from django.urls import path

from . import views

app_name = "scheduler"

urlpatterns = [
    path("departments/", views.DepartmentListView.as_view(), name="department-list"),
    path("departments/<int:pk>/", views.DepartmentDetailView.as_view(), name="department-detail"),
    path("amenities/", views.AmenityListView.as_view(), name="amenity-list"),
    path("amenities/<int:pk>/", views.AmenityDetailView.as_view(), name="amenity-detail"),
    path("resources/", views.ResourceListView.as_view(), name="resource-list"),
    path("resources/<int:pk>/", views.ResourceDetailView.as_view(), name="resource-detail"),
    path("subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path(
        "subjects/<int:pk>/", views.SubjectDetailView.as_view(), name="subject-detail"
    ),
    path("rooms/", views.RoomListView.as_view(), name="room-list"),
    path("rooms/<int:pk>/", views.RoomDetailView.as_view(), name="room-detail"),
    path("timeslots/", views.TimeSlotListView.as_view(), name="timeslot-list"),
    path(
        "timeslots/<int:pk>/",
        views.TimeSlotDetailView.as_view(),
        name="timeslot-detail",
    ),
    path("timetable/", views.TimetableView.as_view(), name="timetable"),
    path("timetable/<int:pk>/", views.TimetableEntryDetailView.as_view(), name="timetable-entry-detail"),
    path("timetable/<int:entry_id>/smart-swaps/", views.FindSmartSwapView.as_view(), name="smart-swaps"),
    path("generate/", views.GenerateTimetableView.as_view(), name="generate"),
    path(
        "task-status/<str:task_id>/", views.TaskStatusView.as_view(), name="task-status"
    ),
    path("settings/", views.InstitutionSettingsView.as_view(), name="institution-settings"),
    path("versions/", views.TimetableVersionListView.as_view(), name="version-list"),
    path("versions/<int:pk>/", views.TimetableVersionDetailView.as_view(), name="version-detail"),
    path("absences/", views.AbsenceReportListView.as_view(), name="absence-list"),
    path("absences/<int:pk>/", views.AbsenceReportDetailView.as_view(), name="absence-detail"),
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"),
    path("swaps/", views.TimetableSwapRequestListView.as_view(), name="swap-list"),
    path("swaps/<int:pk>/", views.TimetableSwapRequestDetailView.as_view(), name="swap-detail"),
    path("blackout-dates/", views.BlackoutDateListView.as_view(), name="blackout-date-list"),
    path("blackout-dates/<int:pk>/", views.BlackoutDateDetailView.as_view(), name="blackout-date-detail"),
    path("ical/<int:user_id>/", views.ICalFeedView.as_view(), name="ical-feed"),
    path("analytics/accreditation/", views.AccreditationAnalyticsView.as_view(), name="analytics-accreditation"),
    path("analytics/forecast/", views.ForecastingAnalyticsView.as_view(), name="analytics-forecast"),
]

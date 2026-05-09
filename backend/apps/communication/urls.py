"""
URL patterns for the Communication app.
"""
from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('notices/', views.NoticeListView.as_view(), name='notice-list'),
    path('notices/create/', views.CreateNoticeView.as_view(), name='notice-create'),
    path('alerts/attendance/', views.SendAttendanceAlertsView.as_view(), name='attendance-alerts'),
]

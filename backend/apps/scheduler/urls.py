"""
URL patterns for the Scheduler app.
"""
from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('timeslots/', views.TimeSlotListView.as_view(), name='timeslot-list'),
    path('timeslots/<int:pk>/', views.TimeSlotDetailView.as_view(), name='timeslot-detail'),
    path('timetable/', views.TimetableView.as_view(), name='timetable'),
    path('generate/', views.GenerateTimetableView.as_view(), name='generate'),
]

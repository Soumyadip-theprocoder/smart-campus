"""
URL patterns for the Scheduler app.
"""
from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='subject-list'),
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('timeslots/', views.TimeSlotListView.as_view(), name='timeslot-list'),
    path('timetable/', views.TimetableView.as_view(), name='timetable'),
    path('generate/', views.GenerateTimetableView.as_view(), name='generate'),
]

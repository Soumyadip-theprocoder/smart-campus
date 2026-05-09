"""
Admin registration for Scheduler models.
"""
from django.contrib import admin
from .models import Subject, Room, TimeSlot, TimetableEntry


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'faculty', 'credits', 'required_capacity', 'sessions_per_week']
    list_filter = ['credits', 'faculty__department']
    search_fields = ['code', 'name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'capacity', 'building', 'room_type']
    list_filter = ['building', 'room_type']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['day', 'start_time', 'end_time']
    list_filter = ['day']


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'room', 'time_slot']
    list_filter = ['time_slot__day', 'room']

"""
Models for the Scheduler app.
Subject, Room, and TimetableEntry.
"""
from django.db import models
from apps.accounts.models import Faculty


class Subject(models.Model):
    """Academic subject/course."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='subjects',
    )
    credits = models.PositiveIntegerField(default=3)
    required_capacity = models.PositiveIntegerField(
        default=30,
        help_text='Minimum room capacity needed for this subject',
    )
    sessions_per_week = models.PositiveIntegerField(
        default=3,
        help_text='Number of sessions per week',
    )

    class Meta:
        db_table = 'subjects'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"


class Room(models.Model):
    """Physical classroom/lab."""

    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    building = models.CharField(max_length=100, default='Main Building')
    room_type = models.CharField(
        max_length=20,
        choices=[
            ('lecture', 'Lecture Hall'),
            ('lab', 'Laboratory'),
            ('seminar', 'Seminar Room'),
        ],
        default='lecture',
    )

    class Meta:
        db_table = 'rooms'
        ordering = ['building', 'room_number']

    def __str__(self):
        return f"{self.room_number} ({self.building}, cap: {self.capacity})"


class TimeSlot(models.Model):
    """Predefined time slots for scheduling."""

    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    ]

    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = 'time_slots'
        ordering = ['day', 'start_time']
        unique_together = ['day', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class TimetableEntry(models.Model):
    """A scheduled class session — one subject assigned to a time slot and room."""

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='timetable_entries',
    )

    class Meta:
        db_table = 'timetable_entries'
        ordering = ['time_slot__day', 'time_slot__start_time']
        # Core constraints: no double-booking rooms or faculty
        unique_together = [
            ('room', 'time_slot'),        # No two classes in same room at same time
        ]

    def __str__(self):
        return (
            f"{self.subject.code} | {self.room.room_number} | "
            f"{self.time_slot}"
        )

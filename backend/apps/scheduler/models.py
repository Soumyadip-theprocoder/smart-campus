"""
Models for the Scheduler app.
Subject, Room, and TimetableEntry.
"""

from apps.accounts.models import Faculty
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Amenity(models.Model):
    """Physical characteristics of a room or needs of a subject."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "amenities"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Resource(models.Model):
    """Moveable physical equipment (e.g., Projector A)."""
    name = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "resources"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    """Academic Department for scoping generation and settings."""
    dept_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Standardized Department ID, e.g. DEP-0001"
    )
    name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField(null=True, blank=True, help_text="Override global start time")
    end_time = models.TimeField(null=True, blank=True, help_text="Override global end time")
    default_breaks = models.JSONField(
        default=list,
        blank=True,
        help_text='List of break times like ["13:00"]'
    )
    no_of_years = models.PositiveIntegerField(
        default=4, 
        help_text="Number of years for the programs in this department"
    )
    program_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., B.Sc, M.Sc, B.Tech, M.Tech"
    )
    core_department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., Civil, Mechanical, Computer Science"
    )
    hod = models.ForeignKey(
        'accounts.Faculty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        help_text="Head of Department"
    )

    class Meta:
        db_table = "departments"
        ordering = ["dept_id", "name"]

    def save(self, *args, **kwargs):
        if not self.dept_id:
            import re
            existing_ids = Department.objects.exclude(dept_id__isnull=True).values_list("dept_id", flat=True)
            max_num = 0
            for did in existing_ids:
                m = re.match(r"^DEP-(\d+)$", str(did))
                if m:
                    max_num = max(max_num, int(m.group(1)))
            self.dept_id = f"DEP-{(max_num + 1):04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        if self.dept_id:
            return f"[{self.dept_id}] {self.name}"
        return self.name



class Subject(models.Model):
    """Academic subject/course."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
    )
    semester = models.PositiveIntegerField(
        default=1,
        null=True,
        blank=True,
        help_text="Target semester (e.g. 1, 2, ...)",
    )
    credits = models.FloatField(default=3.0)
    required_capacity = models.PositiveIntegerField(
        default=30,
        help_text="Minimum room capacity needed for this subject",
    )
    sessions_per_week = models.PositiveIntegerField(
        default=3,
        help_text="Number of sessions per week",
    )
    subject_type = models.CharField(
        max_length=20,
        choices=[
            ("lecture", "Lecture"),
            ("lab", "Laboratory"),
            ("seminar", "Seminar"),
        ],
        default="lecture",
    )
    description = models.TextField(blank=True, null=True)
    color_code = models.CharField(
        max_length=7,
        default="#1e293b",
        help_text="Hex color code for timetable display",
    )
    departments = models.ManyToManyField(
        Department,
        related_name="subjects",
        blank=True,
        help_text="Departments this subject belongs to",
    )
    is_elective = models.BooleanField(
        default=False,
        help_text="True if this is a shared elective across departments",
    )
    elective_group = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        db_index=True,
        help_text="Group identifier for elective choices where students must choose one",
    )
    amenities = models.ManyToManyField(
        Amenity,
        related_name="required_by_subjects",
        blank=True,
        help_text="Amenities required by this subject",
    )
    resources = models.ManyToManyField(
        Resource,
        related_name="required_by_subjects",
        blank=True,
        help_text="Movable resources (from pools) required by this subject",
    )
    required_tas = models.PositiveIntegerField(
        default=0,
        help_text="Number of TAs required for this class",
    )

    class Meta:
        db_table = "subjects"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class StudentElectiveEnrollment(models.Model):
    """Enforces that a student is enrolled in exactly one elective per group."""
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='elective_enrollments',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrolled_students',
    )
    elective_group = models.CharField(
        max_length=150,
        db_index=True,
        help_text="Group identifier matching Subject.elective_group",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "student_elective_enrollments"
        unique_together = ("student", "elective_group")
        ordering = ["elective_group", "enrolled_at"]

    def __str__(self):
        return f"{self.student.enrollment_number} -> {self.subject.code} ({self.elective_group})"


class Room(models.Model):
    """Physical classroom/lab."""

    room_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    building = models.CharField(max_length=100, default="Main Building")
    room_type = models.CharField(
        max_length=20,
        choices=[
            ("lecture", "Lecture Hall"),
            ("lab", "Laboratory"),
            ("seminar", "Seminar Room"),
        ],
        default="lecture",
    )
    equipment = models.JSONField(
        default=list,
        blank=True,
        help_text='List of equipment like ["Projector", "Whiteboard"]',
    )
    departments = models.ManyToManyField(
        Department,
        related_name="rooms",
        blank=True,
        help_text="Departments that can use this room",
    )
    amenities = models.ManyToManyField(
        Amenity,
        related_name="rooms",
        blank=True,
        help_text="Amenities present in this room",
    )

    class Meta:
        db_table = "rooms"
        ordering = ["building", "room_number"]

    def __str__(self):
        return f"{self.room_number} ({self.building}, cap: {self.capacity})"


class TimeSlot(models.Model):
    """Predefined time slots for scheduling."""

    DAY_CHOICES = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
    ]

    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "time_slots"
        ordering = ["day", "start_time"]
        unique_together = ["day", "start_time", "end_time"]

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class TimetableVersion(models.Model):
    """Sandbox version of a timetable."""
    
    name = models.CharField(max_length=100)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "timetable_versions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} {'(Published)' if self.is_published else '(Draft)'}"


class TimetableEntry(models.Model):
    """A scheduled class session — one subject assigned to a time slot and room."""

    version = models.ForeignKey(
        TimetableVersion,
        on_delete=models.CASCADE,
        related_name="entries",
        null=True,
        blank=True
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
        null=True,
        blank=True,
    )
    event_title = models.CharField(max_length=200, blank=True, null=True)
    event_color = models.CharField(max_length=7, blank=True, null=True)
    event_type = models.CharField(max_length=50, blank=True, null=True, default="class")
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="custom_entries",
        null=True,
        blank=True
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="If true, the CSP solver will not modify this entry.",
    )
    teaching_assistants = models.ManyToManyField(
        'accounts.Student',
        blank=True,
        related_name="ta_assignments",
    )

    class Meta:
        db_table = "timetable_entries"
        ordering = ["time_slot__day", "time_slot__start_time"]
        # Core constraints: no double-booking rooms or faculty per version
        unique_together = [
            ("version", "room", "time_slot"),  # No two classes in same room at same time in a single version
        ]

    def __str__(self):
        title = self.subject.code if self.subject else (self.event_title or "Custom Event")
        return f"{title} | {self.room.room_number} | {self.time_slot} | {self.version}"


class InstitutionSettings(models.Model):
    """Global settings for the institution (timetable bounds, etc.)."""

    start_time = models.TimeField(default="09:00")
    end_time = models.TimeField(default="18:00")
    default_breaks = models.JSONField(
        default=list,
        help_text='List of break times like ["13:00"]',
    )

    class Meta:
        db_table = "institution_settings"

    def __str__(self):
        return f"Institution Settings (Active: {self.start_time} - {self.end_time})"

class AbsenceReport(models.Model):
    """Report filed by a faculty for being absent on a certain date."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="absences")
    date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    substitute = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="substitutions")
    timetable_entry = models.ForeignKey(TimetableEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name="absences")

    class Meta:
        db_table = "absence_reports"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.faculty} - {self.date} ({self.status})"

class Notification(models.Model):
    """System push alerts/notifications."""

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.recipient.email}: {self.message[:20]}..."

class TimetableSwapRequest(models.Model):
    """Request for swapping a class to a different time slot or trading with another class."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    requester = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="swap_requests")
    target_entry = models.ForeignKey(TimetableEntry, on_delete=models.CASCADE, related_name="swap_targets")
    requested_time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="swap_slots")
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "timetable_swap_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Swap Request: {self.target_entry.subject.code} to {self.requested_time_slot} ({self.status})"

class BlackoutDate(models.Model):
    """Specific dates where classes should not be scheduled (e.g. holidays)."""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=200)
    is_global = models.BooleanField(default=True)
    
    class Meta:
        db_table = "blackout_dates"
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} - {self.reason}"


class SchedulerTaskProgress(models.Model):
    """Real-time progress and dynamic ETA tracking for asynchronous timetable generation."""

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    task_id = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    scope_type = models.CharField(max_length=20, default="department")
    scope_label = models.CharField(max_length=150, blank=True, default="")
    total_waves = models.PositiveIntegerField(default=1)
    current_wave = models.PositiveIntegerField(default=0)
    current_wave_name = models.CharField(max_length=150, blank=True, default="")
    sessions_scheduled = models.PositiveIntegerField(default=0)
    percent = models.FloatField(default=0.0)
    elapsed_seconds = models.FloatField(default=0.0)
    eta_remaining_seconds = models.FloatField(default=0.0)
    start_time = models.FloatField(default=0.0)
    error = models.TextField(blank=True, default="")
    result_data = models.JSONField(blank=True, null=True)
    input_payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scheduler_task_progress"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} ({self.status}) - {self.percent:.1f}% ETA: {self.eta_remaining_seconds:.1f}s"


class SchedulerInputLog(models.Model):
    """Audit and debug log for all incoming frontend generation requests."""

    task_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    endpoint = models.CharField(max_length=60, default="generate")
    draft_name = models.CharField(max_length=150, blank=True, default="")
    scope_type = models.CharField(max_length=30, default="department")
    scope_label = models.CharField(max_length=150, blank=True, default="")
    department_id = models.IntegerField(null=True, blank=True)
    block_name = models.CharField(max_length=100, blank=True, default="")
    raw_payload = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)
    user_username = models.CharField(max_length=150, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "scheduler_input_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.scope_label} ({self.scope_type}) by {self.user_username or 'anonymous'}"

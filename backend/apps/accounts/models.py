"""
Models for the Accounts app.
Defines the custom User model with role-based access, plus
Student and Faculty profile models.
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from pgvector.django import HnswIndex, VectorField


class AcademicGroup(models.Model):
    """Flexible grouping for interdisciplinary classes or batches."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "academic_groups"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with role field for RBAC."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STUDENT = "student", "Student"
        FACULTY = "faculty", "Faculty"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["id"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_faculty(self):
        return self.role == self.Role.FACULTY


class Student(models.Model):
    """Student profile linked to User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    enrollment_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        'scheduler.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        help_text="Primary department",
    )
    groups = models.ManyToManyField(
        AcademicGroup,
        related_name="students",
        blank=True,
    )
    semester = models.PositiveIntegerField(default=1)
    face_encoding = VectorField(
        dimensions=128,
        blank=True,
        null=True,
        help_text="128-dimensional face encoding vector",
    )
    face_image = models.ImageField(
        upload_to="face_images/",
        blank=True,
        null=True,
    )
    accessibility_needs = models.JSONField(
        default=list,
        blank=True,
        help_text='List of needs like ["Wheelchair Access"]',
    )
    is_ta = models.BooleanField(
        default=False,
        help_text="Whether this student is also a Teaching Assistant",
    )
    ta_max_hours_per_week = models.PositiveIntegerField(
        default=10,
        help_text="Maximum hours per week the student can TA",
    )
    ta_qualified_subjects = models.ManyToManyField(
        'scheduler.Subject',
        blank=True,
        related_name='qualified_tas',
        help_text="Subjects this TA is qualified to teach",
    )

    class Meta:
        db_table = "students"
        ordering = ["enrollment_number"]
        indexes = [
            HnswIndex(
                name="student_face_hnsw_idx",
                fields=["face_encoding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            )
        ]

    def __str__(self):
        return f"{self.enrollment_number} — {self.user.get_full_name()}"


class Faculty(models.Model):
    """Faculty profile linked to User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="faculty_profile",
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        'scheduler.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculty_members",
        help_text="Primary department",
    )
    groups = models.ManyToManyField(
        AcademicGroup,
        related_name="faculty_members",
        blank=True,
    )
    designation = models.CharField(max_length=100, default="Assistant Professor")
    max_hours_per_week = models.PositiveIntegerField(default=20)
    availability = models.JSONField(
        blank=True, null=True, help_text="Per-day time slot availability preferences"
    )

    class Meta:
        db_table = "faculty"
        verbose_name_plural = "Faculty"
        ordering = ["employee_id"]
        indexes = [GinIndex(fields=["availability"], name="faculty_avail_gin_idx")]

    def __str__(self):
        return f"{self.employee_id} — {self.user.get_full_name()}"

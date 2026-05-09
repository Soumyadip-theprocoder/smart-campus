"""
Models for the Communication app.
Notices and alert tracking.
"""
from django.db import models
from django.conf import settings


class Notice(models.Model):
    """Campus notice / announcement."""

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    title = models.CharField(max_length=300)
    content = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notices',
    )
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All'),
            ('students', 'Students'),
            ('faculty', 'Faculty'),
        ],
        default='all',
    )
    email_sent = models.BooleanField(
        default=False,
        help_text='Whether notification emails have been dispatched',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notices'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

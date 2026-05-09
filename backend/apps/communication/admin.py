"""
Admin registration for Communication models.
"""
from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'posted_by', 'target_audience', 'email_sent', 'created_at']
    list_filter = ['priority', 'target_audience', 'email_sent']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'

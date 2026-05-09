"""
Serializers for the Communication app.
"""
from rest_framework import serializers
from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    """Serializer for Notice model."""
    posted_by_name = serializers.CharField(
        source='posted_by.get_full_name', read_only=True,
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True,
    )

    class Meta:
        model = Notice
        fields = [
            'id', 'title', 'content', 'priority', 'priority_display',
            'posted_by', 'posted_by_name', 'target_audience',
            'email_sent', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'posted_by', 'email_sent', 'created_at', 'updated_at']


class CreateNoticeSerializer(serializers.ModelSerializer):
    """Serializer for creating a notice with optional email dispatch."""
    send_email = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = Notice
        fields = [
            'title', 'content', 'priority', 'target_audience', 'send_email',
        ]

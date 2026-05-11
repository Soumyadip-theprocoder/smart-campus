"""
Views for the Communication app.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notice
from .serializers import NoticeSerializer, CreateNoticeSerializer
from .email_service import send_notice_email, send_attendance_alerts


class NoticeListView(generics.ListAPIView):
    """List all notices (newest first)."""
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notice.objects.select_related('posted_by').all()


class CreateNoticeView(APIView):
    """Create a new notice and optionally send email notifications."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateNoticeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        send_email = serializer.validated_data.pop('send_email', False)

        notice = Notice.objects.create(
            posted_by=request.user,
            **serializer.validated_data,
        )

        # Send email if requested (and priority is high/urgent)
        emails_sent = 0
        if send_email or notice.priority in ('high', 'urgent'):
            emails_sent = send_notice_email(notice)

        return Response({
            'notice': NoticeSerializer(notice).data,
            'emails_sent': emails_sent,
        }, status=status.HTTP_201_CREATED)


class DeleteNoticeView(generics.DestroyAPIView):
    """Delete a notice (admin only)."""
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notice.objects.all()
    lookup_field = 'pk'


class SendAttendanceAlertsView(APIView):
    """Trigger attendance shortage alerts (admin only)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        threshold = float(request.data.get('threshold', 75.0))
        emails_sent = send_attendance_alerts(threshold)

        return Response({
            'message': f'Sent {emails_sent} attendance alert emails.',
            'threshold': threshold,
        })

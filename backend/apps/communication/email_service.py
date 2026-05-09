"""
Email service for automated notifications.
Handles attendance alerts and notice emails via SMTP.
"""
import logging
from django.core.mail import send_mass_mail, send_mail
from django.conf import settings
from django.template.loader import render_to_string

from apps.accounts.models import User, Student
from apps.attendance.services import get_low_attendance_students

logger = logging.getLogger(__name__)


def send_notice_email(notice) -> int:
    """
    Send email notification for a new notice.
    Returns the number of emails sent.
    """
    # Determine recipients based on target audience
    if notice.target_audience == 'students':
        recipients = User.objects.filter(
            role=User.Role.STUDENT, is_active=True,
        ).values_list('email', flat=True)
    elif notice.target_audience == 'faculty':
        recipients = User.objects.filter(
            role=User.Role.FACULTY, is_active=True,
        ).values_list('email', flat=True)
    else:  # 'all'
        recipients = User.objects.filter(
            is_active=True,
        ).values_list('email', flat=True)

    if not recipients:
        return 0

    subject = f"[Smart Campus] [{notice.get_priority_display()}] {notice.title}"
    message = (
        f"Notice: {notice.title}\n"
        f"Priority: {notice.get_priority_display()}\n"
        f"Posted by: {notice.posted_by.get_full_name()}\n\n"
        f"{notice.content}\n\n"
        f"---\n"
        f"Smart Campus Management System\n"
        f"This is an automated notification."
    )

    emails = [
        (subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        for email in recipients
    ]

    try:
        count = send_mass_mail(emails, fail_silently=False)
        notice.email_sent = True
        notice.save(update_fields=['email_sent'])
        logger.info(f"Sent {count} notification emails for notice: {notice.title}")
        return count
    except Exception as e:
        logger.error(f"Failed to send notice emails: {e}")
        return 0


def send_attendance_alerts(threshold: float = 75.0) -> int:
    """
    Check for students with low attendance and send alert emails.
    Returns the number of alerts sent.
    """
    low_attendance = get_low_attendance_students(threshold)

    if not low_attendance:
        logger.info("No students below attendance threshold.")
        return 0

    emails_sent = 0
    for record in low_attendance:
        student = record['student']
        subject_line = (
            f"[Smart Campus] ⚠️ Attendance Alert — "
            f"{record['percentage']}% attendance"
        )
        message = (
            f"Dear {student.user.get_full_name()},\n\n"
            f"Your current overall attendance is {record['percentage']}%, "
            f"which is below the required minimum of {threshold}%.\n\n"
            f"Classes attended: {record['classes_attended']}/{record['total_classes']}\n\n"
            f"Please ensure regular attendance to avoid academic penalties.\n\n"
            f"---\n"
            f"Smart Campus Management System\n"
            f"This is an automated alert."
        )

        try:
            send_mail(
                subject_line,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [student.user.email],
                fail_silently=False,
            )
            emails_sent += 1
        except Exception as e:
            logger.error(
                f"Failed to send attendance alert to "
                f"{student.enrollment_number}: {e}"
            )

    logger.info(f"Sent {emails_sent} attendance alert emails.")
    return emails_sent

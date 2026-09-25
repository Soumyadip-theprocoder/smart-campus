"""
Tests for the Communication app.
Covers notice CRUD, email dispatch, and attendance alerts.
"""

from apps.accounts.models import User
from apps.communication.models import Notice
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class NoticeModelTests(TestCase):
    """Tests for the Notice model."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="pass",
            role="admin",
        )

    def test_create_notice(self):
        notice = Notice.objects.create(
            title="Test Notice",
            content="This is a test notice.",
            priority="medium",
            target_audience="all",
            posted_by=self.admin,
        )
        self.assertEqual(notice.title, "Test Notice")
        self.assertEqual(notice.priority, "medium")
        self.assertFalse(notice.email_sent)

    def test_notice_ordering(self):
        """Notices should be ordered newest first."""
        n1 = Notice.objects.create(
            title="First",
            content="...",
            priority="low",
            target_audience="all",
            posted_by=self.admin,
        )
        n2 = Notice.objects.create(
            title="Second",
            content="...",
            priority="high",
            target_audience="all",
            posted_by=self.admin,
        )
        notices = list(Notice.objects.all())
        self.assertEqual(notices[0].title, "Second")


class NoticeAPITests(TestCase):
    """Tests for notice API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="pass",
            role="admin",
            is_staff=True,
        )
        self.student = User.objects.create_user(
            email="stu@test.com",
            username="stu",
            password="pass",
            role="student",
        )
        self.notice = Notice.objects.create(
            title="Existing Notice",
            content="Already here.",
            priority="medium",
            target_audience="all",
            posted_by=self.admin,
        )

    def test_list_notices_authenticated(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(reverse("communication:notice-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_notices_unauthenticated(self):
        response = self.client.get(reverse("communication:notice-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_notice(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("communication:notice-create"),
            {
                "title": "New Notice",
                "content": "Important announcement.",
                "priority": "urgent",
                "target_audience": "all",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notice.objects.filter(title="New Notice").exists())

    def test_create_notice_has_posted_by_name(self):
        """Notice response should include posted_by_name."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("communication:notice-list"))
        results = response.data.get("results", response.data)
        if results:
            self.assertIn("posted_by_name", results[0])

    def test_delete_notice(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("communication:notice-delete", args=[self.notice.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notice.objects.filter(id=self.notice.id).exists())

    def test_attendance_alerts_endpoint(self):
        """Attendance alerts endpoint should respond (even with no low-attendance students)."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("communication:attendance-alerts"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)


class RobustnessCommunicationTests(TestCase):
    """Tests for edge cases and boundary conditions in communication."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="pass",
            role="admin",
            is_staff=True,
        )
        self.student = User.objects.create_user(
            email="stu@test.com",
            username="stu",
            password="pass",
            role="student",
        )

    def test_student_cannot_create_notice(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            reverse("communication:notice-create"),
            {
                "title": "Hacked Notice",
                "content": "Student created this.",
                "priority": "urgent",
                "target_audience": "all",
            },
        )
        # Will be either 403 or 401 depending on the exact setup, but shouldn't be 201
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_notice_missing_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("communication:notice-create"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertIn("content", response.data)

    def test_delete_notice_invalid_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("communication:notice-delete", args=[9999])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

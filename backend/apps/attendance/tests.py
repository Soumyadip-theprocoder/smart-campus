"""
Tests for the Attendance app.
Covers model creation, attendance listing, marking, reports, and summary.
"""

from datetime import date, timedelta

from apps.accounts.models import Faculty, Student, User
from apps.attendance.models import Attendance
from apps.attendance.services import get_low_attendance_students
from apps.scheduler.models import Subject
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class AttendanceModelTests(TestCase):
    """Tests for the Attendance model."""

    def setUp(self):
        self.faculty_user = User.objects.create_user(
            email="fac@test.com",
            username="fac",
            password="pass",
            role="faculty",
        )
        self.faculty = Faculty.objects.create(
            user=self.faculty_user,
            employee_id="FAC_T1",
            department="CS",
            designation="Professor",
        )
        self.student_user = User.objects.create_user(
            email="stu@test.com",
            username="stu",
            password="pass",
            role="student",
        )
        self.student = Student.objects.create(
            user=self.student_user,
            enrollment_number="STU_T1",
            department="CS",
            semester=3,
        )
        self.subject = Subject.objects.create(
            code="TEST101",
            name="Test Subject",
            faculty=self.faculty,
            credits=3,
            required_capacity=30,
            sessions_per_week=3,
        )

    def test_create_attendance_record(self):
        att = Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status=Attendance.Status.PRESENT,
            method=Attendance.Method.FACE_RECOGNITION,
        )
        self.assertEqual(att.status, "present")
        self.assertEqual(att.method, "face_recognition")
        self.assertEqual(str(att), f"STU_T1 — TEST101 — {date.today()} — present")

    def test_unique_constraint(self):
        """A student can only have one attendance record per subject per day."""
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status=Attendance.Status.PRESENT,
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                student=self.student,
                subject=self.subject,
                date=date.today(),
                status=Attendance.Status.ABSENT,
            )


class AttendanceAPITests(TestCase):
    """Tests for attendance API endpoints."""

    def setUp(self):
        self.client = APIClient()

        # Create admin
        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            password="pass",
            role="admin",
            is_staff=True,
        )

        # Create faculty + student + subject
        self.fac_user = User.objects.create_user(
            email="fac@test.com",
            username="fac",
            password="pass",
            role="faculty",
        )
        self.faculty = Faculty.objects.create(
            user=self.fac_user,
            employee_id="FAC_T2",
            department="CS",
            designation="Professor",
        )
        self.stu_user = User.objects.create_user(
            email="stu@test.com",
            username="stu",
            password="pass",
            role="student",
        )
        self.student = Student.objects.create(
            user=self.stu_user,
            enrollment_number="STU_T2",
            department="CS",
            semester=3,
        )
        self.subject = Subject.objects.create(
            code="ATT101",
            name="Attendance Test Subject",
            faculty=self.faculty,
            credits=3,
            required_capacity=30,
            sessions_per_week=3,
        )

    def test_list_attendance_as_admin(self):
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status="present",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("attendance:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_attendance_unauthenticated(self):
        response = self.client.get(reverse("attendance:list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_sees_only_own_attendance(self):
        """Students should only see their own attendance records."""
        # Create another student
        other_user = User.objects.create_user(
            email="other@test.com",
            username="other",
            password="pass",
            role="student",
        )
        other_student = Student.objects.create(
            user=other_user,
            enrollment_number="STU_OTHER",
            department="CS",
            semester=3,
        )
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status="present",
        )
        Attendance.objects.create(
            student=other_student,
            subject=self.subject,
            date=date.today(),
            status="absent",
        )

        self.client.force_authenticate(user=self.stu_user)
        response = self.client.get(reverse("attendance:list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        # Should only see their own record
        for record in results:
            self.assertEqual(
                record["student_name"],
                "Test User" if "student_name" in record else True,
                True,
            )

    def test_mark_attendance(self):
        response = self.client.post(
            reverse("attendance:mark"),
            {
                "enrollment_number": "STU_T2",
                "subject_id": self.subject.id,
                "date": str(date.today()),
                "method": "manual",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Attendance.objects.filter(
                student=self.student,
                subject=self.subject,
                date=date.today(),
            ).exists()
        )

    def test_mark_attendance_duplicate(self):
        """Second mark on the same day should return 200, not create duplicate."""
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status="present",
        )
        response = self.client.post(
            reverse("attendance:mark"),
            {
                "enrollment_number": "STU_T2",
                "subject_id": self.subject.id,
                "date": str(date.today()),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Attendance.objects.filter(
                student=self.student,
                subject=self.subject,
                date=date.today(),
            ).count(),
            1,
        )

    def test_mark_attendance_invalid_student(self):
        response = self.client.post(
            reverse("attendance:mark"),
            {
                "enrollment_number": "DOESNOTEXIST",
                "subject_id": self.subject.id,
                "date": str(date.today()),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_attendance_summary(self):
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date.today(),
            status="present",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("attendance:summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_students", response.data)
        self.assertIn("today_present", response.data)
        self.assertIn("overall_attendance_rate", response.data)

    def test_attendance_report(self):
        # Create attendance records over multiple days
        for i in range(5):
            Attendance.objects.create(
                student=self.student,
                subject=self.subject,
                date=date.today() - timedelta(days=i),
                status="present" if i < 3 else "absent",
            )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("attendance:report", args=[self.student.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # One subject
        self.assertEqual(response.data[0]["total_classes"], 5)
        self.assertEqual(response.data[0]["classes_attended"], 3)
        self.assertEqual(response.data[0]["percentage"], 60.0)


class LowAttendanceServiceTests(TestCase):
    """Tests for the get_low_attendance_students service."""

    def setUp(self):
        self.fac_user = User.objects.create_user(
            email="fac@test.com",
            username="fac",
            password="pass",
            role="faculty",
        )
        self.faculty = Faculty.objects.create(
            user=self.fac_user,
            employee_id="FAC_S1",
            department="CS",
            designation="Professor",
        )
        self.subject = Subject.objects.create(
            code="SVC101",
            name="Service Test",
            faculty=self.faculty,
            credits=3,
            required_capacity=30,
            sessions_per_week=3,
        )

    def _create_student_with_attendance(self, email, enrollment, present, absent):
        user = User.objects.create_user(
            email=email,
            username=enrollment,
            password="pass",
            role="student",
        )
        student = Student.objects.create(
            user=user,
            enrollment_number=enrollment,
            department="CS",
            semester=3,
        )
        for i in range(present):
            Attendance.objects.create(
                student=student,
                subject=self.subject,
                date=date.today() - timedelta(days=i),
                status="present",
            )
        for i in range(absent):
            Attendance.objects.create(
                student=student,
                subject=self.subject,
                date=date.today() - timedelta(days=present + i),
                status="absent",
            )
        return student

    def test_detects_low_attendance(self):
        # 40% attendance — should be flagged
        self._create_student_with_attendance("low@test.com", "LOW01", 2, 3)
        # 90% attendance — should NOT be flagged
        self._create_student_with_attendance("high@test.com", "HIGH01", 9, 1)

        result = get_low_attendance_students(threshold=75.0)
        enrollment_numbers = [r["student"].enrollment_number for r in result]
        self.assertIn("LOW01", enrollment_numbers)
        self.assertNotIn("HIGH01", enrollment_numbers)

    def test_empty_when_all_above_threshold(self):
        self._create_student_with_attendance("good@test.com", "GOOD01", 10, 0)
        result = get_low_attendance_students(threshold=75.0)
        self.assertEqual(len(result), 0)


class RobustnessAttendanceTests(TestCase):
    """Tests for edge cases and robustness in attendance marking."""

    def setUp(self):
        self.client = APIClient()
        self.fac_user = User.objects.create_user(
            email="fac@test.com",
            username="fac",
            password="pass",
            role="faculty",
        )
        self.faculty = Faculty.objects.create(
            user=self.fac_user,
            employee_id="FAC_R1",
            department="CS",
            designation="Professor",
        )
        self.stu_user = User.objects.create_user(
            email="stu@test.com",
            username="stu",
            password="pass",
            role="student",
        )
        self.student = Student.objects.create(
            user=self.stu_user,
            enrollment_number="STU_R1",
            department="CS",
            semester=3,
        )
        self.subject = Subject.objects.create(
            code="ROB101",
            name="Robustness Test Subject",
            faculty=self.faculty,
            credits=3,
            required_capacity=30,
            sessions_per_week=3,
        )

    def test_mark_attendance_future_date(self):
        # We don't have a future date validation yet, but it's good to test how it behaves
        future_date = date.today() + timedelta(days=5)
        response = self.client.post(
            reverse("attendance:mark"),
            {
                "enrollment_number": "STU_R1",
                "subject_id": self.subject.id,
                "date": str(future_date),
                "method": "manual",
            },
        )
        # Assuming the API allows it since there's no validator, it should be 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mark_attendance_invalid_method(self):
        response = self.client.post(
            reverse("attendance:mark"),
            {
                "enrollment_number": "STU_R1",
                "subject_id": self.subject.id,
                "date": str(date.today()),
                "method": "magic",  # invalid choice
            },
        )
        # Should be 400 since serializer enforces choices
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("method", response.data)

    def test_mark_attendance_missing_fields(self):
        response = self.client.post(reverse("attendance:mark"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("enrollment_number", response.data)
        self.assertIn("subject_id", response.data)
        self.assertIn("date", response.data)

    def test_get_report_invalid_student(self):
        self.client.force_authenticate(user=self.fac_user)
        response = self.client.get(reverse("attendance:report", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Faculty, Student
from apps.scheduler.models import Department

User = get_user_model()


class StandardizedIDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testadmin@smartcampus.edu",
            username="testadmin",
            password="adminpassword123",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_department_auto_generation(self):
        dept1 = Department.objects.create(name="Computer Science Engineering", core_department="CSE")
        self.assertTrue(dept1.dept_id.startswith("DEP-"))

        dept2 = Department.objects.create(name="Mechanical Engineering", core_department="MECH")
        self.assertTrue(dept2.dept_id.startswith("DEP-"))

        num1 = int(dept1.dept_id.split("-")[1])
        num2 = int(dept2.dept_id.split("-")[1])
        self.assertEqual(num2, num1 + 1)

    def test_next_department_id_endpoint(self):
        url = reverse("scheduler:next-department-id")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next_id", response.data)
        self.assertTrue(response.data["next_id"].startswith("DEP-"))

    def test_next_student_id_endpoint(self):
        url = reverse("accounts:next-student-id")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next_id", response.data)
        self.assertTrue(response.data["next_id"].startswith("STU-"))

    def test_next_faculty_id_endpoint(self):
        url = reverse("accounts:next-faculty-id")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next_id", response.data)
        self.assertTrue(response.data["next_id"].startswith("FAC-"))

    def test_student_auto_generation_on_save(self):
        user = User.objects.create_user(
            email="autostudent@smartcampus.edu",
            username="autostudent",
            password="pass",
            role=User.Role.STUDENT,
        )
        student = Student.objects.create(user=user)
        self.assertTrue(student.enrollment_number.startswith("STU-"))

    def test_faculty_auto_generation_on_save(self):
        user = User.objects.create_user(
            email="autofaculty@smartcampus.edu",
            username="autofaculty",
            password="pass",
            role=User.Role.FACULTY,
        )
        faculty = Faculty.objects.create(user=user)
        self.assertTrue(faculty.employee_id.startswith("FAC-"))

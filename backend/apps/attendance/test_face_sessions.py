import base64
import cv2
import numpy as np
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User, Faculty, Student, FaceSample
from apps.scheduler.models import Subject
from apps.attendance.models import AttendanceSession, Attendance

class FaceRecognitionSessionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.faculty_user = User.objects.create_user(
            email='faculty@test.com',
            password='password123',
            first_name='Fac',
            last_name='Ulty',
            role=User.Role.FACULTY
        )
        self.faculty = Faculty.objects.create(user=self.faculty_user, employee_id='F001')
        
        self.student_user = User.objects.create_user(
            email='student@test.com',
            password='password123',
            first_name='Stu',
            last_name='Dent',
            role=User.Role.STUDENT
        )
        self.student = Student.objects.create(user=self.student_user, enrollment_number='S001')
        
        # Mock encoding (128d vector)
        self.mock_encoding = np.random.rand(128).tolist()
        FaceSample.objects.create(student=self.student, face_encoding=self.mock_encoding)
        
        # Create Subject
        self.subject = Subject.objects.create(
            code='CS101',
            name='Test Subject',
            faculty=self.faculty,
            credits=3
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        
    def test_start_session(self):
        url = reverse('session-start')
        response = self.client.post(url, {'subject_id': self.subject.id})
        self.assertEqual(response.status_code, 200)
        self.assertIn('session_id', response.data)
        
        session = AttendanceSession.objects.get(id=response.data['session_id'])
        self.assertEqual(session.status, AttendanceSession.Status.ACTIVE)
        
    def test_end_session(self):
        session = AttendanceSession.objects.create(
            subject=self.subject,
            faculty=self.faculty,
            status=AttendanceSession.Status.ACTIVE
        )
        url = reverse('session-end', args=[session.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        
        session.refresh_from_db()
        self.assertEqual(session.status, AttendanceSession.Status.COMPLETED)
        
    def test_process_frame_unauthorized(self):
        self.client.force_authenticate(user=self.student_user)
        session = AttendanceSession.objects.create(subject=self.subject, faculty=self.faculty)
        url = reverse('session-process-frame', args=[session.id])
        response = self.client.post(url, {'frame': 'fakebase64'})
        self.assertEqual(response.status_code, 403)

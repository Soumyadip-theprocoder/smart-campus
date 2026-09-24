"""
Tests for the Accounts app.
Covers user model, authentication (login/register), JWT tokens,
and permission checks on profile endpoints.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, Student, Faculty


class UserModelTests(TestCase):
    """Tests for the custom User model and role properties."""

    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, User.Role.STUDENT)  # default role

    def test_role_properties(self):
        admin = User.objects.create_user(
            email='admin@test.com', username='admin',
            password='pass', role='admin',
        )
        student = User.objects.create_user(
            email='stu@test.com', username='stu',
            password='pass', role='student',
        )
        faculty = User.objects.create_user(
            email='fac@test.com', username='fac',
            password='pass', role='faculty',
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_student)
        self.assertTrue(student.is_student)
        self.assertFalse(student.is_faculty)
        self.assertTrue(faculty.is_faculty)

    def test_student_profile_creation(self):
        user = User.objects.create_user(
            email='stu@test.com', username='stu',
            password='pass', role='student',
        )
        student = Student.objects.create(
            user=user,
            enrollment_number='STU999',
            department='CS',
            semester=3,
        )
        self.assertEqual(student.enrollment_number, 'STU999')
        self.assertEqual(user.student_profile, student)

    def test_faculty_profile_creation(self):
        user = User.objects.create_user(
            email='fac@test.com', username='fac',
            password='pass', role='faculty',
        )
        faculty = Faculty.objects.create(
            user=user,
            employee_id='FAC999',
            department='CS',
            designation='Professor',
        )
        self.assertEqual(faculty.employee_id, 'FAC999')
        self.assertEqual(user.faculty_profile, faculty)


class LoginAPITests(TestCase):
    """Tests for the login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='test@campus.edu',
            username='testuser',
            password='correct_password',
            first_name='Test',
            last_name='User',
            role='student',
        )

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': 'test@campus.edu',
            'password': 'correct_password',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], 'test@campus.edu')

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            'email': 'test@campus.edu',
            'password': 'wrong_password',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            'email': 'nobody@campus.edu',
            'password': 'anything',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        response = self.client.post(self.login_url, {'email': 'test@campus.edu'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterAPITests(TestCase):
    """Tests for the registration endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts:register')

    def test_register_student_success(self):
        response = self.client.post(self.register_url, {
            'email': 'new@campus.edu',
            'username': 'newstudent',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'student',
            'enrollment_number': 'STU100',
            'department': 'CS',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertTrue(User.objects.filter(email='new@campus.edu').exists())
        self.assertTrue(Student.objects.filter(enrollment_number='STU100').exists())

    def test_register_faculty_success(self):
        response = self.client.post(self.register_url, {
            'email': 'fac@campus.edu',
            'username': 'newfaculty',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Faculty',
            'role': 'faculty',
            'employee_id': 'FAC100',
            'department': 'CS',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Faculty.objects.filter(employee_id='FAC100').exists())

    def test_register_student_missing_enrollment(self):
        response = self.client.post(self.register_url, {
            'email': 'bad@campus.edu',
            'username': 'badstudent',
            'password': 'securepass123',
            'first_name': 'Bad',
            'last_name': 'Student',
            'role': 'student',
            'department': 'CS',
            # missing enrollment_number
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email='taken@campus.edu', username='taken', password='pass',
        )
        response = self.client.post(self.register_url, {
            'email': 'taken@campus.edu',
            'username': 'another',
            'password': 'securepass123',
            'first_name': 'Dup',
            'last_name': 'User',
            'role': 'student',
            'enrollment_number': 'STU200',
            'department': 'CS',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeAPITests(TestCase):
    """Tests for the /me/ endpoint (authenticated profile)."""

    def setUp(self):
        self.client = APIClient()
        self.me_url = reverse('accounts:me')
        self.user = User.objects.create_user(
            email='me@campus.edu',
            username='meuser',
            password='testpass',
            first_name='Me',
            last_name='User',
            role='student',
        )
        Student.objects.create(
            user=self.user,
            enrollment_number='STU_ME',
            department='CS',
            semester=5,
        )

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@campus.edu')
        self.assertIn('profile', response.data)

    def test_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTTokenTests(TestCase):
    """Tests for JWT token flow (login -> use access -> refresh)."""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('accounts:login')
        self.refresh_url = reverse('accounts:token_refresh')
        self.me_url = reverse('accounts:me')
        self.user = User.objects.create_user(
            email='jwt@campus.edu',
            username='jwtuser',
            password='jwtpass',
            role='admin',
        )

    def test_jwt_full_flow(self):
        # Step 1: Login and get tokens
        login_resp = self.client.post(self.login_url, {
            'email': 'jwt@campus.edu',
            'password': 'jwtpass',
        })
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        access = login_resp.data['tokens']['access']
        refresh = login_resp.data['tokens']['refresh']

        # Step 2: Use access token to hit /me/
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me_resp = self.client.get(self.me_url)
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)

        # Step 3: Refresh token
        self.client.credentials()  # clear auth
        refresh_resp = self.client.post(self.refresh_url, {'refresh': refresh})
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)

    def test_jwt_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        me_resp = self.client.get(self.me_url)
        self.assertEqual(me_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(me_resp.data['code'], 'token_not_valid')

    def test_jwt_invalid_refresh_token(self):
        refresh_resp = self.client.post(self.refresh_url, {'refresh': 'invalid_refresh_token'})
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_resp.data['code'], 'token_not_valid')


class RobustnessAccountsTests(TestCase):
    """Tests for edge cases and boundary conditions in accounts."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')

    def test_register_invalid_role(self):
        response = self.client.post(self.register_url, {
            'email': 'bad_role@campus.edu',
            'username': 'badrole',
            'password': 'securepass123',
            'first_name': 'Bad',
            'last_name': 'Role',
            'role': 'hacker',  # invalid role
            'enrollment_number': 'STU_HACK',
            'department': 'CS',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)

    def test_login_invalid_email_format(self):
        response = self.client.post(self.login_url, {
            'email': 'not-an-email',
            'password': 'password',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_long_strings(self):
        long_string = 'A' * 300
        response = self.client.post(self.register_url, {
            'email': f'{long_string}@campus.edu',
            'username': long_string,
            'password': 'securepass123',
            'first_name': long_string,
            'last_name': long_string,
            'role': 'student',
            'enrollment_number': 'STU_LONG',
            'department': 'CS',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Should fail validation due to max_length constraints


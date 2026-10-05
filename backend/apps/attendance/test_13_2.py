from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient

from apps.attendance.models import AlertLog, Attendance
from apps.attendance.tasks import dispatch_absenteeism_alerts_task
from apps.accounts.models import Student, User, Faculty
from apps.scheduler.models import Subject

class Phase13_2_UAT(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="pwd", first_name="Test")
        self.student = Student.objects.create(user=self.user, enrollment_number="STU001")
        
        self.fac_user = User.objects.create_user(username="facuser", email="fac@example.com", password="pwd")
        self.faculty = Faculty.objects.create(user=self.fac_user, employee_id="EMP001")
        
        self.subject = Subject.objects.create(code="SUB101", name="Test Subject", faculty=self.faculty)
        
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=timezone.now().date(),
            status="present",
            method="manual"
        )
        self.client = APIClient()

    @patch('apps.attendance.tasks.predict_absenteeism_risk')
    @patch('apps.attendance.tasks.send_mail')
    def test_scenario_a_initial_dispatch(self, mock_send_mail, mock_predict):
        """Scenario A: Initial Dispatch (No Prior Alerts)"""
        mock_predict.return_value = {"is_at_risk": True, "current_pct": 50.0, "risk_probability": 0.9}
        
        result = dispatch_absenteeism_alerts_task()
        
        self.assertEqual(result['dispatched'], 1)
        mock_send_mail.assert_called_once()
        self.assertTrue(AlertLog.objects.filter(student=self.student, subject=self.subject).exists())

    @patch('apps.attendance.tasks.predict_absenteeism_risk')
    @patch('apps.attendance.tasks.send_mail')
    def test_scenario_b_anti_spam_cooldown(self, mock_send_mail, mock_predict):
        """Scenario B: Anti-Spam Cooldown (Within 7 Days)"""
        mock_predict.return_value = {"is_at_risk": True, "current_pct": 50.0, "risk_probability": 0.9}
        
        AlertLog.objects.create(student=self.student, subject=self.subject)
        AlertLog.objects.filter(student=self.student).update(dispatched_at=timezone.now() - timedelta(days=2))
        
        result = dispatch_absenteeism_alerts_task()
        
        self.assertEqual(result['dispatched'], 0)
        self.assertEqual(result['cooldown_skipped'], 1)
        mock_send_mail.assert_not_called()

    @patch('apps.attendance.tasks.predict_absenteeism_risk')
    @patch('apps.attendance.tasks.send_mail')
    def test_scenario_c_cooldown_expiration(self, mock_send_mail, mock_predict):
        """Scenario C: Cooldown Expiration (After 7 Days)"""
        mock_predict.return_value = {"is_at_risk": True, "current_pct": 50.0, "risk_probability": 0.9}
        
        old_log = AlertLog.objects.create(student=self.student, subject=self.subject)
        AlertLog.objects.filter(id=old_log.id).update(dispatched_at=timezone.now() - timedelta(days=8))
        
        result = dispatch_absenteeism_alerts_task()
        
        self.assertEqual(result['dispatched'], 1)
        mock_send_mail.assert_called_once()
        self.assertEqual(AlertLog.objects.filter(student=self.student, subject=self.subject).count(), 2)

    @patch('apps.attendance.tasks.predict_absenteeism_risk')
    @patch('apps.attendance.tasks.send_mail')
    def test_scenario_d_safe_student_ignored(self, mock_send_mail, mock_predict):
        """Scenario D: Safe Student Ignored"""
        mock_predict.return_value = {"is_at_risk": False, "current_pct": 90.0, "risk_probability": 0.1}
        
        result = dispatch_absenteeism_alerts_task()
        
        self.assertEqual(result['dispatched'], 0)
        mock_send_mail.assert_not_called()
        self.assertFalse(AlertLog.objects.filter(student=self.student, subject=self.subject).exists())

    def test_scenario_e_api_trigger_acceptance(self):
        """Scenario E: API Trigger Acceptance"""
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'pwd')
        self.client.force_authenticate(user=admin_user)
        
        response = self.client.post('/api/attendance/alerts/dispatch/')
        
        self.assertEqual(response.status_code, 202)
        self.assertIn("task_id", response.data)

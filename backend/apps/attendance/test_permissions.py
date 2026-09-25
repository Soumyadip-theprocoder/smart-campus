from django.conf import settings
from django.test import RequestFactory, TestCase
from rest_framework.views import APIView

from .permissions import HasFaceEngineAPIKey


class DummyView(APIView):
    pass


class HasFaceEngineAPIKeyTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = HasFaceEngineAPIKey()
        self.view = DummyView()
        # Set a test API key
        settings.FACE_ENGINE_API_KEY = "test-secret-key-123"

    def test_missing_header_denied(self):
        request = self.factory.post("/api/attendance/mark/")
        # DRF permissions expect a DRF Request, but BasePermission works with standard WSGIRequest if .headers is used
        # We simulate DRF Request by attaching headers
        request.headers = {}

        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_invalid_header_format_denied(self):
        request = self.factory.post("/api/attendance/mark/")
        request.headers = {"Authorization": "Bearer test-secret-key-123"}
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_incorrect_key_denied(self):
        request = self.factory.post("/api/attendance/mark/")
        request.headers = {"Authorization": "Api-Key wrong-key"}
        self.assertFalse(self.permission.has_permission(request, self.view))

    def test_correct_key_allowed(self):
        request = self.factory.post("/api/attendance/mark/")
        request.headers = {"Authorization": "Api-Key test-secret-key-123"}
        self.assertTrue(self.permission.has_permission(request, self.view))

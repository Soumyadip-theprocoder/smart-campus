"""
Views for the Accounts app.
JWT-based authentication and user profile endpoints.
"""

from rest_framework import generics, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AcademicGroup, Faculty, Student, User
from .serializers import (AcademicGroupSerializer, FacultySerializer, LoginSerializer,
                          RegisterSerializer, StudentSerializer,
                          UserSerializer)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from seed_data import seed  # noqa: E402


class AcademicGroupViewSet(viewsets.ModelViewSet):
    """CRUD operations for Academic Groups."""
    queryset = AcademicGroup.objects.all()
    serializer_class = AcademicGroupSerializer
    permission_classes = [permissions.IsAdminUser]


class SeedDatabaseView(APIView):
    """Seed the database with demo data if it doesn't exist."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if User.objects.filter(email="admin@smartcampus.edu").exists():
            return Response({"message": "Database already seeded."}, status=status.HTTP_200_OK)
        
        try:
            seed()
            return Response({"message": "Database successfully seeded."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterView(generics.CreateAPIView):
    """Register a new user (admin-only in production)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )


class MeView(APIView):
    """Get the current authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        # Attach role-specific profile
        if user.is_student and hasattr(user, "student_profile"):
            data["profile"] = StudentSerializer(user.student_profile).data
        elif user.is_faculty and hasattr(user, "faculty_profile"):
            data["profile"] = FacultySerializer(user.faculty_profile).data

        return Response(data)

    def put(self, request):
        user = request.user
        if user.is_student and hasattr(user, "student_profile"):
            needs = request.data.get("accessibility_needs")
            if isinstance(needs, list):
                user.student_profile.accessibility_needs = needs
                user.student_profile.save()
        return self.get(request)


class StudentListView(generics.ListAPIView):
    """List all students (admin only)."""

    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Student.objects.select_related("user").all()


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a single student's details."""

    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Student.objects.select_related("user").all()

    def get_object(self):
        obj = super().get_object()
        # Admin can access any student. A student can only access their own profile.
        if not self.request.user.is_staff:
            if not hasattr(self.request.user, 'student_profile') or self.request.user.student_profile != obj:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have permission to modify this student's profile.")
        return obj

    def perform_destroy(self, instance):
        # Delete the associated user (cascades to student profile)
        if instance.user:
            instance.user.delete()
        else:
            instance.delete()


class FacultyListView(generics.ListAPIView):
    """List all faculty (admin only)."""

    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Faculty.objects.select_related("user").all()


class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a faculty member."""

    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Faculty.objects.select_related("user").all()

    def perform_destroy(self, instance):
        # Delete the associated user (cascades to faculty profile)
        instance.user.delete()


from .models import FaceSample

class FaceSampleListCreateView(APIView):
    """List or register face samples for a student."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, student_id):
        # Allow admins, faculty, or the student themselves
        if not (request.user.is_admin or request.user.is_faculty or 
               (request.user.is_student and request.user.student_profile.id == student_id)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        samples = FaceSample.objects.filter(student_id=student_id)
        data = [{"id": s.id, "created_at": s.created_at, "image_url": s.image.url if s.image else None} for s in samples]
        return Response(data)

    def post(self, request, student_id):
        if not (request.user.is_admin or request.user.is_faculty or 
               (request.user.is_student and request.user.student_profile.id == student_id)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get("face_image")
        if not file_obj:
            return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

        from django.conf import settings
        import requests

        encoding_list = None

        if getattr(settings, "FACE_ENGINE_URL", None):
            url = f"{settings.FACE_ENGINE_URL.rstrip('/')}/encode"
            headers = {"Bypass-Tunnel-Reminder": "true"}
            if getattr(settings, "FACE_ENGINE_API_KEY", None):
                headers["Authorization"] = f"Bearer {settings.FACE_ENGINE_API_KEY}"
            try:
                file_obj.seek(0)
                files = {"file": (file_obj.name, file_obj, file_obj.content_type)}
                response = requests.post(url, files=files, headers=headers, timeout=30)
                if response.status_code == 200:
                    encoding_list = response.json().get("encoding")
                else:
                    return Response({"error": response.json().get("detail", "Face Engine Error")}, status=400)
            except requests.RequestException as e:
                return Response({"error": str(e)}, status=503)
        else:
            try:
                import face_recognition
                file_obj.seek(0)
                image = face_recognition.load_image_file(file_obj)
                face_locations = face_recognition.face_locations(image, model="hog")
                if not face_locations:
                    return Response({"error": "No face detected."}, status=400)
                if len(face_locations) > 1:
                    return Response({"error": "Multiple faces detected."}, status=400)
                encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
                encoding_list = encoding.tolist()
            except ImportError:
                return Response({"error": "Face recognition not installed locally."}, status=501)
            except Exception as e:
                return Response({"error": str(e)}, status=500)

        if not encoding_list:
            return Response({"error": "Failed to extract encoding."}, status=500)

        sample = FaceSample.objects.create(
            student=student,
            face_encoding=encoding_list,
            image=file_obj
        )
        # Invalidate the live session face encoding cache so new faces are recognized immediately
        try:
            from apps.attendance.views import invalidate_face_encodings_cache
            invalidate_face_encodings_cache()
        except ImportError:
            pass
        return Response({"message": "Face registered successfully.", "id": sample.id}, status=status.HTTP_201_CREATED)


class FaceSampleDeleteView(APIView):
    """Delete a face sample."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, student_id, sample_id):
        if not (request.user.is_admin or request.user.is_faculty or 
               (request.user.is_student and request.user.student_profile.id == student_id)):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            sample = FaceSample.objects.get(id=sample_id, student_id=student_id)
            sample.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FaceSample.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

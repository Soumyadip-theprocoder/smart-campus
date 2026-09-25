"""
Views for the Accounts app.
JWT-based authentication and user profile endpoints.
"""

from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Faculty, Student, User
from .serializers import (FacultySerializer, LoginSerializer,
                          RegisterSerializer, StudentSerializer,
                          UserSerializer)
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from seed_data import seed


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


class StudentListView(generics.ListAPIView):
    """List all students (admin only)."""

    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Student.objects.select_related("user").all()


class StudentDetailView(generics.RetrieveAPIView):
    """Get a single student's details."""

    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Student.objects.select_related("user").all()


class FacultyListView(generics.ListAPIView):
    """List all faculty (admin only)."""

    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Faculty.objects.select_related("user").all()


class FacultyDetailView(generics.RetrieveDestroyAPIView):
    """Retrieve or delete a faculty member."""

    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Faculty.objects.select_related("user").all()

    def perform_destroy(self, instance):
        # Delete the associated user (cascades to faculty profile)
        instance.user.delete()


class FaceRegistrationView(APIView):
    """Register face data for a student via uploaded image."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        if not user.is_student or not hasattr(user, "student_profile"):
            return Response(
                {"error": "Only students can register face data."},
                status=status.HTTP_403_FORBIDDEN,
            )

        file_obj = request.FILES.get("face_image")
        if not file_obj:
            return Response(
                {"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        from django.conf import settings
        import requests

        encoding_list = None

        if getattr(settings, "FACE_ENGINE_URL", None):
            # Use external Colab API
            url = f"{settings.FACE_ENGINE_URL.rstrip('/')}/encode"
            headers = {}
            if getattr(settings, "FACE_ENGINE_API_KEY", None):
                headers["Authorization"] = f"Bearer {settings.FACE_ENGINE_API_KEY}"
            
            try:
                # Reset file pointer before reading
                file_obj.seek(0)
                files = {"file": (file_obj.name, file_obj, file_obj.content_type)}
                response = requests.post(url, files=files, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    encoding_list = data.get("encoding")
                else:
                    err_msg = response.json().get("detail", "Unknown error")
                    return Response(
                        {"error": f"Face Engine Error: {err_msg}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except requests.RequestException as e:
                return Response(
                    {"error": f"Failed to connect to Face Engine API: {str(e)}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        else:
            # Local fallback
            try:
                import face_recognition
            except ImportError:
                return Response(
                    {"error": "Face recognition is not enabled on this server and FACE_ENGINE_URL is not set."},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

            try:
                # Reset file pointer
                file_obj.seek(0)
                image = face_recognition.load_image_file(file_obj)
                face_locations = face_recognition.face_locations(image, model="hog")

                if not face_locations:
                    return Response(
                        {"error": "No face detected in the image."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if len(face_locations) > 1:
                    return Response(
                        {
                            "error": "Multiple faces detected. Please ensure only your face is visible."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
                encoding_list = encoding.tolist()
            except Exception as e:
                return Response(
                    {"error": f"Failed to process image locally: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        if not encoding_list:
            return Response(
                {"error": "Failed to extract face encoding."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            student = user.student_profile
            student.face_encoding = encoding_list
            student.face_image = file_obj
            student.save()

            return Response(
                {"message": "Face registered successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to save profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

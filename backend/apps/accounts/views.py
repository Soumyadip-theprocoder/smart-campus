"""
Views for the Accounts app.
JWT-based authentication and user profile endpoints.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Student, Faculty
from .serializers import (
    UserSerializer, StudentSerializer, FacultySerializer,
    RegisterSerializer, LoginSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Register a new user (admin-only in production)."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAdminUser in prod

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate user and return JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        })


class MeView(APIView):
    """Get the current authenticated user's profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        # Attach role-specific profile
        if user.is_student and hasattr(user, 'student_profile'):
            data['profile'] = StudentSerializer(user.student_profile).data
        elif user.is_faculty and hasattr(user, 'faculty_profile'):
            data['profile'] = FacultySerializer(user.faculty_profile).data

        return Response(data)


class StudentListView(generics.ListAPIView):
    """List all students (admin only)."""
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Student.objects.select_related('user').all()


class StudentDetailView(generics.RetrieveAPIView):
    """Get a single student's details."""
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Student.objects.select_related('user').all()


class FacultyListView(generics.ListAPIView):
    """List all faculty (admin only)."""
    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Faculty.objects.select_related('user').all()

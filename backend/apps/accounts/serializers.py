"""
Serializers for the Accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Student, Faculty


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student profile."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'user', 'enrollment_number', 'department',
            'semester', 'face_image',
        ]
        read_only_fields = ['id']


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty profile."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Faculty
        fields = ['id', 'user', 'employee_id', 'department', 'designation', 'max_hours_per_week', 'availability']
        read_only_fields = ['id']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=6)
    enrollment_number = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'first_name', 'last_name',
            'role', 'enrollment_number', 'employee_id', 'department',
        ]

    def validate(self, attrs):
        role = attrs.get('role', User.Role.STUDENT)
        if role == User.Role.STUDENT and not attrs.get('enrollment_number'):
            raise serializers.ValidationError(
                {'enrollment_number': 'Required for students.'}
            )
        if role == User.Role.FACULTY and not attrs.get('employee_id'):
            raise serializers.ValidationError(
                {'employee_id': 'Required for faculty.'}
            )
        return attrs

    def create(self, validated_data):
        enrollment_number = validated_data.pop('enrollment_number', None)
        employee_id = validated_data.pop('employee_id', None)
        department = validated_data.pop('department', '')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Create associated profile
        if user.role == User.Role.STUDENT:
            Student.objects.create(
                user=user,
                enrollment_number=enrollment_number,
                department=department,
            )
        elif user.role == User.Role.FACULTY:
            Faculty.objects.create(
                user=user,
                employee_id=employee_id,
                department=department,
            )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login — validates credentials."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled.')
        attrs['user'] = user
        return attrs

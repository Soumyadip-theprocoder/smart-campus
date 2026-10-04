"""
Serializers for the Accounts app.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import AcademicGroup, Faculty, Student, User
from apps.scheduler.models import Department


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name", "last_name", "role"]
        read_only_fields = ["id"]


class AcademicGroupSerializer(serializers.ModelSerializer):
    """Serializer for AcademicGroup."""

    class Meta:
        model = AcademicGroup
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student profile."""

    user = UserSerializer(read_only=True)
    has_face_encoding = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "enrollment_number",
            "department",
            "semester",
            "marks_10th",
            "marks_12th",
            "cgpa_semesters",
            "face_image",
            "has_face_encoding",
            "accessibility_needs",
            "is_ta",
            "ta_max_hours_per_week",
            "ta_qualified_subjects",
        ]
        read_only_fields = ["id"]

    def get_has_face_encoding(self, obj):
        # Check both legacy Student.face_encoding and FaceSample entries
        if obj.face_encoding is not None:
            return True
        return obj.face_samples.exists()

    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)

    def update(self, instance, validated_data):
        user_data = {}
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        if 'email' in validated_data:
            user_data['email'] = validated_data.pop('email')

        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        return super().update(instance, validated_data)


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty profile."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Faculty
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "employee_id",
            "department",
            "designation",
            "max_hours_per_week",
            "availability",
        ]
        read_only_fields = ["id"]

    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)

    def update(self, instance, validated_data):
        user_data = {}
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        if 'email' in validated_data:
            user_data['email'] = validated_data.pop('email')

        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=6)
    enrollment_number = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(required=False, allow_blank=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False, allow_null=True)
    semester = serializers.IntegerField(required=False, default=1)
    marks_10th = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    marks_12th = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    cgpa_semesters = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "role",
            "enrollment_number",
            "employee_id",
            "department",
            "semester",
            "marks_10th",
            "marks_12th",
            "cgpa_semesters",
        ]

    def validate(self, attrs):
        role = attrs.get("role", User.Role.STUDENT)
        if role == User.Role.STUDENT and not attrs.get("enrollment_number"):
            raise serializers.ValidationError(
                {"enrollment_number": "Required for students."}
            )
        if role == User.Role.FACULTY and not attrs.get("employee_id"):
            raise serializers.ValidationError({"employee_id": "Required for faculty."})
        return attrs

    def create(self, validated_data):
        enrollment_number = validated_data.pop("enrollment_number", None)
        employee_id = validated_data.pop("employee_id", None)
        department = validated_data.pop("department", None)
        semester = validated_data.pop("semester", 1)
        marks_10th = validated_data.pop("marks_10th", None)
        marks_12th = validated_data.pop("marks_12th", None)
        cgpa_semesters = validated_data.pop("cgpa_semesters", {})
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Create associated profile
        if user.role == User.Role.STUDENT:
            profile = Student.objects.create(
                user=user,
                enrollment_number=enrollment_number,
                department=department,
                semester=semester,
                marks_10th=marks_10th,
                marks_12th=marks_12th,
                cgpa_semesters=cgpa_semesters,
            )
        elif user.role == User.Role.FACULTY:
            profile = Faculty.objects.create(
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
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        attrs["user"] = user
        return attrs

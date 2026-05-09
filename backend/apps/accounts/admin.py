"""
Admin registration for Accounts models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Faculty


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['enrollment_number', 'get_name', 'department', 'semester']
    list_filter = ['department', 'semester']
    search_fields = ['enrollment_number', 'user__first_name', 'user__last_name']

    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_name', 'department', 'designation']
    list_filter = ['department', 'designation']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name']

    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'

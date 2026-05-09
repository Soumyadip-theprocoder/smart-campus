"""
Seed data script for Smart Campus Management System.
Creates demo users, students, faculty, subjects, rooms, and time slots.

Usage:
    python manage.py shell < seed_data.py
    OR
    python seed_data.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User, Student, Faculty
from apps.scheduler.models import Subject, Room, TimeSlot
from apps.communication.models import Notice
from apps.attendance.models import Attendance
from datetime import time, date, timedelta
import random


def seed():
    print("🌱 Seeding database...\n")

    # ── Admin User ──────────────────────────────────────────────────
    admin_user, created = User.objects.get_or_create(
        email='admin@smartcampus.edu',
        defaults={
            'username': 'admin',
            'first_name': 'System',
            'last_name': 'Admin',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✓ Admin user created (admin@smartcampus.edu / admin123)")

    # ── Faculty ─────────────────────────────────────────────────────
    faculty_data = [
        {
            'email': 'john.smith@smartcampus.edu',
            'username': 'jsmith',
            'first_name': 'John',
            'last_name': 'Smith',
            'employee_id': 'FAC001',
            'department': 'Computer Science',
            'designation': 'Professor',
        },
        {
            'email': 'sarah.johnson@smartcampus.edu',
            'username': 'sjohnson',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'employee_id': 'FAC002',
            'department': 'Computer Science',
            'designation': 'Associate Professor',
        },
        {
            'email': 'mike.wilson@smartcampus.edu',
            'username': 'mwilson',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'employee_id': 'FAC003',
            'department': 'Mathematics',
            'designation': 'Assistant Professor',
        },
        {
            'email': 'emily.davis@smartcampus.edu',
            'username': 'edavis',
            'first_name': 'Emily',
            'last_name': 'Davis',
            'employee_id': 'FAC004',
            'department': 'Electronics',
            'designation': 'Professor',
        },
    ]

    faculty_objects = []
    for fd in faculty_data:
        user, created = User.objects.get_or_create(
            email=fd['email'],
            defaults={
                'username': fd['username'],
                'first_name': fd['first_name'],
                'last_name': fd['last_name'],
                'role': 'faculty',
            },
        )
        if created:
            user.set_password('faculty123')
            user.save()

        faculty, _ = Faculty.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': fd['employee_id'],
                'department': fd['department'],
                'designation': fd['designation'],
            },
        )
        faculty_objects.append(faculty)
        print(f"✓ Faculty: {fd['first_name']} {fd['last_name']} ({fd['employee_id']})")

    # ── Students ────────────────────────────────────────────────────
    student_data = [
        {
            'email': 'alice.brown@smartcampus.edu',
            'username': 'abrown',
            'first_name': 'Alice',
            'last_name': 'Brown',
            'enrollment_number': 'STU001',
            'department': 'Computer Science',
            'semester': 5,
        },
        {
            'email': 'bob.taylor@smartcampus.edu',
            'username': 'btaylor',
            'first_name': 'Bob',
            'last_name': 'Taylor',
            'enrollment_number': 'STU002',
            'department': 'Computer Science',
            'semester': 5,
        },
        {
            'email': 'charlie.lee@smartcampus.edu',
            'username': 'clee',
            'first_name': 'Charlie',
            'last_name': 'Lee',
            'enrollment_number': 'STU003',
            'department': 'Computer Science',
            'semester': 3,
        },
        {
            'email': 'diana.patel@smartcampus.edu',
            'username': 'dpatel',
            'first_name': 'Diana',
            'last_name': 'Patel',
            'enrollment_number': 'STU004',
            'department': 'Electronics',
            'semester': 5,
        },
        {
            'email': 'ethan.kim@smartcampus.edu',
            'username': 'ekim',
            'first_name': 'Ethan',
            'last_name': 'Kim',
            'enrollment_number': 'STU005',
            'department': 'Mathematics',
            'semester': 3,
        },
    ]

    for sd in student_data:
        user, created = User.objects.get_or_create(
            email=sd['email'],
            defaults={
                'username': sd['username'],
                'first_name': sd['first_name'],
                'last_name': sd['last_name'],
                'role': 'student',
            },
        )
        if created:
            user.set_password('student123')
            user.save()

        Student.objects.get_or_create(
            user=user,
            defaults={
                'enrollment_number': sd['enrollment_number'],
                'department': sd['department'],
                'semester': sd['semester'],
            },
        )
        print(f"✓ Student: {sd['first_name']} {sd['last_name']} ({sd['enrollment_number']})")

    # ── Rooms ───────────────────────────────────────────────────────
    rooms_data = [
        {'room_number': 'LH-101', 'capacity': 60, 'building': 'Main Block', 'room_type': 'lecture'},
        {'room_number': 'LH-102', 'capacity': 60, 'building': 'Main Block', 'room_type': 'lecture'},
        {'room_number': 'LH-201', 'capacity': 40, 'building': 'Main Block', 'room_type': 'lecture'},
        {'room_number': 'LAB-301', 'capacity': 30, 'building': 'CS Block', 'room_type': 'lab'},
        {'room_number': 'LAB-302', 'capacity': 30, 'building': 'CS Block', 'room_type': 'lab'},
        {'room_number': 'SR-101', 'capacity': 20, 'building': 'Annex', 'room_type': 'seminar'},
    ]

    for rd in rooms_data:
        Room.objects.get_or_create(
            room_number=rd['room_number'],
            defaults=rd,
        )
        print(f"✓ Room: {rd['room_number']} ({rd['building']}, cap: {rd['capacity']})")

    # ── Time Slots ──────────────────────────────────────────────────
    slot_times = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']

    for day in days:
        for start, end in slot_times:
            TimeSlot.objects.get_or_create(
                day=day,
                start_time=start,
                end_time=end,
            )

    print(f"✓ Time slots: {len(days)} days × {len(slot_times)} slots = {len(days)*len(slot_times)} total")

    # ── Subjects ────────────────────────────────────────────────────
    subjects_data = [
        {
            'code': 'CS301',
            'name': 'Data Structures & Algorithms',
            'faculty': faculty_objects[0],
            'credits': 4,
            'required_capacity': 40,
            'sessions_per_week': 3,
        },
        {
            'code': 'CS302',
            'name': 'Database Management Systems',
            'faculty': faculty_objects[1],
            'credits': 3,
            'required_capacity': 40,
            'sessions_per_week': 3,
        },
        {
            'code': 'CS303',
            'name': 'Computer Networks',
            'faculty': faculty_objects[0],
            'credits': 3,
            'required_capacity': 40,
            'sessions_per_week': 2,
        },
        {
            'code': 'MA201',
            'name': 'Discrete Mathematics',
            'faculty': faculty_objects[2],
            'credits': 3,
            'required_capacity': 60,
            'sessions_per_week': 3,
        },
        {
            'code': 'EC201',
            'name': 'Digital Electronics',
            'faculty': faculty_objects[3],
            'credits': 4,
            'required_capacity': 40,
            'sessions_per_week': 3,
        },
        {
            'code': 'CS304',
            'name': 'Artificial Intelligence',
            'faculty': faculty_objects[1],
            'credits': 3,
            'required_capacity': 30,
            'sessions_per_week': 2,
        },
    ]

    for sd in subjects_data:
        Subject.objects.get_or_create(
            code=sd['code'],
            defaults=sd,
        )
        print(f"✓ Subject: {sd['code']} — {sd['name']}")

    # ── Sample Notices ──────────────────────────────────────────────
    notices_data = [
        {
            'title': 'Mid-Semester Examination Schedule Released',
            'content': 'The mid-semester examination schedule for all departments has been released. Please check the timetable section for your exam dates and timings. All students are requested to carry their ID cards to the examination hall.',
            'priority': 'high',
            'target_audience': 'all',
        },
        {
            'title': 'Campus Wi-Fi Maintenance — Weekend Downtime',
            'content': 'The campus Wi-Fi network will undergo scheduled maintenance this Saturday from 10:00 PM to Sunday 6:00 AM. Please plan your work accordingly.',
            'priority': 'medium',
            'target_audience': 'all',
        },
        {
            'title': 'Workshop on Machine Learning — Register Now',
            'content': 'The Computer Science department is organizing a two-day workshop on "Practical Machine Learning with Python" on May 20-21. Registration is open for all CS students. Limited seats available.',
            'priority': 'low',
            'target_audience': 'students',
        },
    ]

    for nd in notices_data:
        Notice.objects.get_or_create(
            title=nd['title'],
            defaults={**nd, 'posted_by': admin_user},
        )
        print(f"✓ Notice: {nd['title'][:50]}...")

    # ── Attendance Records ──────────────────────────────────────────
    print("\n📋 Seeding attendance records...")

    random.seed(42)  # Deterministic for reproducibility

    students = list(Student.objects.all())
    subjects = list(Subject.objects.all())
    today = date.today()

    # Map subjects to the days they have classes (simulate a timetable)
    subject_class_days = {
        'CS301': [0, 2, 4],      # Mon, Wed, Fri
        'CS302': [1, 3, 4],      # Tue, Thu, Fri
        'CS303': [0, 3],         # Mon, Thu
        'MA201': [1, 2, 4],      # Tue, Wed, Fri
        'EC201': [0, 2, 3],      # Mon, Wed, Thu
        'CS304': [1, 3],         # Tue, Thu
    }

    # Per-student attendance tendency (some students attend more regularly)
    student_attendance_rate = {
        'STU001': 0.92,  # Alice — very regular
        'STU002': 0.78,  # Bob — decent
        'STU003': 0.65,  # Charlie — struggles
        'STU004': 0.88,  # Diana — good
        'STU005': 0.72,  # Ethan — average
    }

    attendance_count = 0
    for day_offset in range(30, 0, -1):  # Last 30 days
        current_date = today - timedelta(days=day_offset)
        weekday = current_date.weekday()  # 0=Mon ... 6=Sun

        if weekday >= 5:  # Skip weekends
            continue

        for subj in subjects:
            class_days = subject_class_days.get(subj.code, [])
            if weekday not in class_days:
                continue

            for student in students:
                rate = student_attendance_rate.get(
                    student.enrollment_number, 0.80
                )
                is_present = random.random() < rate
                method = random.choice(
                    ['face_recognition', 'face_recognition',
                     'face_recognition', 'manual']  # 75% face recog
                )

                obj, created = Attendance.objects.get_or_create(
                    student=student,
                    subject=subj,
                    date=current_date,
                    defaults={
                        'status': 'present' if is_present else 'absent',
                        'method': method,
                    },
                )
                if created:
                    attendance_count += 1

    print(f"✓ Attendance records created: {attendance_count}")

    # Print per-student summary
    for student in students:
        total = Attendance.objects.filter(student=student).count()
        present = Attendance.objects.filter(
            student=student, status='present'
        ).count()
        pct = (present / total * 100) if total else 0
        print(
            f"  📊 {student.user.first_name} {student.user.last_name}: "
            f"{present}/{total} present ({pct:.0f}%)"
        )

    print("\n✅ Database seeding complete!")


if __name__ == '__main__':
    seed()

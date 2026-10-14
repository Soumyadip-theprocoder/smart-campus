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

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

import random
from datetime import date, time, timedelta

from apps.accounts.models import Faculty, Student, User
from apps.attendance.models import Attendance
from apps.communication.models import Notice
from apps.scheduler.models import Department, Room, Subject, TimeSlot


def seed():
    print("Seeding database...\n")

    # ── Admin User ──────────────────────────────────────────────────
    admin_user, created = User.objects.get_or_create(
        email="admin@smartcampus.edu",
        defaults={
            "username": "admin",
            "first_name": "System",
            "last_name": "Admin",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")
    admin_user.set_password(admin_password)
    admin_user.save()
    print("[OK] Admin user ensured (admin@smartcampus.edu)")

    # ── Faculty ─────────────────────────────────────────────────────
    faculty_data = [
        {
            "email": "john.smith.dep0009@smartcampus.edu",
            "username": "john.smith.dep0009",
            "first_name": "John",
            "last_name": "Smith",
            "employee_id": "FAC-2026-0001",
            "department": "Computer Science",
            "designation": "Professor",
        },
        {
            "email": "sarah.johnson.dep0009@smartcampus.edu",
            "username": "sarah.johnson.dep0009",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "employee_id": "FAC-2026-0002",
            "department": "Computer Science",
            "designation": "Associate Professor",
        },
        {
            "email": "mike.wilson.dep0010@smartcampus.edu",
            "username": "mike.wilson.dep0010",
            "first_name": "Mike",
            "last_name": "Wilson",
            "employee_id": "FAC-2026-0003",
            "department": "Mathematics",
            "designation": "Assistant Professor",
        },
        {
            "email": "emily.davis.dep0010@smartcampus.edu",
            "username": "emily.davis.dep0010",
            "first_name": "Emily",
            "last_name": "Davis",
            "employee_id": "FAC-2026-0004",
            "department": "Electronics",
            "designation": "Professor",
        },
    ]

    # Generate 50+ Unique Realistic Departments
    programs = ["B.Tech", "M.Tech", "B.Sc", "M.Sc", "BCA", "MCA", "MBA", "BBA", "B.A.", "M.A.", "Ph.D"]
    disciplines = [
        "Computer Science", "Information Technology", "Artificial Intelligence",
        "Data Science", "Cyber Security", "Software Engineering", "Electronics",
        "Electrical", "Mechanical", "Civil", "Aerospace", "Biotechnology",
        "Physics", "Mathematics", "Chemistry", "Economics", "Business Admin",
        "English Literature", "Psychology", "History", "Robotics"
    ]
    
    generated_departments = set()
    while len(generated_departments) < 60:
        prog = random.choice(programs)
        disc = random.choice(disciplines)
        generated_departments.add(f"{prog} in {disc}")
    
    generated_departments = list(generated_departments)
    
    first_names = ["Arjun", "Neha", "Rahul", "Priya", "Vikram", "Anjali", "Siddharth", "Pooja", "Rohan", "Sneha", "Aditya", "Kavya", "Karan", "Riya", "Mohit", "Aisha", "Amit", "Meera", "Varun", "Isha", "Ravi", "Kiran", "Samir", "Tara", "Nikhil", "Divya", "Pranav", "Nidhi", "Gaurav", "Shruti"]
    last_names = ["Sharma", "Verma", "Gupta", "Singh", "Patel", "Kumar", "Mishra", "Das", "Bose", "Nair", "Reddy", "Rao", "Iyer", "Joshi", "Chauhan", "Sen", "Yadav", "Malhotra", "Kapoor", "Agarwal", "Bhatt", "Menon", "Pillai", "Chakraborty", "Sengupta", "Banerjee", "Mukherjee", "Chatterjee", "Bhattacharya", "Gosh"]
    
    # Generate 300+ Faculty
    designations = ["Assistant Professor", "Associate Professor", "Professor", "Lecturer"]
    
    for i in range(5, 310):
        dept = random.choice(generated_departments)
        dept_obj, _ = Department.objects.get_or_create(name=dept)
        dept_code = dept_obj.dept_id.lower().replace("-", "") if dept_obj.dept_id else f"d{dept_obj.id}"
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        fac_id = f"FAC-{random.randint(2000,2026)}-{i:04d}"
        username = f"{fname.lower()}.{lname.lower()}.{dept_code}.{i}"
        faculty_data.append({
            "email": f"{username}@smartcampus.edu",
            "username": username,
            "first_name": fname,
            "last_name": lname,
            "employee_id": fac_id,
            "department": dept,
            "designation": random.choice(designations),
        })

    faculty_objects = []
    for fd in faculty_data:
        user, created = User.objects.get_or_create(
            email=fd["email"],
            defaults={
                "username": fd["username"],
                "first_name": fd["first_name"],
                "last_name": fd["last_name"],
                "role": "faculty",
            },
        )
        faculty_password = os.environ.get("SEED_FACULTY_PASSWORD", "faculty123")
        user.set_password(faculty_password)
        user.save()

        dept_obj, _ = Department.objects.get_or_create(name=fd["department"])
        faculty, _ = Faculty.objects.get_or_create(
            user=user,
            defaults={
                "employee_id": fd["employee_id"],
                "department": dept_obj,
                "designation": fd["designation"],
            },
        )
        faculty_objects.append(faculty)
        print(f"[OK] Faculty: {fd['first_name']} {fd['last_name']} ({fd['employee_id']})")

    # ── Students ────────────────────────────────────────────────────
    student_data = [
        {
            "email": "alice.brown.dep0009.y1.11@smartcampus.edu",
            "username": "alice.brown.dep0009.y1.11",
            "first_name": "Alice",
            "last_name": "Brown",
            "enrollment_number": "STU-2026-00011",
            "department": "Computer Science",
            "semester": 1,
        },
        {
            "email": "bob.taylor.dep0009.y3.31698@smartcampus.edu",
            "username": "bob.taylor.dep0009.y3.31698",
            "first_name": "Bob",
            "last_name": "Taylor",
            "enrollment_number": "STU-2026-31698",
            "department": "Computer Science",
            "semester": 5,
        },
        {
            "email": "charlie.lee.dep0009.y2.31699@smartcampus.edu",
            "username": "charlie.lee.dep0009.y2.31699",
            "first_name": "Charlie",
            "last_name": "Lee",
            "enrollment_number": "STU-2026-31699",
            "department": "Computer Science",
            "semester": 3,
        },
        {
            "email": "diana.patel.dep0010.y3.31700@smartcampus.edu",
            "username": "diana.patel.dep0010.y3.31700",
            "first_name": "Diana",
            "last_name": "Patel",
            "enrollment_number": "STU-2026-31700",
            "department": "Electronics",
            "semester": 5,
        },
        {
            "email": "ethan.kim.dep0010.y2.5@smartcampus.edu",
            "username": "ethan.kim.dep0010.y2.5",
            "first_name": "Ethan",
            "last_name": "Kim",
            "enrollment_number": "STU-2026-00005",
            "department": "Mathematics",
            "semester": 3,
        },
        {
            "email": "fatima.zahra.dep0033.y3.6@smartcampus.edu",
            "username": "fatima.zahra.dep0033.y3.6",
            "first_name": "Fatima",
            "last_name": "Zahra",
            "enrollment_number": "STU-2026-00006",
            "department": "Computer Science",
            "semester": 5,
        },
        {
            "email": "gabriel.silva.dep0010.y2.7@smartcampus.edu",
            "username": "gabriel.silva.dep0010.y2.7",
            "first_name": "Gabriel",
            "last_name": "Silva",
            "enrollment_number": "STU-2026-00007",
            "department": "Electronics",
            "semester": 3,
        },
        {
            "email": "haruki.murakami.dep0009.y1.8@smartcampus.edu",
            "username": "haruki.murakami.dep0009.y1.8",
            "first_name": "Haruki",
            "last_name": "Murakami",
            "enrollment_number": "STU-2026-00008",
            "department": "Computer Science",
            "semester": 1,
        },
        {
            "email": "isabella.martinez.dep0009.y4.9@smartcampus.edu",
            "username": "isabella.martinez.dep0009.y4.9",
            "first_name": "Isabella",
            "last_name": "Martinez",
            "enrollment_number": "STU-2026-00009",
            "department": "Mathematics",
            "semester": 7,
        },
        {
            "email": "jamal.jackson.dep0039.y3.10@smartcampus.edu",
            "username": "jamal.jackson.dep0039.y3.10",
            "first_name": "Jamal",
            "last_name": "Jackson",
            "enrollment_number": "STU-2026-00010",
            "department": "Computer Science",
            "semester": 5,
        },
    ]

    # Generate 3000+ Students
    semesters = [1, 2, 3, 4, 5, 6, 7, 8]
    
    for i in range(11, 3050):
        dept = random.choice(generated_departments)
        dept_obj, _ = Department.objects.get_or_create(name=dept)
        dept_code = dept_obj.dept_id.lower().replace("-", "") if dept_obj.dept_id else f"d{dept_obj.id}"
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        stu_id = f"STU-{random.choice([2023, 2024, 2025, 2026])}-{i:05d}"
        sem = random.choice(semesters)
        yr = max(1, (sem + 1) // 2)
        username = f"{fname.lower()}.{lname.lower()}.{dept_code}.y{yr}.{i}"
        student_data.append({
            "email": f"{username}@smartcampus.edu",
            "username": username,
            "first_name": fname,
            "last_name": lname,
            "enrollment_number": stu_id,
            "department": dept,
            "semester": sem,
        })

    for sd in student_data:
        user, created = User.objects.get_or_create(
            email=sd["email"],
            defaults={
                "username": sd["username"],
                "first_name": sd["first_name"],
                "last_name": sd["last_name"],
                "role": "student",
            },
        )
        student_password = os.environ.get("SEED_STUDENT_PASSWORD", "student123")
        user.set_password(student_password)
        user.save()

        dept_obj, _ = Department.objects.get_or_create(name=sd["department"])
        try:
            Student.objects.get_or_create(
                user=user,
                defaults={
                    "enrollment_number": sd["enrollment_number"],
                    "department": dept_obj,
                    "semester": sd["semester"],
                },
            )
        except Exception as e:
            print(f"Skipping student {sd['enrollment_number']}: {e}")
        print(
            f"[OK] Student: {sd['first_name']} {sd['last_name']} ({sd['enrollment_number']})"
        )

    # ── Rooms ───────────────────────────────────────────────────────
    rooms_data = [
        {
            "room_number": "LH-101",
            "capacity": 60,
            "building": "Main Block",
            "room_type": "lecture",
        },
        {
            "room_number": "LH-102",
            "capacity": 60,
            "building": "Main Block",
            "room_type": "lecture",
        },
        {
            "room_number": "LH-201",
            "capacity": 40,
            "building": "Main Block",
            "room_type": "lecture",
        },
        {
            "room_number": "LAB-301",
            "capacity": 30,
            "building": "CS Block",
            "room_type": "lab",
        },
        {
            "room_number": "LAB-302",
            "capacity": 30,
            "building": "CS Block",
            "room_type": "lab",
        },
        {
            "room_number": "SR-101",
            "capacity": 20,
            "building": "Annex",
            "room_type": "seminar",
        },
    ]

    for rd in rooms_data:
        Room.objects.get_or_create(
            room_number=rd["room_number"],
            defaults=rd,
        )
        print(f"[OK] Room: {rd['room_number']} ({rd['building']}, cap: {rd['capacity']})")

    # ── Time Slots ──────────────────────────────────────────────────
    # 8 periods per day: 4 morning (9 AM – 1 PM) + 4 afternoon (2 PM – 6 PM)
    slot_times = [
        (time(9, 0), time(10, 0)),  # Period 1
        (time(10, 0), time(11, 0)),  # Period 2
        (time(11, 0), time(12, 0)),  # Period 3
        (time(12, 0), time(13, 0)),  # Period 4
        # ── Lunch Break 1:00 PM – 2:00 PM ──
        (time(14, 0), time(15, 0)),  # Period 5
        (time(15, 0), time(16, 0)),  # Period 6
        (time(16, 0), time(17, 0)),  # Period 7
        (time(17, 0), time(18, 0)),  # Period 8
    ]

    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]

    for day in days:
        for start, end in slot_times:
            TimeSlot.objects.get_or_create(
                day=day,
                start_time=start,
                end_time=end,
            )

    print(
        f"[OK] Time slots: {len(days)} days × {len(slot_times)} periods = {len(days)*len(slot_times)} total"
    )

    # ── Subjects ────────────────────────────────────────────────────
    subjects_data = [
        {
            "code": "CS301",
            "name": "Data Structures & Algorithms",
            "faculty": faculty_objects[0],
            "credits": 4,
            "required_capacity": 40,
            "sessions_per_week": 3,
        },
        {
            "code": "CS302",
            "name": "Database Management Systems",
            "faculty": faculty_objects[1],
            "credits": 3,
            "required_capacity": 40,
            "sessions_per_week": 3,
        },
        {
            "code": "CS303",
            "name": "Computer Networks",
            "faculty": faculty_objects[0],
            "credits": 3,
            "required_capacity": 40,
            "sessions_per_week": 2,
        },
        {
            "code": "MA201",
            "name": "Discrete Mathematics",
            "faculty": faculty_objects[2],
            "credits": 3,
            "required_capacity": 60,
            "sessions_per_week": 3,
        },
        {
            "code": "EC201",
            "name": "Digital Electronics",
            "faculty": faculty_objects[3],
            "credits": 4,
            "required_capacity": 40,
            "sessions_per_week": 3,
        },
        {
            "code": "CS304",
            "name": "Artificial Intelligence",
            "faculty": faculty_objects[1],
            "credits": 3,
            "required_capacity": 30,
            "sessions_per_week": 2,
        },
    ]

    for sd in subjects_data:
        Subject.objects.get_or_create(
            code=sd["code"],
            defaults=sd,
        )
        print(f"[OK] Subject: {sd['code']} — {sd['name']}")

    # ── Sample Notices ──────────────────────────────────────────────
    notices_data = [
        {
            "title": "Mid-Semester Examination Schedule Released",
            "content": "The mid-semester examination schedule for all departments has been released. Please check the timetable section for your exam dates and timings. All students are requested to carry their ID cards to the examination hall.",
            "priority": "high",
            "target_audience": "all",
        },
        {
            "title": "Campus Wi-Fi Maintenance — Weekend Downtime",
            "content": "The campus Wi-Fi network will undergo scheduled maintenance this Saturday from 10:00 PM to Sunday 6:00 AM. Please plan your work accordingly.",
            "priority": "medium",
            "target_audience": "all",
        },
        {
            "title": "Workshop on Machine Learning — Register Now",
            "content": 'The Computer Science department is organizing a two-day workshop on "Practical Machine Learning with Python" on May 20-21. Registration is open for all CS students. Limited seats available.',
            "priority": "low",
            "target_audience": "students",
        },
        {
            "title": "Campus Placement Drive 2026",
            "content": "Top tier tech companies including Google, Microsoft, and Amazon are visiting our campus for the placement drive next month. Final year students please update your resumes in the placement portal.",
            "priority": "urgent",
            "target_audience": "students",
        },
        {
            "title": "Faculty Development Program",
            "content": 'A mandatory faculty development program on "AI in Education" will be held next Friday in the main auditorium. Please ensure your classes are rescheduled.',
            "priority": "medium",
            "target_audience": "faculty",
        },
        {
            "title": 'Annual Tech Fest "Innovate 2026"',
            "content": "Get ready for the biggest technical festival of the year! Call for project submissions is now open. Exciting cash prizes to be won.",
            "priority": "low",
            "target_audience": "all",
        },
    ]

    for nd in notices_data:
        Notice.objects.get_or_create(
            title=nd["title"],
            defaults={**nd, "posted_by": admin_user},
        )
        print(f"[OK] Notice: {nd['title'][:50]}...")

    # ── Attendance Records ──────────────────────────────────────────
    print("\n[OK] Seeding attendance records...")

    random.seed(42)  # Deterministic for reproducibility

    students = list(Student.objects.all())
    subjects = list(Subject.objects.all())
    today = date.today()

    # Map subjects to the days they have classes (simulate a timetable)
    subject_class_days = {
        "CS301": [0, 2, 4],  # Mon, Wed, Fri
        "CS302": [1, 3, 4],  # Tue, Thu, Fri
        "CS303": [0, 3],  # Mon, Thu
        "MA201": [1, 2, 4],  # Tue, Wed, Fri
        "EC201": [0, 2, 3],  # Mon, Wed, Thu
        "CS304": [1, 3],  # Tue, Thu
    }

    # Per-student attendance tendency (some students attend more regularly)
    student_attendance_rate = {
        "STU001": 0.92,  # Alice — very regular
        "STU002": 0.78,  # Bob — decent
        "STU003": 0.65,  # Charlie — struggles
        "STU004": 0.88,  # Diana — good
        "STU005": 0.72,  # Ethan — average
        "STU006": 0.98,  # Fatima — near perfect
        "STU007": 0.45,  # Gabriel — severe attendance shortage
        "STU008": 0.85,  # Haruki — good
        "STU009": 0.95,  # Isabella — excellent
        "STU010": 0.30,  # Jamal — failing attendance
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
                rate = student_attendance_rate.get(student.enrollment_number, 0.80)
                is_present = random.random() < rate
                method = random.choice(
                    [
                        "face_recognition",
                        "face_recognition",
                        "face_recognition",
                        "manual",
                    ]  # 75% face recog
                )

                obj, created = Attendance.objects.get_or_create(
                    student=student,
                    subject=subj,
                    date=current_date,
                    defaults={
                        "status": "present" if is_present else "absent",
                        "method": method,
                    },
                )
                if created:
                    attendance_count += 1

    print(f"[OK] Attendance records created: {attendance_count}")

    # Print per-student summary
    for student in students:
        total = Attendance.objects.filter(student=student).count()
        present = Attendance.objects.filter(student=student, status="present").count()
        pct = (present / total * 100) if total else 0
        print(
            f"  [Summary] {student.user.first_name} {student.user.last_name}: "
            f"{present}/{total} present ({pct:.0f}%)"
        )

    print("\nDatabase seeding complete!")


if __name__ == "__main__":
    seed()

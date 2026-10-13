"""
Seed script to ingest MAKAUT AICTE UG syllabus courses from aicteugdetails.html
across departments and semesters 1 to 8.
"""

import os
import sys
import json
import re
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.models import Department, Subject
from apps.accounts.models import Faculty


COLOR_PALETTES = {
    "comp": ["#2563eb", "#3b82f6", "#4f46e5", "#6366f1", "#7c3aed", "#8b5cf6", "#ec4899"],
    "elec": ["#d97706", "#f59e0b", "#ea580c", "#f97316", "#eab308", "#ca8a04"],
    "mech": ["#dc2626", "#ef4444", "#b91c1c", "#991b1b", "#c2410c", "#ea580c"],
    "civil": ["#059669", "#10b981", "#047857", "#0d9488", "#14b8a6", "#0f766e"],
    "bio": ["#0891b2", "#06b6d4", "#0284c7", "#65a30d", "#84cc16", "#16a34a"],
    "text": ["#9333ea", "#a855f7", "#c026d3", "#d946ef", "#db2777"],
    "default": ["#475569", "#64748b", "#334155", "#1e293b"]
}

def get_color_for_subject(code, dept_name):
    d_lower = dept_name.lower()
    c_lower = code.lower()
    if any(k in d_lower for k in ["computer", "information", "artificial", "data", "cyber", "internet"]):
        colors = COLOR_PALETTES["comp"]
    elif any(k in d_lower for k in ["electronics", "electrical"]):
        colors = COLOR_PALETTES["elec"]
    elif any(k in d_lower for k in ["mechanical", "automobile", "robotics"]):
        colors = COLOR_PALETTES["mech"]
    elif any(k in d_lower for k in ["civil", "environmental"]):
        colors = COLOR_PALETTES["civil"]
    elif any(k in d_lower for k in ["biotechnology", "chemical", "food", "biomedical"]):
        colors = COLOR_PALETTES["bio"]
    elif any(k in d_lower for k in ["textile", "apparel", "leather"]):
        colors = COLOR_PALETTES["text"]
    else:
        colors = COLOR_PALETTES["default"]
    
    # Hash code for stable color
    idx = sum(ord(c) for c in code) % len(colors)
    return colors[idx]


def clean_title(title):
    # Remove weird characters and noise
    title = re.sub(r'[\ufffd\u2013\u2014]', '-', title)
    title = re.sub(r'\s+', ' ', title).strip(' .,-:')
    title = re.sub(r'^\)\s*', '', title)
    return title


def is_valid_course(c):
    code = c.get("code", "")
    name = c.get("name", "")
    if len(code) < 3 or len(name) < 3:
        return False
    if not any(char.isdigit() for char in code):
        return False
    if any(k in name.lower() for k in ["curriculum structure", "academic session", "applicable from", "page 1 of", "table of contents"]):
        return False
    return True


def run_seed():
    json_path = os.path.join(os.path.dirname(__file__), "scratch", "all_courses.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist!")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Loaded syllabus data for {len(catalog)} departments.")

    created_subjects = 0
    updated_subjects = 0
    dept_mappings_count = 0

    # Ensure all departments exist and map them
    for dept_name, courses in catalog.items():
        dept, _ = Department.objects.get_or_create(
            name=dept_name,
            defaults={
                "program_type": "B.Tech",
                "core_department": "Engineering & Technology",
                "no_of_years": 4,
            }
        )
        if not dept.program_type:
            dept.program_type = "B.Tech"
            dept.save()

        # Find potential faculty
        faculty_member = Faculty.objects.filter(department=dept).first()
        if not faculty_member:
            parts = [p for p in dept.name.split() if len(p) > 3]
            for p in parts[:2]:
                faculty_member = Faculty.objects.filter(department__name__icontains=p).first()
                if faculty_member:
                    break
        if not faculty_member:
            faculty_member = Faculty.objects.first()

        for c in courses:
            if not is_valid_course(c):
                continue

            raw_code = c["code"][:20]  # Respect max_length=20
            name = clean_title(c["name"])[:200]
            semester = int(c.get("semester", 1))
            credits = float(c.get("credits", 3.0))
            subject_type = c.get("subject_type", "lecture")
            sessions = int(c.get("sessions_per_week", 3))

            color_code = get_color_for_subject(raw_code, dept.name)
            req_cap = 30 if subject_type == "lab" else 60

            subject, created = Subject.objects.get_or_create(
                code=raw_code,
                defaults={
                    "name": name,
                    "semester": semester,
                    "credits": credits,
                    "subject_type": subject_type,
                    "sessions_per_week": sessions,
                    "required_capacity": req_cap,
                    "color_code": color_code,
                    "faculty": faculty_member,
                }
            )

            # If already existed, update semester/credits if default or missing
            if not created:
                changed = False
                if not subject.semester or subject.semester != semester:
                    subject.semester = semester
                    changed = True
                if subject.credits != credits:
                    subject.credits = credits
                    changed = True
                if changed:
                    subject.save()
                updated_subjects += 1
            else:
                created_subjects += 1

            # Associate department
            subject.departments.add(dept)
            dept_mappings_count += 1

    print("\n" + "="*50)
    print("MAKAUT AICTE UG INGESTION SUMMARY:")
    print(f"  Created new subjects: {created_subjects}")
    print(f"  Updated existing subjects: {updated_subjects}")
    print(f"  Total department-subject relationships created: {dept_mappings_count}")
    print(f"  Total Subjects now in DB: {Subject.objects.count()}")
    print("="*50)


if __name__ == "__main__":
    run_seed()

"""
Comprehensive Seeder for MAKAUT AICTE UG Syllabus and Course Curriculum.
Ingests courses across 37+ academic departments and semesters 1 to 8 (up to 10 for B.Arch)
from makautexam.net/aicte_details/aicteugdetails.html.
"""

import os
import sys
import json
import re
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from apps.scheduler.models import Department, Subject
from apps.accounts.models import Faculty


COLOR_PALETTES = {
    "comp": ["#2563eb", "#3b82f6", "#4f46e5", "#6366f1", "#7c3aed", "#8b5cf6", "#ec4899"],
    "elec": ["#d97706", "#f59e0b", "#ea580c", "#f97316", "#eab308", "#ca8a04"],
    "mech": ["#dc2626", "#ef4444", "#b91c1c", "#991b1b", "#c2410c", "#ea580c"],
    "civil": ["#059669", "#10b981", "#047857", "#0d9488", "#14b8a6", "#0f766e"],
    "bio": ["#0891b2", "#06b6d4", "#0284c7", "#65a30d", "#84cc16", "#16a34a"],
    "mgmt": ["#0284c7", "#0369a1", "#075985", "#0e7490", "#155e75"],
    "arch": ["#b45309", "#92400e", "#78350f", "#854d0e"],
    "pharm": ["#047857", "#065f46", "#064e3b", "#115e59"],
    "default": ["#475569", "#64748b", "#334155", "#1e293b"]
}


def get_color_for_subject(code, dept_name):
    d_lower = dept_name.lower()
    if any(k in d_lower for k in ["computer", "information", "artificial", "data", "cyber", "internet", "bca"]):
        colors = COLOR_PALETTES["comp"]
    elif any(k in d_lower for k in ["electronics", "electrical"]):
        colors = COLOR_PALETTES["elec"]
    elif any(k in d_lower for k in ["mechanical", "automobile", "robotics"]):
        colors = COLOR_PALETTES["mech"]
    elif any(k in d_lower for k in ["civil", "environmental"]):
        colors = COLOR_PALETTES["civil"]
    elif any(k in d_lower for k in ["biotechnology", "chemical", "food", "biomedical"]):
        colors = COLOR_PALETTES["bio"]
    elif any(k in d_lower for k in ["business", "bba", "management", "hotel"]):
        colors = COLOR_PALETTES["mgmt"]
    elif any(k in d_lower for k in ["architecture", "arch"]):
        colors = COLOR_PALETTES["arch"]
    elif any(k in d_lower for k in ["pharmacy", "pharm"]):
        colors = COLOR_PALETTES["pharm"]
    else:
        colors = COLOR_PALETTES["default"]

    idx = sum(ord(c) for c in code) % len(colors)
    return colors[idx]


def clean_course_name(name):
    name = re.sub(r'[\ufffd\u2013\u2014]', '-', name)
    name = re.sub(r'\s+', ' ', name).strip(' .,-:')
    name = re.sub(r'^\)\s*', '', name)
    # Remove leading numbering like "1.", "2 "
    name = re.sub(r'^[0-9]+[\.\)]\s*', '', name)
    return name


# Standard 1st Year B.Tech foundation courses for MAKAUT (applicable to all B.Tech streams)
BTECH_COMMON_YEAR1 = [
    # Semester 1
    {"code": "BS-PH101", "name": "Physics-I", "semester": 1, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "BS-CH101", "name": "Chemistry-I", "semester": 1, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "BS-M101", "name": "Mathematics - IA (Calculus & Linear Algebra)", "semester": 1, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "ES-EE101", "name": "Basic Electrical Engineering", "semester": 1, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "BS-PH191", "name": "Physics-I Laboratory", "semester": 1, "credits": 1.5, "subject_type": "lab", "sessions_per_week": 2},
    {"code": "BS-CH191", "name": "Chemistry-I Laboratory", "semester": 1, "credits": 1.5, "subject_type": "lab", "sessions_per_week": 2},
    {"code": "ES-EE191", "name": "Basic Electrical Engineering Laboratory", "semester": 1, "credits": 1.0, "subject_type": "lab", "sessions_per_week": 2},
    {"code": "ES-ME191", "name": "Engineering Graphics & Design", "semester": 1, "credits": 3.0, "subject_type": "lab", "sessions_per_week": 4},
    {"code": "ES-ME192", "name": "Workshop / Manufacturing Practices", "semester": 1, "credits": 3.0, "subject_type": "lab", "sessions_per_week": 4},

    # Semester 2
    {"code": "BS-PH201", "name": "Physics-II", "semester": 2, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "BS-CH201", "name": "Chemistry-II", "semester": 2, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "BS-M201", "name": "Mathematics - IIA (Differential Equations & Complex Variables)", "semester": 2, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "ES-CS201", "name": "Programming for Problem Solving", "semester": 2, "credits": 4.0, "subject_type": "lecture", "sessions_per_week": 4},
    {"code": "HM-HU201", "name": "English", "semester": 2, "credits": 2.0, "subject_type": "lecture", "sessions_per_week": 2},
    {"code": "BS-PH291", "name": "Physics-II Laboratory", "semester": 2, "credits": 1.5, "subject_type": "lab", "sessions_per_week": 2},
    {"code": "ES-CS291", "name": "Programming for Problem Solving Laboratory", "semester": 2, "credits": 1.5, "subject_type": "lab", "sessions_per_week": 2},
    {"code": "HM-HU291", "name": "Language Laboratory", "semester": 2, "credits": 1.0, "subject_type": "lab", "sessions_per_week": 2},
]


def run_seeder():
    print("=" * 80)
    print("STARTING MAKAUT AICTE UG SYLLABUS SEEDER (ALL DEPARTMENTS & SEMESTERS)")
    print("=" * 80)

    json_path = os.path.join(os.path.dirname(__file__), "scratch", "comprehensive_courses.json")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist!")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Loaded catalog with {len(catalog)} departments.")

    created_subjects_count = 0
    updated_subjects_count = 0
    relationships_count = 0

    with transaction.atomic():
        # First ensure all departments exist and have proper metadata
        dept_obj_map = {}
        for dept_name in catalog.keys():
            prog_type = "B.Tech"
            years = 4
            core = "Engineering & Technology"

            if "architecture" in dept_name.lower():
                prog_type = "B.Arch"
                years = 5
                core = "Architecture & Planning"
            elif "pharmacy" in dept_name.lower():
                prog_type = "B.Pharm"
                years = 4
                core = "Pharmacy"
            elif "business" in dept_name.lower() or "bba" in dept_name.lower():
                prog_type = "BBA"
                years = 4
                core = "Management Studies"
            elif "computer application" in dept_name.lower() or "bca" in dept_name.lower():
                prog_type = "BCA"
                years = 4
                core = "Computer Applications"
            elif "hotel" in dept_name.lower():
                prog_type = "BHMCT"
                years = 4
                core = "Hotel Management & Tourism"

            dept, created = Department.objects.get_or_create(
                name=dept_name,
                defaults={
                    "program_type": prog_type,
                    "core_department": core,
                    "no_of_years": years,
                }
            )
            # Update fields if missing
            changed = False
            if not dept.program_type:
                dept.program_type = prog_type
                changed = True
            if not dept.no_of_years or dept.no_of_years != years:
                dept.no_of_years = years
                changed = True
            if not dept.core_department:
                dept.core_department = core
                changed = True
            if changed:
                dept.save()

            dept_obj_map[dept_name] = dept

        print(f"Verified {len(dept_obj_map)} academic departments in database.")

        # Ingest courses per department
        for dept_name, courses in catalog.items():
            dept = dept_obj_map[dept_name]
            dept_faculty = Faculty.objects.filter(department=dept).first()
            if not dept_faculty:
                dept_faculty = Faculty.objects.first()

            all_dept_courses = list(courses)

            # If it's a B.Tech department, ensure 1st Year common foundation courses are included
            if dept.program_type == "B.Tech":
                existing_sems = set(c.get("semester") for c in all_dept_courses)
                if 1 not in existing_sems or 2 not in existing_sems:
                    for common_c in BTECH_COMMON_YEAR1:
                        if common_c["semester"] not in existing_sems:
                            all_dept_courses.append(common_c)

            print(f"\nProcessing [{dept.dept_id}] {dept.name} ({len(all_dept_courses)} courses)...")

            for c in all_dept_courses:
                raw_code = c["code"][:20].strip()
                name = clean_course_name(c["name"])[:200]
                semester = int(c.get("semester", 1))
                credits = float(c.get("credits", 3.0))
                subject_type = c.get("subject_type", "lecture")
                sessions = int(c.get("sessions_per_week", 3))

                if len(raw_code) < 3 or len(name) < 3:
                    continue

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
                        "faculty": dept_faculty,
                    }
                )

                if created:
                    created_subjects_count += 1
                else:
                    # Sync semester/credits if needed
                    changed = False
                    if not subject.semester or (subject.semester != semester and semester > 1):
                        subject.semester = semester
                        changed = True
                    if subject.credits != credits and credits > 0:
                        subject.credits = credits
                        changed = True
                    if changed:
                        subject.save()
                    updated_subjects_count += 1

                # Link subject to department
                if not subject.departments.filter(id=dept.id).exists():
                    subject.departments.add(dept)
                    relationships_count += 1

        print("\n" + "=" * 80)
        print("SEEDING SUMMARY:")
        print(f"  New subjects created: {created_subjects_count}")
        print(f"  Existing subjects verified/updated: {updated_subjects_count}")
        print(f"  New department-subject relationships linked: {relationships_count}")
        print(f"  Total active subjects in database: {Subject.objects.count()}")
        print("=" * 80)


if __name__ == "__main__":
    run_seeder()

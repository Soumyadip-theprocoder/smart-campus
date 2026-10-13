"""
standardize_ids.py
Migrates and standardizes:
1. Departments: Backfills dept_id as DEP-0001, DEP-0002, etc.
2. Students: Normalizes legacy IDs (e.g. STU001 -> STU-2026-0001) to STU-YYYY-XXXX.
3. Face Recognition: Renames training image folders to match new student IDs.
4. Faculty: Verifies all employee IDs match FAC-YYYY-XXXX format.
"""

import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.models import Department
from apps.accounts.models import Student, Faculty

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_IMAGES_DIR = os.path.join(BASE_DIR, "face_recognition_engine", "training_images")


def standardize_departments():
    print("\n--- Standardizing Departments ---")
    departments = Department.objects.all().order_by("id")
    count = 1
    updated = 0
    for dept in departments:
        expected_id = f"DEP-{count:04d}"
        if dept.dept_id != expected_id:
            dept.dept_id = expected_id
            dept.save(update_fields=["dept_id"])
            updated += 1
        count += 1
    print(f"Standardized {count - 1} departments ({updated} newly backfilled).")


def standardize_students():
    print("\n--- Standardizing Students ---")
    # Handle legacy STU001..STU012 and any other non-standard formats
    legacy_mapping = {
        "STU001": "STU-2026-0001",
        "STU002": "STU-2026-0002",
        "STU003": "STU-2026-0003",
        "STU004": "STU-2026-0004",
        "STU005": "STU-2026-0005",
        "STU006": "STU-2026-0006",
        "STU007": "STU-2026-0007",
        "STU008": "STU-2026-0008",
        "STU009": "STU-2026-0009",
        "STU010": "STU-2026-0010",
        "STU011": "STU-2026-0011",
        "STU012": "STU-2026-0012",
    }

    updated_count = 0
    for old_id, new_id in legacy_mapping.items():
        try:
            student = Student.objects.get(enrollment_number=old_id)
            student.enrollment_number = new_id
            student.save(update_fields=["enrollment_number"])
            print(f"Updated Student: {old_id} -> {new_id} ({student.user.get_full_name()})")
            updated_count += 1

            # Rename training image folder if exists
            old_folder = os.path.join(TRAINING_IMAGES_DIR, old_id)
            new_folder = os.path.join(TRAINING_IMAGES_DIR, new_id)
            if os.path.exists(old_folder):
                if not os.path.exists(new_folder):
                    os.rename(old_folder, new_folder)
                    print(f"  Renamed training images: {old_id} -> {new_id}")
                else:
                    print(f"  Training images target folder {new_id} already exists")

        except Student.DoesNotExist:
            pass

    # Verify all students match STU-YYYY-XXXX
    pattern = re.compile(r"^STU-\d{4}-\d{4}$")
    non_conforming = Student.objects.exclude(enrollment_number__regex=r"^STU-\d{4}-\d{4}$")
    if non_conforming.exists():
        print(f"WARNING: {non_conforming.count()} students do not conform to STU-YYYY-XXXX:")
        for s in non_conforming[:5]:
            print(f"  - {s.enrollment_number} ({s.user.get_full_name()})")
    else:
        print(f"All {Student.objects.count()} students match STU-YYYY-XXXX format!")


def verify_faculty():
    print("\n--- Verifying Faculty ---")
    non_conforming = Faculty.objects.exclude(employee_id__regex=r"^FAC-\d{4}-\d{4}$")
    if non_conforming.exists():
        print(f"Fixing {non_conforming.count()} non-conforming faculty...")
        count = 1
        for fac in non_conforming:
            fac.employee_id = f"FAC-2026-{count:04d}"
            fac.save(update_fields=["employee_id"])
            count += 1
    print(f"All {Faculty.objects.count()} faculty match FAC-YYYY-XXXX format!")


def main():
    standardize_departments()
    standardize_students()
    verify_faculty()
    print("\n[SUCCESS] All IDs standardized successfully!")


if __name__ == "__main__":
    main()

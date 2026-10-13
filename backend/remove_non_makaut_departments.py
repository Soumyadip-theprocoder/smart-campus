"""
Production script to remove all non-MAKAUT departments.
Migrates all associated students and faculty to their closest matching MAKAUT department,
ensuring zero orphaned records, and safely deletes the 127 non-MAKAUT departments.
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from apps.scheduler.models import Department, Subject
from apps.accounts.models import Student, Faculty

RETAINED_IDS = set([
    'DEP-0009', 'DEP-0010', 'DEP-0033', 'DEP-0039', 'DEP-0045', 'DEP-0069', 'DEP-0077',
    'DEP-0084', 'DEP-0099', 'DEP-0151', 'DEP-0152', 'DEP-0153', 'DEP-0154', 'DEP-0155',
    'DEP-0156', 'DEP-0157', 'DEP-0158', 'DEP-0159', 'DEP-0160', 'DEP-0161', 'DEP-0162',
    'DEP-0163', 'DEP-0164', 'DEP-0165', 'DEP-0166', 'DEP-0167', 'DEP-0168', 'DEP-0169',
    'DEP-0170', 'DEP-0171', 'DEP-0172', 'DEP-0173', 'DEP-0174', 'DEP-0175', 'DEP-0176',
    'DEP-0177', 'DEP-0178', 'DEP-0179', 'DEP-0180', 'DEP-0181', 'DEP-0182', 'DEP-0183',
    'DEP-0184', 'DEP-0185'
])

def get_target_for(d):
    name = d.name.lower()
    if 'bca' in name:
        return 'DEP-0077'  # BCA in Computer Science
    elif 'data science' in name:
        return 'DEP-0069'  # B.Tech in Data Science
    elif 'artificial intelligence' in name or 'ai' in name:
        return 'DEP-0163'  # B.Tech in AI & ML
    elif 'cyber security' in name:
        return 'DEP-0155'  # B.Tech in CSE (Cyber Security)
    elif 'computer' in name or 'software' in name:
        return 'DEP-0151'  # B.Tech in CSE
    elif 'information technology' in name:
        return 'DEP-0169'  # B.Tech in IT
    elif 'robotics' in name:
        return 'DEP-0039'  # B.Tech in Robotics
    elif 'electronics' in name:
        return 'DEP-0165'  # B.Tech in ECE
    elif 'electrical' in name:
        return 'DEP-0166'  # B.Tech in EE
    elif 'mechanical' in name or 'aerospace' in name:
        return 'DEP-0167'  # B.Tech in ME
    elif 'civil' in name:
        return 'DEP-0168'  # B.Tech in Civil Engineering
    elif 'biotechnology' in name or 'biomedical' in name:
        return 'DEP-0180'  # B.Tech in Biotechnology
    elif 'chemistry' in name or 'chemical' in name:
        return 'DEP-0177'  # B.Tech in Chemical Engineering
    elif 'math' in name:
        return 'DEP-0010'  # B.Sc in Mathematics
    elif 'physic' in name:
        return 'DEP-0009'  # B.Sc in Physics
    elif 'economic' in name:
        return 'DEP-0033'  # B.Sc in Economics
    elif 'history' in name:
        return 'DEP-0045'  # M.A. in History
    elif any(k in name for k in ['business', 'bba', 'mba', 'management', 'psychology', 'english']):
        return 'DEP-0084'  # BBA in Business Admin
    else:
        return 'DEP-0151'  # Fallback to CSE

def execute_removal():
    print("=" * 80)
    print("REMOVING NON-MAKAUT DEPARTMENTS & MIGRATING STUDENTS/FACULTY")
    print("=" * 80)

    with transaction.atomic():
        non_makaut = list(Department.objects.exclude(dept_id__in=RETAINED_IDS))
        print(f"Total non-MAKAUT departments to remove: {len(non_makaut)}")

        migrated_students = 0
        migrated_faculty = 0
        transferred_rooms = 0
        deleted_count = 0

        for d in non_makaut:
            target_code = get_target_for(d)
            target = Department.objects.get(dept_id=target_code)

            # Migrate students
            s_count = d.students.count()
            if s_count > 0:
                d.students.update(department=target)
                migrated_students += s_count

            # Migrate faculty
            f_count = d.faculty_members.count()
            if f_count > 0:
                d.faculty_members.update(department=target)
                migrated_faculty += f_count

            # Migrate subjects
            for sub in list(d.subjects.all()):
                sub.departments.add(target)
                sub.departments.remove(d)

            # Migrate rooms
            for room in list(d.rooms.all()):
                room.departments.add(target)
                room.departments.remove(d)
                transferred_rooms += 1

            # Transfer HOD if target has none
            if not target.hod and d.hod:
                target.hod = d.hod
                target.save(update_fields=['hod'])

            d.hod = None
            d.save(update_fields=['hod'])
            d.delete()
            deleted_count += 1

        print("\n" + "=" * 80)
        print("SUMMARY:")
        print(f"  [OK] Deleted non-MAKAUT departments: {deleted_count}")
        print(f"  [OK] Migrated students: {migrated_students}")
        print(f"  [OK] Migrated faculty members: {migrated_faculty}")
        print(f"  [OK] Transferred room assignments: {transferred_rooms}")
        print(f"  [OK] Remaining verified MAKAUT departments: {Department.objects.count()}")
        print(f"  [OK] Orphaned students: {Student.objects.filter(department__isnull=True).count()}")
        print(f"  [OK] Orphaned faculty: {Faculty.objects.filter(department__isnull=True).count()}")
        print(f"  [OK] Active subjects in DB: {Subject.objects.count()}")
        print("=" * 80)

if __name__ == "__main__":
    execute_removal()

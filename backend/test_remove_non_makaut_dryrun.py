import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from apps.scheduler.models import Department
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
        return 'DEP-0077'
    elif 'data science' in name:
        return 'DEP-0069'
    elif 'artificial intelligence' in name or 'ai' in name:
        return 'DEP-0163'
    elif 'cyber security' in name:
        return 'DEP-0155'
    elif 'computer' in name or 'software' in name:
        return 'DEP-0151'
    elif 'information technology' in name:
        return 'DEP-0169'
    elif 'robotics' in name:
        return 'DEP-0039'
    elif 'electronics' in name:
        return 'DEP-0165'
    elif 'electrical' in name:
        return 'DEP-0166'
    elif 'mechanical' in name or 'aerospace' in name:
        return 'DEP-0167'
    elif 'civil' in name:
        return 'DEP-0168'
    elif 'biotechnology' in name or 'biomedical' in name:
        return 'DEP-0180'
    elif 'chemistry' in name or 'chemical' in name:
        return 'DEP-0177'
    elif 'math' in name:
        return 'DEP-0010'
    elif 'physic' in name:
        return 'DEP-0009'
    elif 'economic' in name:
        return 'DEP-0033'
    elif 'history' in name:
        return 'DEP-0045'
    elif any(k in name for k in ['business', 'bba', 'mba', 'management', 'psychology', 'english']):
        return 'DEP-0084'
    else:
        return 'DEP-0151'

def dry_run():
    print("Testing migration & removal inside atomic transaction (with rollback)...")
    with transaction.atomic():
        non_makaut = list(Department.objects.exclude(dept_id__in=RETAINED_IDS))
        print(f"Total non-MAKAUT departments to process: {len(non_makaut)}")

        migrated_students = 0
        migrated_faculty = 0

        for d in non_makaut:
            target_code = get_target_for(d)
            target = Department.objects.get(dept_id=target_code)

            # Migrate students
            stu_cnt = d.students.count()
            d.students.update(department=target)
            migrated_students += stu_cnt

            # Migrate faculty
            fac_cnt = d.faculty_members.count()
            d.faculty_members.update(department=target)
            migrated_faculty += fac_cnt

            # Migrate subjects
            for sub in list(d.subjects.all()):
                sub.departments.add(target)
                sub.departments.remove(d)

            # Migrate rooms
            for room in list(d.rooms.all()):
                room.departments.add(target)
                room.departments.remove(d)

            # Transfer HOD if target has none
            if not target.hod and d.hod:
                target.hod = d.hod
                target.save(update_fields=['hod'])

            d.hod = None
            d.save(update_fields=['hod'])
            d.delete()

        remaining_depts = Department.objects.count()
        orphaned_students = Student.objects.filter(department__isnull=True).count()
        orphaned_faculty = Faculty.objects.filter(department__isnull=True).count()

        print(f"Dry run complete!")
        print(f"  - Migrated students: {migrated_students}")
        print(f"  - Migrated faculty: {migrated_faculty}")
        print(f"  - Remaining departments in DB: {remaining_depts}")
        print(f"  - Orphaned students: {orphaned_students}")
        print(f"  - Orphaned faculty: {orphaned_faculty}")

        transaction.set_rollback(True)
        print("Dry run succeeded! Transaction successfully rolled back.")

if __name__ == "__main__":
    dry_run()

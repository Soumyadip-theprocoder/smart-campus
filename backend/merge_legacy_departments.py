"""
Script to merge legacy placeholder departments (DEP-0001 to DEP-0012 and requested duplicates)
into target departments based on user confirmation.

Mappings:
1. DEP-0001 (Computer Science), DEP-0004 (Computer Science & Engineering), DEP-0050 (B.Tech in Computer Science)
   -> DEP-0151 (B.Tech in Computer Science & Engineering)

2. DEP-0002 (Electronics), DEP-0020 (B.Tech in Electronics)
   -> DEP-0165 (B.Tech in Electronics & Communication Engineering)

3. DEP-0009 (Physics & Astrophysics)
   -> Keep & configure as B.Sc in Physics (program_type='B.Sc', core_department='Physics').
   (Delete empty placeholder DEP-0096 to prevent name collision).

4. DEP-0010 (Pure Mathematics)
   -> Configure as B.Sc in Mathematics (program_type='B.Sc', core_department='Mathematics', remove 'Pure').
   Merge DEP-0003 (Mathematics) into DEP-0010.

5. DEP-0005 (Electrical Engineering), DEP-0031 (B.Tech in Electrical)
   -> DEP-0166 (B.Tech in Electrical Engineering)

6. DEP-0006 (Mechanical Engineering)
   -> DEP-0167 (B.Tech in Mechanical Engineering)

7. DEP-0007 (Business Administration), DEP-0008 (Management Studies)
   -> DEP-0084 (BBA in Business Admin)

8. DEP-0011 (History)
   -> DEP-0045 (M.A. in History)

9. DEP-0012 (Economics)
   -> DEP-0033 (B.Sc in Economics)
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import transaction
from apps.scheduler.models import Department
from apps.accounts.models import Student, Faculty


def merge_departments():
    print("=" * 80)
    print("STARTING DEPARTMENT MERGE & NORMALIZATION PROCESS")
    print("=" * 80)

    with transaction.atomic():
        # Step 1: Resolve B.Sc in Physics conflict and configure DEP-0009
        print("\n[Step 1] Configuring DEP-0009 as B.Sc in Physics...")
        d96 = Department.objects.filter(dept_id="DEP-0096").first()
        if d96:
            print(f"  - Removing empty duplicate record {d96.dept_id}: '{d96.name}' (id={d96.id})")
            d96.delete()

        d9 = Department.objects.get(dept_id="DEP-0009")
        d9.name = "B.Sc in Physics"
        d9.program_type = "B.Sc"
        d9.core_department = "Physics"
        d9.no_of_years = 4
        d9.save()
        print(f"  [OK] Updated {d9.dept_id} -> Name: '{d9.name}', Program: '{d9.program_type}'")

        # Step 2: Configure DEP-0010 as B.Sc in Mathematics
        print("\n[Step 2] Configuring DEP-0010 as B.Sc in Mathematics...")
        d10 = Department.objects.get(dept_id="DEP-0010")
        d10.name = "B.Sc in Mathematics"
        d10.program_type = "B.Sc"
        d10.core_department = "Mathematics"
        d10.no_of_years = 4
        d10.save()
        print(f"  [OK] Updated {d10.dept_id} -> Name: '{d10.name}', Program: '{d10.program_type}'")

        # Step 3: Define Merges
        # Tuple format: (target_dept_id, [list_of_source_dept_ids])
        merges = [
            ("DEP-0151", ["DEP-0001", "DEP-0004", "DEP-0050"]),
            ("DEP-0165", ["DEP-0002", "DEP-0020"]),
            ("DEP-0010", ["DEP-0003"]),
            ("DEP-0166", ["DEP-0005", "DEP-0031"]),
            ("DEP-0167", ["DEP-0006"]),
            ("DEP-0084", ["DEP-0007", "DEP-0008"]),
            ("DEP-0045", ["DEP-0011"]),
            ("DEP-0033", ["DEP-0012"]),
        ]

        print("\n[Step 3] Executing Merges...")
        for target_id, source_ids in merges:
            target = Department.objects.get(dept_id=target_id)
            print(f"\nTarget: [{target.dept_id}] {target.name}")
            init_students = target.students.count()
            init_faculty = target.faculty_members.count()
            init_subjects = target.subjects.count()

            for s_id in source_ids:
                source = Department.objects.get(dept_id=s_id)
                s_name = source.name
                s_stu = source.students.count()
                s_fac = source.faculty_members.count()
                s_sub = source.subjects.count()
                s_room = source.rooms.count()
                s_hod = source.hod

                # Reassign Students
                source.students.update(department=target)

                # Reassign Faculty
                source.faculty_members.update(department=target)

                # Reassign Subjects (M2M)
                for sub in list(source.subjects.all()):
                    sub.departments.add(target)
                    sub.departments.remove(source)

                # Reassign Rooms (M2M)
                for room in list(source.rooms.all()):
                    room.departments.add(target)
                    room.departments.remove(source)

                # Assign HOD if target does not have one
                if not target.hod and s_hod:
                    target.hod = s_hod
                    target.save(update_fields=["hod"])
                    print(f"    - Transferred HOD {s_hod} from {s_id} to {target_id}")

                # Detach HOD from source before deleting
                source.hod = None
                source.save(update_fields=["hod"])

                # Delete source department
                source.delete()
                print(f"  [OK] Merged & deleted [{s_id}] '{s_name}': {s_stu} students, {s_fac} faculty, {s_sub} subjects, {s_room} rooms transferred")

            target.refresh_from_db()
            print(f"  => Current [{target.dept_id}] {target.name}: {target.students.count()} students (+{target.students.count() - init_students}), {target.faculty_members.count()} faculty (+{target.faculty_members.count() - init_faculty}), {target.subjects.count()} subjects, HOD: {target.hod}")

    print("\n" + "=" * 80)
    print("DEPARTMENT MERGE COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    merge_departments()

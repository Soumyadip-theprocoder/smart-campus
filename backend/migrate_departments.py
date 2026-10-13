import os
import sys
import django

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

from apps.scheduler.models import Department

def migrate_departments():
    departments = Department.objects.all()
    count = 0
    for dept in departments:
        name = dept.name
        if " in " in name:
            parts = name.split(" in ")
            dept.program_type = parts[0].strip()
            dept.core_department = parts[1].strip()
            dept.save()
            count += 1
        else:
            # Maybe it's just "Computer Science"
            dept.core_department = name.strip()
            dept.save()
            count += 1
    print(f"Updated {count} departments successfully.")

if __name__ == "__main__":
    migrate_departments()

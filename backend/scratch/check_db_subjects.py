import os
import sys
import django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.models import Department, Subject

print("Total subjects in DB:", Subject.objects.count())
depts_with_subs = Department.objects.filter(subjects__isnull=False).distinct()
print("Departments with subjects:", depts_with_subs.count())
for d in depts_with_subs.order_by("name"):
    sems = list(d.subjects.values_list("semester", flat=True).distinct().order_by("semester"))
    print(f"[{d.dept_id}] {d.name}: {d.subjects.count()} subjects (sems: {sems})")

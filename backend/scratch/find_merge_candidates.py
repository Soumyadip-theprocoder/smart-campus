import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.scheduler.models import Department

for i in range(1, 13):
    d = Department.objects.get(dept_id=f'DEP-{i:04d}')
    words = [w for w in d.name.split() if len(w) > 3 and w.lower() not in ['engineering', 'studies', 'pure']]
    qs = Department.objects.exclude(dept_id__in=[f'DEP-{j:04d}' for j in range(1, 13)])
    
    candidates = []
    for w in words:
        for c in qs.filter(name__icontains=w):
            if c not in candidates:
                candidates.append(c)
                
    print(f"[{d.dept_id}] {d.name} (Students: {d.students.count()}, Faculty: {d.faculty_members.count()})")
    for c in candidates[:6]:
        print(f"    -> {c.dept_id}: {c.name} ({c.program_type})")

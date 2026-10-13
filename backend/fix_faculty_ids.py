import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Faculty

def fix_faculty_ids():
    faculties = Faculty.objects.all().order_by('id')
    
    # First pass: randomize to avoid unique constraint violations
    for fac in faculties:
        fac.employee_id = f"TEMP-{uuid.uuid4().hex[:8]}"
        fac.save(update_fields=['employee_id'])
        
    count = 1
    updated = 0
    for fac in faculties:
        new_id = f"FAC-2026-{count:04d}"
        fac.employee_id = new_id
        fac.save(update_fields=['employee_id'])
        updated += 1
        count += 1
        
    print(f"Updated {updated} faculty IDs to format FAC-YYYY-XXXX.")

if __name__ == "__main__":
    fix_faculty_ids()

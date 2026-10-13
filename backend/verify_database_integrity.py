import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.models import Department, Subject
from apps.accounts.models import Faculty, Student

def audit_database():
    print("=" * 80)
    print("COMPREHENSIVE DATABASE AUDIT & INTEGRITY VERIFICATION")
    print("=" * 80)

    total_subjects = Subject.objects.count()
    print(f"\n1. SUBJECTS OVERVIEW:")
    print(f"   Total subjects: {total_subjects}")

    # Check for invalid semester
    invalid_sem = Subject.objects.filter(semester__isnull=True).count()
    zero_sem = Subject.objects.filter(semester=0).count()
    print(f"   Subjects with null semester: {invalid_sem}")
    print(f"   Subjects with semester=0: {zero_sem}")

    # Check for empty code or name
    empty_codes = Subject.objects.filter(code="").count()
    empty_names = Subject.objects.filter(name="").count()
    short_names = Subject.objects.filter(name__regex=r'^.{1,2}$').count()
    print(f"   Subjects with empty code: {empty_codes}")
    print(f"   Subjects with empty name: {empty_names}")
    print(f"   Subjects with name length < 3: {short_names}")

    # Check for invalid credits
    invalid_credits = Subject.objects.filter(credits__lte=0).count()
    high_credits = Subject.objects.filter(credits__gt=10).count()
    print(f"   Subjects with credits <= 0: {invalid_credits}")
    print(f"   Subjects with credits > 10: {high_credits}")

    from django.db.models import Count

    # Inspect orphaned subjects
    orphaned_subs = Subject.objects.filter(departments__isnull=True)
    print(f"   Subjects with NO department linked: {orphaned_subs.count()}")
    for s in orphaned_subs:
        print(f"      - [{s.code}] {s.name} (Sem {s.semester})")

    # Inspect credits <= 0
    zero_credit_subs = Subject.objects.filter(credits__lte=0)
    print(f"   Subjects with credits <= 0: {zero_credit_subs.count()}")
    for s in zero_credit_subs:
        print(f"      - [{s.code}] {s.name} (credits={s.credits})")

    # Check subjects per semester breakdown
    print(f"\n2. SUBJECT DISTRIBUTION BY SEMESTER:")
    for s in range(1, 11):
        cnt = Subject.objects.filter(semester=s).count()
        print(f"   Semester {s:2d}: {cnt:4d} subjects")

    # Check subjects per department
    print(f"\n3. DEPARTMENT SUBJECT COVERAGE (Top 15):")
    for d in Department.objects.annotate(num_subs=Count('subjects')).filter(num_subs__gt=0).order_by("-num_subs")[:15]:
        sems = sorted(list(set(d.subjects.values_list("semester", flat=True))))
        print(f"   [{d.dept_id}] {d.name:55}: {d.num_subs:3d} subjects | sems: {sems}")

    # Check for garbled titles (e.g. ending in unwanted digits or weird symbols)
    weird_titles = []
    for s in Subject.objects.all():
        if any(char in s.name for char in ['\ufffd', '\n', '\r', '\t']):
            weird_titles.append((s.code, s.name))
    print(f"\n4. TITLE QUALITY CHECK:")
    print(f"   Subjects with weird formatting characters: {len(weird_titles)}")
    if weird_titles:
        for code, name in weird_titles[:5]:
            print(f"      - {code}: {repr(name)}")

    # Check faculty and student linking
    print(f"\n5. ACCOUNTS & PROFILES:")
    print(f"   Total Students: {Student.objects.count()} (Orphaned: {Student.objects.filter(department__isnull=True).count()})")
    print(f"   Total Faculty:  {Faculty.objects.count()} (Orphaned: {Faculty.objects.filter(department__isnull=True).count()})")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    audit_database()

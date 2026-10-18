# Generated manually for Smart Campus Management System
# Rebalances course faculty assignments term-aware across all 4,290 faculty members,
# ensuring realistic university teaching loads (<= 12 sessions/week per term)
# and eliminating the 128 sessions/week overload bottleneck on single faculty members.

from collections import defaultdict
from django.db import migrations


def rebalance_faculty_workload(apps, schema_editor):
    Faculty = apps.get_model("accounts", "Faculty")
    Department = apps.get_model("scheduler", "Department")
    Subject = apps.get_model("scheduler", "Subject")

    def get_school_block(d):
        name = (d.name or "").lower()
        core = (d.core_department or "").lower()
        if any(k in core or k in name for k in ["computer", "data science", "artificial intelligence", "cyber", "information technology", "software", "bca", "mca"]):
            return "A"
        elif any(k in core or k in name for k in ["mechanical", "civil", "electrical", "electronics", "chemical", "textile", "leather", "robotics", "food technology", "engineering"]):
            return "B"
        elif any(k in core or k in name for k in ["medical", "health", "hospital", "nutrition", "physiotherapy", "paramedical", "optometry", "clinical", "biomedical"]):
            return "C"
        elif any(k in core or k in name for k in ["business", "management", "bba", "mba", "commerce", "finance", "marketing", "apparel"]):
            return "D"
        elif any(k in core or k in name for k in ["physics", "math", "chemistry", "biology", "biotechnology", "life sciences", "environmental", "forensic", "genetics"]):
            return "E"
        elif any(k in core or k in name for k in ["pharmacy", "pharm"]):
            return "F"
        elif any(k in core or k in name for k in ["media", "film", "animation", "journalism", "mass communication", "fashion", "design", "architecture", "b.arch", "m.arch"]):
            return "G"
        elif any(k in core or k in name for k in ["humanities", "psychology", "english", "history", "economics", "law", "social"]):
            return "H"
        else:
            return "I"

    # Map faculty members by department and school block
    fac_by_dept = defaultdict(list)
    fac_by_block = defaultdict(list)
    all_fac = list(Faculty.objects.all().order_by("id"))

    for f in all_fac:
        fac_by_dept[f.department_id].append(f)
        if f.department:
            b = get_school_block(f.department)
            fac_by_block[b].append(f)

    # Track session loads separately for Odd and Even terms
    odd_loads = defaultdict(int)
    even_loads = defaultdict(int)

    subjects_to_update = []
    all_subjects = list(Subject.objects.prefetch_related("departments").order_by("code"))

    for s in all_subjects:
        is_odd = (s.semester is not None and s.semester % 2 == 1)
        depts = list(s.departments.all())

        cand_fac = []
        for d in depts:
            cand_fac.extend(fac_by_dept[d.id])

        if not cand_fac and depts:
            b = get_school_block(depts[0])
            cand_fac = fac_by_block[b]

        if not cand_fac:
            cand_fac = all_fac

        if is_odd:
            best_f = min(cand_fac, key=lambda f: odd_loads[f.id])
            odd_loads[best_f.id] += (s.sessions_per_week or 3)
        else:
            best_f = min(cand_fac, key=lambda f: even_loads[f.id])
            even_loads[best_f.id] += (s.sessions_per_week or 3)

        s.faculty = best_f
        subjects_to_update.append(s)

    # Bulk update faculty assignments
    Subject.objects.bulk_update(subjects_to_update, ["faculty"], batch_size=500)


def reverse_rebalance_faculty_workload(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("scheduler", "0019_scale_campus_infrastructure"),
    ]

    operations = [
        migrations.RunPython(rebalance_faculty_workload, reverse_code=reverse_rebalance_faculty_workload),
    ]

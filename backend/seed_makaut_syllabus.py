"""
Seed script to ingest official MAKAUT AICTE NEP 2020 1st Year B.Tech curriculum and detailed syllabus.
Creates all 30 B.Tech departments (Group A CSE & Allied, Group B Other branches) and adds all
detailed courses for Semester 1 and Semester 2 mapped accurately to departments and semesters.
"""

import os
import sys
import django

# Setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.models import Department, Subject, Amenity
from apps.accounts.models import Faculty


GROUP_A_BRANCHES = [
    "B.Tech in Computer Science & Engineering",
    "B.Tech in Computer Science & Engineering (Artificial Intelligence and Machine Learning)",
    "B.Tech in Computer Science & Business Systems",
    "B.Tech in Computer Science & Engineering (Data Science)",
    "B.Tech in Computer Science & Engineering (Cyber Security)",
    "B.Tech in Computer Science & Engineering (Internet of Things)",
    "B.Tech in Computer Science & Engineering (Artificial Intelligence)",
    "B.Tech in Computer Science & Engineering (IoT and Cyber Security including Blockchain Technology)",
    "B.Tech in Computer Science & Design",
    "B.Tech in Computer Science & Information Technology",
    "B.Tech in Electronics and Computer Science",
    "B.Tech in Electrical & Computer Engineering",
    "B.Tech in Artificial Intelligence & Machine Learning",
    "B.Tech in Artificial Intelligence & Data Science",
    "B.Tech in Artificial Intelligence",
]

GROUP_B_BRANCHES = [
    "B.Tech in Electronics & Communication Engineering",
    "B.Tech in Electrical Engineering",
    "B.Tech in Mechanical Engineering",
    "B.Tech in Civil Engineering",
    "B.Tech in Information Technology",
    "B.Tech in Electrical & Electronics Engineering",
    "B.Tech in Textile Technology",
    "B.Tech in Applied Electronics & Instrumentation Engineering",
    "B.Tech in Food Technology",
    "B.Tech in Apparel & Production Management",
    "B.Tech in Civil & Environmental Engineering",
    "B.Tech in Biomedical Engineering",
    "B.Tech in Chemical Engineering",
    "B.Tech in Leather Technology",
    "B.Tech in Automobile Engineering",
]


COURSES_DATA = [
    # ================= SEMESTER 1 =================
    {
        "code": "26-BS-M101",
        "name": "Mathematics - I",
        "semester": 1,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#2563eb",  # Blue
        "target_group": "ALL",
        "dept_keyword": "Mathematics",
        "description": (
            "Differential and integral calculus of one and several variables, Taylor series, "
            "maxima and minima, Lagrange multipliers, multiple integrals (area & volume), "
            "matrices, consistency of linear systems, eigenvalues, eigenvectors, Cayley-Hamilton theorem."
        ),
    },
    {
        "code": "26-BS-PH101",
        "name": "Physics",
        "semester": 1,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#7c3aed",  # Purple
        "target_group": "A",
        "dept_keyword": "Physics",
        "description": (
            "Oscillations and waves, physical optics (interference, diffraction grating, polarisation), "
            "electromagnetism and Maxwell's equations in vacuum and matter, elements of quantum mechanics "
            "and solid-state physics for engineering devices."
        ),
    },
    {
        "code": "26-BS-CH101",
        "name": "Chemistry",
        "semester": 1,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#059669",  # Emerald
        "target_group": "B",
        "dept_keyword": "Chemistry",
        "description": (
            "Atomic and molecular structure, periodic properties, chemical thermodynamics, reaction kinetics, "
            "organic reaction mechanisms, synthesis of engineering polymers, corrosion science and protection."
        ),
    },
    {
        "code": "26-ES-EE101",
        "name": "Basic Electrical and Electronics Engineering",
        "semester": 1,
        "credits": 4.0,
        "subject_type": "lecture",
        "sessions_per_week": 4,
        "required_capacity": 60,
        "color_code": "#d97706",  # Amber
        "target_group": "ALL",
        "dept_keyword": "Electrical",
        "description": (
            "DC network analysis (Thevenin, Norton, Superposition), single-phase & three-phase AC circuits, "
            "magnetic circuits and transformers, DC/AC machines, semiconductor physics, diodes, BJT, and Op-Amp fundamentals."
        ),
    },
    {
        "code": "26-AEC-101",
        "name": "English for Communication Skills",
        "semester": 1,
        "credits": 2.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#0891b2",  # Cyan
        "target_group": "ALL",
        "dept_keyword": "English",
        "description": (
            "Foundational communication skills, lexical acquisition, sentence framing, technical reading comprehension, "
            "business correspondence, technical report drafting, and presentation techniques."
        ),
    },
    {
        "code": "26-BS-PH191",
        "name": "Physics Laboratory",
        "semester": 1,
        "credits": 1.5,
        "subject_type": "lab",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#6d28d9",  # Deep Violet
        "target_group": "A",
        "dept_keyword": "Physics",
        "description": (
            "Hands-on experiments on Newton's rings, diffraction grating, dispersive power of prism, torsional pendulum, "
            "photoelectric effect, Planck's constant, Hall effect, and error analysis."
        ),
    },
    {
        "code": "26-BS-CH191",
        "name": "Chemistry Laboratory",
        "semester": 1,
        "credits": 1.5,
        "subject_type": "lab",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#047857",  # Forest Green
        "target_group": "B",
        "dept_keyword": "Chemistry",
        "description": (
            "Volumetric and complexometric titrations, determination of water hardness, conductometric titrations, "
            "pH-metric analysis, viscosity and surface tension of liquid solutions."
        ),
    },
    {
        "code": "26-ES-ME191",
        "name": "Engineering Graphics and Design",
        "semester": 1,
        "credits": 2.0,
        "subject_type": "lab",
        "sessions_per_week": 4,
        "required_capacity": 30,
        "color_code": "#ea580c",  # Orange
        "target_group": "A",
        "dept_keyword": "Mechanical",
        "description": (
            "Principles of orthographic projection, projections of points, straight lines, inclined planes, and solids. "
            "Isometric projections, section of solids, introduction to CAD drafting software."
        ),
    },
    {
        "code": "26-ES-ME192",
        "name": "Workshop Practice",
        "semester": 1,
        "credits": 2.0,
        "subject_type": "lab",
        "sessions_per_week": 4,
        "required_capacity": 30,
        "color_code": "#b45309",  # Brown/Amber
        "target_group": "B",
        "dept_keyword": "Mechanical",
        "description": (
            "Practical benchwork in fitting shop, carpentry shop, welding and tin-smithy, basic electrical house wiring, "
            "machine tool operations (lathe), and industrial safety standards."
        ),
    },
    {
        "code": "26-ES-EE191",
        "name": "Basic Electrical and Electronics Engineering Laboratory",
        "semester": 1,
        "credits": 1.5,
        "subject_type": "lab",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#c2410c",  # Rust
        "target_group": "ALL",
        "dept_keyword": "Electrical",
        "description": (
            "Experimental validation of KVL, KCL, Thevenin and Norton theorems, RLC series and parallel resonance, "
            "diode V-I characteristics, rectifiers, filter circuits, and BJT switching characteristics."
        ),
    },
    {
        "code": "26-VAC-181",
        "name": "NCC / NSS / Yoga and Sports",
        "semester": 1,
        "credits": 2.0,
        "subject_type": "seminar",
        "sessions_per_week": 4,
        "required_capacity": 60,
        "color_code": "#15803d",  # Green
        "target_group": "ALL",
        "dept_keyword": None,
        "description": (
            "Value-added physical and social awareness module covering community service, civic duties, physical endurance, "
            "yoga asanas, team sportsmanship, and holistic mental and physical well-being."
        ),
    },
    {
        "code": "26-SEC-181",
        "name": "Skill Enhancement Course - MOOCs / Skills",
        "semester": 1,
        "credits": 1.0,
        "subject_type": "seminar",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#4f46e5",  # Indigo
        "target_group": "ALL",
        "dept_keyword": None,
        "description": (
            "Industry-aligned skill training or approved MOOC course (SWAYAM Plus / FutureSkills Prime) covering digital literacy, "
            "hands-on tools, and modern problem solving."
        ),
    },
    {
        "code": "26-MC-181",
        "name": "Indian Constitution",
        "semester": 1,
        "credits": 0.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#475569",  # Slate
        "target_group": "A",
        "dept_keyword": "History",
        "description": (
            "Mandatory non-credit course covering constitutional framework, philosophy of Preamble, Fundamental Rights and Duties, "
            "Directive Principles of State Policy, and Union & State executive machinery."
        ),
    },
    {
        "code": "26-MC-182",
        "name": "Indian Knowledge System",
        "semester": 1,
        "credits": 0.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#78350f",  # Warm Amber
        "target_group": "B",
        "dept_keyword": "History",
        "description": (
            "Mandatory non-credit course providing insights into ancient Indian scientific traditions, Vedic mathematics, "
            "astronomy, metallurgy, architectural planning, sustainable agriculture, and indigenous knowledge heritage."
        ),
    },

    # ================= SEMESTER 2 =================
    {
        "code": "26-BS-M201",
        "name": "Mathematics - II",
        "semester": 2,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#1d4ed8",  # Royal Blue
        "target_group": "ALL",
        "dept_keyword": "Mathematics",
        "description": (
            "First order and higher order linear ordinary differential equations with constant coefficients, "
            "Cauchy-Euler equations, Laplace transforms and inverse transforms with applications to initial value problems, "
            "vector calculus (gradient, divergence, curl, line and surface integrals, Green's, Gauss, and Stokes' theorems)."
        ),
    },
    {
        "code": "26-BS-BI201",
        "name": "Biology for Engineers",
        "semester": 2,
        "credits": 2.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#16a34a",  # Fresh Green
        "target_group": "ALL",
        "dept_keyword": "Biotechnology",
        "description": (
            "Biological macromolecules (proteins, nucleic acids, lipids), cell organization, bioenergetics, enzyme catalysis, "
            "transmission of genetic information, bio-inspired engineering principles, biosensors, and neural computing foundations."
        ),
    },
    {
        "code": "26-BS-PH201",
        "name": "Physics",
        "semester": 2,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#7c3aed",  # Purple
        "target_group": "B",
        "dept_keyword": "Physics",
        "description": (
            "Oscillations and waves, physical optics (interference, diffraction grating, polarisation), "
            "electromagnetism and Maxwell's equations in vacuum and matter, elements of quantum mechanics "
            "and solid-state physics for engineering devices."
        ),
    },
    {
        "code": "26-BS-CH201",
        "name": "Chemistry",
        "semester": 2,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#059669",  # Emerald
        "target_group": "A",
        "dept_keyword": "Chemistry",
        "description": (
            "Atomic and molecular structure, periodic properties, chemical thermodynamics, reaction kinetics, "
            "organic reaction mechanisms, synthesis of engineering polymers, corrosion science and protection."
        ),
    },
    {
        "code": "26-ES-CS201",
        "name": "Programming for Problem Solving and Introduction to AI",
        "semester": 2,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#db2777",  # Pink/Rose
        "target_group": "ALL",
        "dept_keyword": "Computer Science",
        "description": (
            "Problem-solving methodology, algorithms, flowcharting, structured programming constructs (iteration, conditionals, "
            "arrays, functions, recursion, pointers, file I/O). Overview of Artificial Intelligence, machine learning paradigms, "
            "and modern AI engineering tools."
        ),
    },
    {
        "code": "26-VAC-201",
        "name": "Environmental Science",
        "semester": 2,
        "credits": 3.0,
        "subject_type": "lecture",
        "sessions_per_week": 3,
        "required_capacity": 60,
        "color_code": "#0d9488",  # Teal
        "target_group": "ALL",
        "dept_keyword": None,
        "description": (
            "Ecosystem concepts, biodiversity conservation, natural resource depletion, air, water and noise pollution abatement, "
            "solid waste management, environmental legislation, greenhouse effect, and sustainable environmental practices."
        ),
    },
    {
        "code": "26-BS-PH291",
        "name": "Physics Laboratory",
        "semester": 2,
        "credits": 1.5,
        "subject_type": "lab",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#6d28d9",  # Deep Violet
        "target_group": "B",
        "dept_keyword": "Physics",
        "description": (
            "Hands-on experiments on Newton's rings, diffraction grating, dispersive power of prism, torsional pendulum, "
            "photoelectric effect, Planck's constant, Hall effect, and error analysis."
        ),
    },
    {
        "code": "26-BS-CH291",
        "name": "Chemistry Laboratory",
        "semester": 2,
        "credits": 1.5,
        "subject_type": "lab",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#047857",  # Forest Green
        "target_group": "A",
        "dept_keyword": "Chemistry",
        "description": (
            "Volumetric and complexometric titrations, determination of water hardness, conductometric titrations, "
            "pH-metric analysis, viscosity and surface tension of liquid solutions."
        ),
    },
    {
        "code": "26-ES-CS291",
        "name": "Programming for Problem Solving Lab & AI Tools",
        "semester": 2,
        "credits": 2.0,
        "subject_type": "lab",
        "sessions_per_week": 4,
        "required_capacity": 30,
        "color_code": "#e11d48",  # Red-Rose
        "target_group": "ALL",
        "dept_keyword": "Computer Science",
        "description": (
            "Laboratory implementation of algorithms in C/Python, matrix manipulation, string operations, recursive functions, "
            "file handling, and hands-on integration with state-of-the-art AI tools and prompt engineering."
        ),
    },
    {
        "code": "26-ES-ME291",
        "name": "Engineering Graphics and Design",
        "semester": 2,
        "credits": 2.0,
        "subject_type": "lab",
        "sessions_per_week": 4,
        "required_capacity": 30,
        "color_code": "#ea580c",  # Orange
        "target_group": "B",
        "dept_keyword": "Mechanical",
        "description": (
            "Principles of orthographic projection, projections of points, straight lines, inclined planes, and solids. "
            "Isometric projections, section of solids, introduction to CAD drafting software."
        ),
    },
    {
        "code": "26-ES-ME292",
        "name": "Workshop Practice",
        "semester": 2,
        "credits": 2.0,
        "subject_type": "lab",
        "sessions_per_week": 4,
        "required_capacity": 30,
        "color_code": "#b45309",  # Brown/Amber
        "target_group": "A",
        "dept_keyword": "Mechanical",
        "description": (
            "Practical benchwork in fitting shop, carpentry shop, welding and tin-smithy, basic electrical house wiring, "
            "machine tool operations (lathe), and industrial safety standards."
        ),
    },
    {
        "code": "26-AEC-281",
        "name": "Language Laboratory",
        "semester": 2,
        "credits": 1.0,
        "subject_type": "lab",
        "sessions_per_week": 2,
        "required_capacity": 30,
        "color_code": "#0284c7",  # Sky Blue
        "target_group": "ALL",
        "dept_keyword": "English",
        "description": (
            "Aural-oral language lab activities, phonetic training, intonation, speech clarity, listening comprehension exercises, "
            "group discussion simulations, and extempore presentation practice."
        ),
    },
    {
        "code": "26-AEC-282",
        "name": "Essentials for Professional Skills",
        "semester": 2,
        "credits": 1.5,
        "subject_type": "seminar",
        "sessions_per_week": 3,
        "required_capacity": 30,
        "color_code": "#6366f1",  # Indigo
        "target_group": "ALL",
        "dept_keyword": "Management",
        "description": (
            "Professional etiquette, resume and CV writing, LinkedIn profile optimization, corporate communications, "
            "interview techniques, interpersonal dynamics, emotional intelligence, and team leadership."
        ),
    },
    {
        "code": "26-SEC-282",
        "name": "Skill Enhancement Course - MOOCs / Skills",
        "semester": 2,
        "credits": 2.0,
        "subject_type": "seminar",
        "sessions_per_week": 4,
        "required_capacity": 60,
        "color_code": "#4338ca",  # Deep Indigo
        "target_group": "ALL",
        "dept_keyword": None,
        "description": (
            "Comprehensive 2-credit Skill Enhancement module via SWAYAM/NPTEL or hands-on institutional certification in "
            "emerging technologies, cloud tools, or domain-specific practical skills."
        ),
    },
    {
        "code": "26-MC-281",
        "name": "Indian Constitution",
        "semester": 2,
        "credits": 0.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#475569",  # Slate
        "target_group": "B",
        "dept_keyword": "History",
        "description": (
            "Mandatory non-credit course covering constitutional framework, philosophy of Preamble, Fundamental Rights and Duties, "
            "Directive Principles of State Policy, and Union & State executive machinery."
        ),
    },
    {
        "code": "26-MC-282",
        "name": "Indian Knowledge System",
        "semester": 2,
        "credits": 0.0,
        "subject_type": "lecture",
        "sessions_per_week": 2,
        "required_capacity": 60,
        "color_code": "#78350f",  # Warm Amber
        "target_group": "A",
        "dept_keyword": "History",
        "description": (
            "Mandatory non-credit course providing insights into ancient Indian scientific traditions, Vedic mathematics, "
            "astronomy, metallurgy, architectural planning, sustainable agriculture, and indigenous knowledge heritage."
        ),
    },
]


def seed_departments():
    """Ensure all 30 MAKAUT B.Tech departments exist with proper metadata."""
    print("Seeding MAKAUT B.Tech departments...")
    group_a_depts = []
    group_b_depts = []

    for name in GROUP_A_BRANCHES:
        dept, created = Department.objects.get_or_create(
            name=name,
            defaults={
                "program_type": "B.Tech",
                "core_department": "Computer Science & Allied",
                "no_of_years": 4,
            }
        )
        if not created and not dept.program_type:
            dept.program_type = "B.Tech"
            dept.core_department = "Computer Science & Allied"
            dept.no_of_years = 4
            dept.save()
        group_a_depts.append(dept)
        status = "Created" if created else "Found"
        print(f"  [{status}] Group A: {dept.dept_id} - {dept.name}")

    for name in GROUP_B_BRANCHES:
        dept, created = Department.objects.get_or_create(
            name=name,
            defaults={
                "program_type": "B.Tech",
                "core_department": "Engineering & Technology",
                "no_of_years": 4,
            }
        )
        if not created and not dept.program_type:
            dept.program_type = "B.Tech"
            dept.core_department = "Engineering & Technology"
            dept.no_of_years = 4
            dept.save()
        group_b_depts.append(dept)
        status = "Created" if created else "Found"
        print(f"  [{status}] Group B: {dept.dept_id} - {dept.name}")

    return group_a_depts, group_b_depts


def get_faculty_for_keyword(keyword):
    """Find a faculty member matching a discipline keyword, or None."""
    if not keyword:
        return Faculty.objects.first()
    f = Faculty.objects.filter(department__name__icontains=keyword).first()
    if not f:
        f = Faculty.objects.filter(user__first_name__icontains=keyword).first()
    if not f:
        f = Faculty.objects.first()
    return f


def seed_courses(group_a_depts, group_b_depts):
    """Create or update MAKAUT 1st Year courses and attach departments & semester."""
    print("\nSeeding MAKAUT NEP 2020 1st Year Courses...")
    all_btech_depts = list(set(group_a_depts + group_b_depts))

    for item in COURSES_DATA:
        faculty = get_faculty_for_keyword(item["dept_keyword"])
        
        subject, created = Subject.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "semester": item["semester"],
                "credits": item["credits"],
                "subject_type": item["subject_type"],
                "sessions_per_week": item["sessions_per_week"],
                "required_capacity": item["required_capacity"],
                "color_code": item["color_code"],
                "description": item["description"],
                "faculty": faculty,
                "is_elective": False,
            }
        )

        # Attach appropriate departments
        target_group = item["target_group"]
        if target_group == "A":
            subject.departments.set(group_a_depts)
            group_label = f"Group A ({len(group_a_depts)} depts)"
        elif target_group == "B":
            subject.departments.set(group_b_depts)
            group_label = f"Group B ({len(group_b_depts)} depts)"
        else:
            subject.departments.set(all_btech_depts)
            group_label = f"Both Groups ({len(all_btech_depts)} depts)"

        action = "Created" if created else "Updated"
        print(f"  [{action}] Sem {subject.semester} | {subject.code} - {subject.name} ({subject.credits} cr) -> {group_label}")


def main():
    group_a_depts, group_b_depts = seed_departments()
    seed_courses(group_a_depts, group_b_depts)
    print("\nMAKAUT syllabus ingestion complete successfully!")


if __name__ == "__main__":
    main()

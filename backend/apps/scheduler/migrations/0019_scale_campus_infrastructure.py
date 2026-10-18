# Generated manually for Smart Campus Management System
# Scales campus physical infrastructure to meet real-world university capacity:
# 374 rooms, ~26,500 simultaneous seats across 9 academic blocks and central auditoriums.

from django.db import migrations


def scale_campus_infrastructure(apps, schema_editor):
    Room = apps.get_model("scheduler", "Room")
    Department = apps.get_model("scheduler", "Department")
    Amenity = apps.get_model("scheduler", "Amenity")
    Resource = apps.get_model("scheduler", "Resource")

    # 1. Ensure Standard Amenities
    amenity_specs = [
        ("Air Conditioning", "Climate-controlled classroom and laboratory environment"),
        ("Smart Board", "Interactive digital touchscreen board"),
        ("Wheelchair Accessible", "Ramp and wide-door accessible room layout"),
        ("Audio-Visual System", "Integrated surround sound, amplifier, and ceiling microphones"),
        ("High-Speed WiFi", "Enterprise gigabit wireless access point"),
        ("Lab Safety Stations", "Equipped with eyewash, chemical safety gear, and first aid kits"),
    ]
    amenities = {}
    for name, desc in amenity_specs:
        amenity, _ = Amenity.objects.get_or_create(name=name, defaults={"description": desc})
        amenities[name] = amenity

    # 2. Central Complex Auditoriums & Lecture Halls
    central_rooms_specs = {
        "AUD-101": {
            "building": "Main Block (Central Complex)",
            "capacity": 500,
            "room_type": "lecture",
            "equipment": ["4K Dual Laser Projector", "PA Line Array Audio System", "Stage Lighting", "Enterprise Gigabit WiFi", "Broadcasting Suite"],
            "amenity_keys": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "Smart Board", "High-Speed WiFi"],
        },
        "LH-101": {
            "building": "Main Block (Central Complex)",
            "capacity": 250,
            "room_type": "lecture",
            "equipment": ["4K Laser Projector", "PA Audio System", "Dual Whiteboards", "Enterprise Gigabit WiFi"],
            "amenity_keys": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "High-Speed WiFi"],
        },
        "LH-102": {
            "building": "Main Block (Central Complex)",
            "capacity": 180,
            "room_type": "lecture",
            "equipment": ["4K Laser Projector", "PA Audio System", "Dual Whiteboards", "Enterprise Gigabit WiFi"],
            "amenity_keys": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "High-Speed WiFi"],
        },
        "LH-201": {
            "building": "Main Block (Central Complex)",
            "capacity": 150,
            "room_type": "lecture",
            "equipment": ["HD Laser Projector", "Surround Audio System", "Whiteboard", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Audio-Visual System", "High-Speed WiFi"],
        },
        "SR-101": {
            "building": "Central Annex",
            "capacity": 60,
            "room_type": "seminar",
            "equipment": ["Video Conference System", "Smart Touchscreen Display", "Executive Board Seating", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Audio-Visual System", "Smart Board", "High-Speed WiFi"],
        },
        "LAB-301": {
            "building": "Central Annex",
            "capacity": 70,
            "room_type": "lab",
            "equipment": ["High-Performance Workstations (70x)", "Gigabit Switch", "Laser Projector", "Whiteboard"],
            "amenity_keys": ["Air Conditioning", "High-Speed WiFi"],
        },
        "LAB-302": {
            "building": "Central Annex",
            "capacity": 70,
            "room_type": "lab",
            "equipment": ["High-Performance Workstations (70x)", "Gigabit Switch", "Laser Projector", "Whiteboard"],
            "amenity_keys": ["Air Conditioning", "High-Speed WiFi"],
        },
    }

    all_depts = list(Department.objects.all())

    for r_num, spec in central_rooms_specs.items():
        room, created = Room.objects.get_or_create(
            room_number=r_num,
            defaults={
                "capacity": spec["capacity"],
                "building": spec["building"],
                "room_type": spec["room_type"],
                "equipment": spec["equipment"],
            },
        )
        room.capacity = spec["capacity"]
        room.building = spec["building"]
        room.room_type = spec["room_type"]
        room.equipment = spec["equipment"]
        room.save()
        room.amenities.set([amenities[k] for k in spec["amenity_keys"] if k in amenities])
        room.departments.set(all_depts)

    # 3. Department School Categorization
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

    depts_by_block = {"A": [], "B": [], "C": [], "D": [], "E": [], "F": [], "G": [], "H": [], "I": []}
    for dept in all_depts:
        b_key = get_school_block(dept)
        depts_by_block[b_key].append(dept)

    # 4. Academic Blocks Floor Plans & Equipment Specs
    blocks_meta = {
        "A": {
            "name": "Block A - Computing & AI Block",
            "floors": 5,
            "rooms_per_floor": 13,
            "lab_equipment": ["AI GPU Workstations (45x)", "Gigabit LAN Switch", "Smart 4K Projector", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Smart Board"],
        },
        "B": {
            "name": "Block B - Engineering & Technology Block",
            "floors": 5,
            "rooms_per_floor": 14,
            "lab_equipment": ["Engineering Workbenches", "Oscilloscopes & Power Supplies", "Safety Stations", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "High-Speed WiFi"],
        },
        "C": {
            "name": "Block C - Health & Allied Medical Sciences Block",
            "floors": 4,
            "rooms_per_floor": 11,
            "lab_equipment": ["Clinical Diagnostic Kits", "Optical Microscopes (35x)", "Specimen Prep Benches", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "D": {
            "name": "Block D - Business & Management Block",
            "floors": 4,
            "rooms_per_floor": 11,
            "lab_equipment": ["Financial Bloomberg Terminals (40x)", "Interactive Projector", "Dual Whiteboards"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Smart Board"],
        },
        "E": {
            "name": "Block E - Basic & Applied Sciences Block",
            "floors": 4,
            "rooms_per_floor": 10,
            "lab_equipment": ["Fume Hoods & Chemical Benches", "Centrifuges & Incubators", "Lab Safety Eyewash", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "F": {
            "name": "Block F - Pharmacy & Pharmaceutical Sciences Block",
            "floors": 3,
            "rooms_per_floor": 8,
            "lab_equipment": ["Analytical Spectrophotometers", "Tablet Dissolution Testers", "Compound Benches", "Safety Stations"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "G": {
            "name": "Block G - Media, Design & Architecture Block",
            "floors": 4,
            "rooms_per_floor": 8,
            "lab_equipment": ["Drawing Drafting Tables (40x)", "Color-Calibrated Mac Workstations", "4K Video Editing Suites"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Audio-Visual System"],
        },
        "H": {
            "name": "Block H - Humanities & Social Sciences Block",
            "floors": 3,
            "rooms_per_floor": 7,
            "lab_equipment": ["Language Audio Lab Consoles", "Conference Projector", "Discussion Tables", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System"],
        },
        "I": {
            "name": "Block I - Hospitality, Tourism & General Studies",
            "floors": 3,
            "rooms_per_floor": 9,
            "lab_equipment": ["Hotel Front-Desk Simulation Consoles", "Culinary Demo Stations", "Projection System"],
            "lab_amenities": ["Air Conditioning", "Wheelchair Accessible", "High-Speed WiFi"],
        },
    }

    # 5. Provision Scaled Room Wings
    for b_key, b_info in blocks_meta.items():
        b_name = b_info["name"]
        assigned_depts = depts_by_block[b_key]
        floors = b_info["floors"]
        rooms_per_floor = b_info["rooms_per_floor"]

        for floor in range(1, floors + 1):
            for r_idx in range(1, rooms_per_floor + 1):
                r_num = f"{b_key}-{floor}{r_idx:02d}"

                if floor == 1:
                    if r_idx == 1:
                        # Tiered Mini-Auditorium / Main Lecture Theatre
                        cap = 150
                        r_type = "lecture"
                        equip = ["4K Dual Laser Projector", "PA Surround Audio System", "Dual Interactive Whiteboards", "Enterprise Gigabit WiFi", "Podium Touchscreen Console"]
                        am_keys = ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "Smart Board", "High-Speed WiFi"]
                    elif r_idx == 2:
                        cap = 120
                        r_type = "lecture"
                        equip = ["Smart 4K Projector", "PA Audio System", "Dual Whiteboard", "Enterprise Gigabit WiFi"]
                        am_keys = ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "High-Speed WiFi"]
                    elif r_idx == 3:
                        cap = 100
                        r_type = "lecture"
                        equip = ["Smart Projector", "PA Audio System", "Dual Whiteboard", "Enterprise Gigabit WiFi"]
                        am_keys = ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "High-Speed WiFi"]
                    else:
                        cap = 80
                        r_type = "lecture"
                        equip = ["Smart Projector", "Magnetic Whiteboard", "High-Speed WiFi"]
                        am_keys = ["Air Conditioning", "Wheelchair Accessible", "High-Speed WiFi"]

                elif floor == 2:
                    if r_idx <= 3:
                        cap = 85
                        r_type = "lecture"
                        equip = ["Smart Projector", "PA Audio System", "Dual Whiteboard", "High-Speed WiFi"]
                        am_keys = ["Air Conditioning", "Audio-Visual System", "High-Speed WiFi"]
                    else:
                        cap = 75
                        r_type = "lecture"
                        equip = ["Smart Projector", "Magnetic Whiteboard", "High-Speed WiFi"]
                        am_keys = ["Air Conditioning", "High-Speed WiFi"]

                elif floor == 3:
                    if r_idx <= 4:
                        cap = 70
                        r_type = "lecture"
                        equip = ["Smart Projector", "Magnetic Whiteboard", "High-Speed WiFi"]
                        am_keys = ["Air Conditioning", "High-Speed WiFi"]
                    elif r_idx <= 7:
                        cap = 45
                        r_type = "seminar"
                        equip = ["Video Conference System", "Smart Touchscreen Display", "Executive Board Seating", "High-Speed WiFi"]
                        am_keys = ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "Smart Board", "High-Speed WiFi"]
                    else:
                        cap = 50
                        r_type = "lab"
                        equip = b_info["lab_equipment"]
                        am_keys = b_info["lab_amenities"]

                elif floor == 4:
                    cap = 50
                    r_type = "lab"
                    equip = b_info["lab_equipment"]
                    am_keys = b_info["lab_amenities"]

                elif floor == 5:
                    cap = 45
                    r_type = "lab"
                    equip = b_info["lab_equipment"]
                    am_keys = b_info["lab_amenities"]

                room, created = Room.objects.get_or_create(
                    room_number=r_num,
                    defaults={
                        "capacity": cap,
                        "building": b_name,
                        "room_type": r_type,
                        "equipment": equip,
                    },
                )
                room.capacity = cap
                room.building = b_name
                room.room_type = r_type
                room.equipment = equip
                room.save()

                room.amenities.set([amenities[k] for k in am_keys if k in amenities])
                room.departments.set(assigned_depts)


def reverse_scale_campus_infrastructure(apps, schema_editor):
    Room = apps.get_model("scheduler", "Room")
    import re
    # Keep the original 114 prototype rooms (A-101 to I-304 + central), delete rooms created beyond floor 3 room 4
    # Pattern matching original migration rooms:
    orig_pattern = r"^[A-I]-[1-3]0[1-4]$"
    central_numbers = {"LH-101", "LH-102", "LH-201", "SR-101", "LAB-301", "LAB-302"}

    for r in Room.objects.all():
        if r.room_number in central_numbers or re.match(orig_pattern, r.room_number):
            continue
        r.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("scheduler", "0018_seed_campus_blocks_and_rooms"),
    ]

    operations = [
        migrations.RunPython(scale_campus_infrastructure, reverse_code=reverse_scale_campus_infrastructure),
    ]

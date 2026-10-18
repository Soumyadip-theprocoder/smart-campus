# Generated manually for Smart Campus Management System

from django.db import migrations


def seed_campus_blocks_and_rooms(apps, schema_editor):
    Room = apps.get_model("scheduler", "Room")
    Department = apps.get_model("scheduler", "Department")
    Amenity = apps.get_model("scheduler", "Amenity")
    Resource = apps.get_model("scheduler", "Resource")

    # 1. Provision Standard Amenities
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

    # 2. Provision Campus Resources
    resource_specs = [
        ("Mobile 4K Projector Unit", 15),
        ("Lab Optical Microscope Set", 30),
        ("Robotics & Microcontroller Kit", 25),
        ("Wireless PA Microphone Set", 20),
        ("VR/AR Immersive Headset Kit", 12),
    ]
    for name, qty in resource_specs:
        Resource.objects.get_or_create(name=name, defaults={"quantity": qty})

    # 3. Enhance Existing Central Rooms
    existing_rooms_data = {
        "LH-101": {
            "building": "Main Block (Central Complex)",
            "capacity": 60,
            "room_type": "lecture",
            "equipment": ["4K Laser Projector", "PA Audio System", "Dual Whiteboards", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System"],
        },
        "LH-102": {
            "building": "Main Block (Central Complex)",
            "capacity": 60,
            "room_type": "lecture",
            "equipment": ["4K Laser Projector", "PA Audio System", "Dual Whiteboards", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System"],
        },
        "LH-201": {
            "building": "Main Block (Central Complex)",
            "capacity": 40,
            "room_type": "lecture",
            "equipment": ["HD Projector", "Whiteboard", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Audio-Visual System"],
        },
        "SR-101": {
            "building": "Central Annex",
            "capacity": 20,
            "room_type": "seminar",
            "equipment": ["Video Conference System", "Smart Display", "Enterprise WiFi"],
            "amenity_keys": ["Air Conditioning", "Audio-Visual System", "Smart Board"],
        },
        "LAB-301": {
            "building": "Block A - Computing & AI Block",
            "capacity": 30,
            "room_type": "lab",
            "equipment": ["Computer Workstations (30x)", "Gigabit Switch", "Whiteboard"],
            "amenity_keys": ["Air Conditioning", "High-Speed WiFi"],
        },
        "LAB-302": {
            "building": "Block A - Computing & AI Block",
            "capacity": 30,
            "room_type": "lab",
            "equipment": ["Computer Workstations (30x)", "Gigabit Switch", "Whiteboard"],
            "amenity_keys": ["Air Conditioning", "High-Speed WiFi"],
        },
    }

    for r_num, spec in existing_rooms_data.items():
        room = Room.objects.filter(room_number=r_num).first()
        if room:
            room.building = spec["building"]
            room.capacity = spec["capacity"]
            room.room_type = spec["room_type"]
            room.equipment = spec["equipment"]
            room.save()
            room.amenities.set([amenities[k] for k in spec["amenity_keys"] if k in amenities])

    # 4. Department Categorization Logic
    def get_school_block(d):
        name = (d.name or "").lower()
        core = (d.core_department or "").lower()

        if any(k in core or k in name for k in ["computer", "data science", "artificial intelligence", "cyber", "information technology", "software", "bca", "mca"]):
            return "A"
        elif any(k in core or k in name for k in ["pharmacy", "pharm"]):
            return "F"
        elif any(k in core or k in name for k in ["medical", "health", "hospital", "nutrition", "physiotherapy", "paramedical", "optometry", "clinical", "biomedical"]):
            return "C"
        elif any(k in core or k in name for k in ["mechanical", "civil", "electrical", "electronics", "chemical", "textile", "leather", "robotics", "food technology", "engineering"]):
            return "B"
        elif any(k in core or k in name for k in ["business", "management", "bba", "mba", "commerce", "finance", "marketing", "apparel"]):
            return "D"
        elif any(k in core or k in name for k in ["physics", "math", "chemistry", "biology", "biotechnology", "life sciences", "environmental", "forensic", "genetics"]):
            return "E"
        elif any(k in core or k in name for k in ["media", "film", "animation", "journalism", "mass communication", "fashion", "design", "architecture", "b.arch", "m.arch"]):
            return "G"
        elif any(k in core or k in name for k in ["humanities", "psychology", "english", "history", "economics", "law", "social"]):
            return "H"
        else:
            return "I"

    # Group all departments by their block
    depts_by_block = {"A": [], "B": [], "C": [], "D": [], "E": [], "F": [], "G": [], "H": [], "I": []}
    for dept in Department.objects.all():
        b_key = get_school_block(dept)
        depts_by_block[b_key].append(dept)

    # 5. Define Academic Blocks and Standard Room Templates
    blocks_meta = {
        "A": {
            "name": "Block A - Computing & AI Block",
            "lab_equipment": ["AI GPU Workstations (40x)", "Gigabit LAN Switch", "Smart 4K Projector", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Smart Board"],
        },
        "B": {
            "name": "Block B - Engineering & Technology Block",
            "lab_equipment": ["Engineering Workbenches", "Oscilloscopes & Power Supplies", "Safety Stations", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "High-Speed WiFi"],
        },
        "C": {
            "name": "Block C - Health & Allied Medical Sciences Block",
            "lab_equipment": ["Clinical Diagnostic Kits", "Optical Microscopes (30x)", "Specimen Prep Benches", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "D": {
            "name": "Block D - Business & Management Block",
            "lab_equipment": ["Financial Bloomberg Terminals (35x)", "Interactive Projector", "Dual Whiteboards"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Smart Board"],
        },
        "E": {
            "name": "Block E - Basic & Applied Sciences Block",
            "lab_equipment": ["Fume Hoods & Chemical Benches", "Centrifuges & Incubators", "Lab Safety Eyewash", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "F": {
            "name": "Block F - Pharmacy & Pharmaceutical Sciences Block",
            "lab_equipment": ["Analytical Spectrophotometers", "Tablet Dissolution Testers", "Compound Benches", "Safety Stations"],
            "lab_amenities": ["Air Conditioning", "Lab Safety Stations", "Wheelchair Accessible"],
        },
        "G": {
            "name": "Block G - Media, Design & Architecture Block",
            "lab_equipment": ["Drawing Drafting Tables (35x)", "Color-Calibrated Mac Workstations", "4K Video Editing Suites"],
            "lab_amenities": ["Air Conditioning", "High-Speed WiFi", "Audio-Visual System"],
        },
        "H": {
            "name": "Block H - Humanities & Social Sciences Block",
            "lab_equipment": ["Language Audio Lab Consoles", "Conference Projector", "Discussion Tables", "Whiteboard"],
            "lab_amenities": ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System"],
        },
        "I": {
            "name": "Block I - Hospitality, Tourism & General Studies",
            "lab_equipment": ["Hotel Front-Desk Simulation Consoles", "Culinary Demo Stations", "Projection System"],
            "lab_amenities": ["Air Conditioning", "Wheelchair Accessible", "High-Speed WiFi"],
        },
    }

    # Generate 12 standard rooms for each block (A-101 to I-304)
    for b_key, b_info in blocks_meta.items():
        b_name = b_info["name"]
        assigned_depts = depts_by_block[b_key]

        room_blueprints = [
            # Floor 1: Large Lecture Halls
            (f"{b_key}-101", 80, "lecture", ["Smart 4K Projector", "Podium Mic & PA System", "Dual Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "Smart Board"]),
            (f"{b_key}-102", 60, "lecture", ["Smart Projector", "PA Audio System", "Dual Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System"]),
            (f"{b_key}-103", 60, "lecture", ["Smart Projector", "Dual Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Wheelchair Accessible"]),
            (f"{b_key}-104", 60, "lecture", ["Smart Projector", "Dual Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Wheelchair Accessible"]),
            # Floor 2: Medium Lecture Halls
            (f"{b_key}-201", 60, "lecture", ["Smart Projector", "Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Audio-Visual System"]),
            (f"{b_key}-202", 60, "lecture", ["Smart Projector", "Whiteboard", "High-Speed WiFi"], ["Air Conditioning", "Audio-Visual System"]),
            (f"{b_key}-203", 60, "lecture", ["Smart Projector", "Whiteboard", "High-Speed WiFi"], ["Air Conditioning"]),
            (f"{b_key}-204", 50, "lecture", ["Smart Projector", "Whiteboard", "High-Speed WiFi"], ["Air Conditioning"]),
            # Floor 3: Specialized Laboratories & Seminar Rooms
            (f"{b_key}-301", 40, "lab", b_info["lab_equipment"], b_info["lab_amenities"]),
            (f"{b_key}-302", 35, "lab", b_info["lab_equipment"], b_info["lab_amenities"]),
            (f"{b_key}-303", 35, "lab", b_info["lab_equipment"], b_info["lab_amenities"]),
            (f"{b_key}-304", 30, "seminar", ["Video Conference System", "Smart Touchscreen Display", "Executive Board Seating", "High-Speed WiFi"], ["Air Conditioning", "Wheelchair Accessible", "Audio-Visual System", "Smart Board"]),
        ]

        for r_num, cap, r_type, equip, am_keys in room_blueprints:
            room, created = Room.objects.get_or_create(
                room_number=r_num,
                defaults={
                    "capacity": cap,
                    "building": b_name,
                    "room_type": r_type,
                    "equipment": equip,
                },
            )
            if not created:
                room.capacity = cap
                room.building = b_name
                room.room_type = r_type
                room.equipment = equip
                room.save()

            # Assign amenities
            room.amenities.set([amenities[k] for k in am_keys if k in amenities])

            # Assign departments
            # All rooms in the block are accessible to the departments in that school
            room.departments.set(assigned_depts)


def remove_campus_blocks_and_rooms(apps, schema_editor):
    Room = apps.get_model("scheduler", "Room")
    import re
    # Remove generated rooms (A-101 through I-304)
    pattern = r"^[A-I]-[1-3]0[1-4]$"
    all_rooms = Room.objects.all()
    for r in all_rooms:
        if re.match(pattern, r.room_number):
            r.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("scheduler", "0017_subject_elective_group_studentelectiveenrollment"),
    ]

    operations = [
        migrations.RunPython(seed_campus_blocks_and_rooms, reverse_code=remove_campus_blocks_and_rooms),
    ]

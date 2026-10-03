from .breaks import normalize_breaks, slot_overlaps_break
from .csp_solver import ScheduleCSP
from .models import Room, Subject, TimeSlot, TimetableEntry, TimetableVersion, Resource


def generate_timetable_task(config):
    """
    Background task to generate a timetable.
    """
    # Filter subjects
    subject_qs = Subject.objects.select_related("faculty")
    subject_ids = config.get("subject_ids")
    if subject_ids:
        subject_qs = subject_qs.filter(id__in=subject_ids)

    subject_qs = subject_qs.prefetch_related("resources")
    subjects = []
    for s in subject_qs:
        subjects.append({
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "faculty_id": s.faculty_id,
            "required_capacity": s.required_capacity,
            "sessions_per_week": s.sessions_per_week,
            "resource_ids": list(s.resources.values_list('id', flat=True)),
            "required_tas": s.required_tas,
        })

    # Filter rooms
    room_qs = Room.objects.all()
    room_ids = config.get("room_ids")
    if room_ids:
        room_qs = room_qs.filter(id__in=room_ids)

    rooms = list(room_qs.values("id", "room_number", "capacity", "room_type"))

    # Get all time slots for the solver's reference map, to avoid KeyError on locked entries
    all_time_slots = list(TimeSlot.objects.all().values("id", "day", "start_time", "end_time"))
    
    timeslot_ids = config.get("timeslot_ids")
    timeslot_ids_set = set(timeslot_ids) if timeslot_ids else {ts["id"] for ts in all_time_slots}

    custom_breaks = normalize_breaks(config.get("custom_breaks"))
    
    valid_time_slots = []
    for ts in all_time_slots:
        if ts["id"] not in timeslot_ids_set:
            continue
        if custom_breaks and slot_overlaps_break(ts["start_time"], ts["end_time"], custom_breaks):
            continue
        valid_time_slots.append(ts)

    if not valid_time_slots:
        return {"success": False, "error": "Every selected time slot falls inside a break or none selected."}
        
    invalid_ts_ids = {ts["id"] for ts in all_time_slots} - {ts["id"] for ts in valid_time_slots}

    # Fetch Resources
    resources = list(Resource.objects.values("id", "name", "quantity"))

    # Validate
    if not subjects or not rooms or not valid_time_slots:
        return {"success": False, "error": "Missing subjects, rooms, or time slots."}

    # Parse advanced constraints
    locked_entries = config.get("locked_entries", [])
    
    # Add DB locked entries
    db_locked_qs = TimetableEntry.objects.filter(is_locked=True)
    db_locked_set = set()
    for le in db_locked_qs:
        le_dict = {
            "subject_id": le.subject_id,
            "room_id": le.room_id,
            "time_slot_id": le.time_slot_id
        }
        if le_dict not in locked_entries:
            locked_entries.append(le_dict)
        db_locked_set.add((le.subject_id, le.room_id, le.time_slot_id))

    excluded_slots = config.get("excluded_slots", {})
    preferred_room_types = config.get("preferred_room_types", {})
    avoid_back_to_back = config.get("avoid_back_to_back", False)
    max_classes_per_day = config.get("max_classes_per_day", 1)
    balance_faculty_workload = config.get("balance_faculty_workload", False)
    auto_schedule_office_hours = config.get("auto_schedule_office_hours", False)
    exam_mode = config.get("exam_mode", False)

    if exam_mode:
        for s in subjects:
            s["sessions_per_week"] = 1
            
    # Convert dict keys to int
    excluded_slots_int = {
        int(k): [int(x) for x in v] for k, v in excluded_slots.items()
    }
    
    # Exclude invalid time slots for all subjects so the solver won't use them
    if invalid_ts_ids:
        invalid_ts_list = list(invalid_ts_ids)
        for s in subjects:
            sid = s["id"]
            if sid not in excluded_slots_int:
                excluded_slots_int[sid] = []
            excluded_slots_int[sid].extend(invalid_ts_list)
            
    pref_room_types_int = {int(k): v for k, v in preferred_room_types.items()}

    # Run CSP solver
    solver = ScheduleCSP(
        subjects,
        rooms,
        all_time_slots,
        resources=resources,
        locked_entries=locked_entries,
        excluded_slots=excluded_slots_int,
        preferred_room_types=pref_room_types_int,
        avoid_back_to_back=avoid_back_to_back,
        max_classes_per_day=max_classes_per_day,
        balance_faculty_workload=balance_faculty_workload,
    )
    timetable = solver.get_timetable()

    if not timetable:
        error_msg = "Could not generate a conflict-free timetable."
        if solver.last_failure_reason:
            error_msg += f" Reason: {solver.last_failure_reason}"
        return {
            "success": False,
            "error": error_msg,
        }

    version_id = config.get("version_id")
    draft_name = config.get("draft_name", "Draft")

    # If version_id is provided, we update that version, else we create a new one
    if version_id:
        version = TimetableVersion.objects.filter(id=version_id).first()
        if not version:
            return {"success": False, "error": "Invalid version ID."}
    else:
        # Create a new version
        version = TimetableVersion.objects.create(name=draft_name, is_published=False)

    # If updating an existing version, clear its unlocked entries
    TimetableEntry.objects.filter(version=version, is_locked=False).delete()
    
    entries = []
    for entry in timetable:
        tup = (entry["subject_id"], entry["room_id"], entry["time_slot_id"])
        if tup not in db_locked_set:
            entries.append(
                TimetableEntry(
                    version=version,
                    subject_id=entry["subject_id"],
                    room_id=entry["room_id"],
                    time_slot_id=entry["time_slot_id"],
                    event_type="exam" if exam_mode else "class",
                    event_title="Exam" if exam_mode else "",
                    is_locked=False
                )
            )
            
    if auto_schedule_office_hours:
        faculty_ids = {s["faculty_id"] for s in subjects if s["faculty_id"]}
        used_room_slots = {(e.room_id, e.time_slot_id) for e in entries}
        for fac_id in faculty_ids:
            busy_slots = {e.time_slot_id for e in entries if getattr(e, "subject_id", None) and next((s for s in subjects if s["id"] == e.subject_id), {}).get("faculty_id") == fac_id}
            assigned = False
            for ts in valid_time_slots:
                if ts["id"] in busy_slots:
                    continue
                for room in rooms:
                    if (room["id"], ts["id"]) not in used_room_slots:
                        entries.append(
                            TimetableEntry(
                                version=version,
                                event_title="Office Hours",
                                event_type="office_hours",
                                event_color="#10b981",
                                faculty_id=fac_id,
                                room_id=room["id"],
                                time_slot_id=ts["id"],
                                is_locked=False
                            )
                        )
                        used_room_slots.add((room["id"], ts["id"]))
                        assigned = True
                        break
                if assigned:
                    break
                    
    created_entries = TimetableEntry.objects.bulk_create(entries)

    # TA Assignment
    from apps.accounts.models import Student
    available_tas = list(Student.objects.filter(is_ta=True).prefetch_related('ta_qualified_subjects'))
    ta_assignments = []
    
    # Postgres bulk_create sets IDs on the returned objects
    for entry in created_entries:
        if not entry.subject_id:
            continue
        subj_req_tas = next((s['required_tas'] for s in subjects if s['id'] == entry.subject_id), 0)
        if subj_req_tas > 0:
            assigned = 0
            for ta in available_tas:
                if assigned >= subj_req_tas:
                    break
                qualified_ids = [s.id for s in ta.ta_qualified_subjects.all()]
                if entry.subject_id in qualified_ids:
                    # In a full implementation, check time conflicts and max hours here
                    ta_assignments.append(TimetableEntry.teaching_assistants.through(
                        timetableentry_id=entry.id,
                        student_id=ta.id
                    ))
                    assigned += 1
                    
    if ta_assignments:
        TimetableEntry.teaching_assistants.through.objects.bulk_create(ta_assignments)

    return {"success": True, "count": len(entries), "version_id": version.id, "version_name": version.name}

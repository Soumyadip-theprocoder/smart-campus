import json

from .csp_solver import ScheduleCSP
from .models import Room, Subject, TimeSlot, TimetableEntry


def generate_timetable_task(config):
    """
    Background task to generate a timetable.
    """
    # Filter subjects
    subject_qs = Subject.objects.select_related("faculty")
    subject_ids = config.get("subject_ids")
    if subject_ids:
        subject_qs = subject_qs.filter(id__in=subject_ids)

    subjects = list(
        subject_qs.values(
            "id",
            "code",
            "name",
            "faculty_id",
            "required_capacity",
            "sessions_per_week",
        )
    )

    # Filter rooms
    room_qs = Room.objects.all()
    room_ids = config.get("room_ids")
    if room_ids:
        room_qs = room_qs.filter(id__in=room_ids)

    rooms = list(room_qs.values("id", "room_number", "capacity", "room_type"))

    # Filter time slots
    ts_qs = TimeSlot.objects.all()
    timeslot_ids = config.get("timeslot_ids")
    if timeslot_ids:
        ts_qs = ts_qs.filter(id__in=timeslot_ids)

    time_slots = list(ts_qs.values("id", "day", "start_time", "end_time"))

    # Validate
    if not subjects or not rooms or not time_slots:
        return {"success": False, "error": "Missing subjects, rooms, or time slots."}

    # Parse advanced constraints
    locked_entries = config.get("locked_entries", [])
    excluded_slots = config.get("excluded_slots", {})
    preferred_room_types = config.get("preferred_room_types", {})
    avoid_back_to_back = config.get("avoid_back_to_back", False)
    max_classes_per_day = config.get("max_classes_per_day", 1)

    # Convert dict keys to int
    excluded_slots_int = {
        int(k): [int(x) for x in v] for k, v in excluded_slots.items()
    }
    pref_room_types_int = {int(k): v for k, v in preferred_room_types.items()}

    # Run CSP solver
    solver = ScheduleCSP(
        subjects,
        rooms,
        time_slots,
        locked_entries=locked_entries,
        excluded_slots=excluded_slots_int,
        preferred_room_types=pref_room_types_int,
        avoid_back_to_back=avoid_back_to_back,
        max_classes_per_day=max_classes_per_day,
    )
    timetable = solver.get_timetable()

    if not timetable:
        return {
            "success": False,
            "error": "Could not generate a conflict-free timetable.",
        }

    # Clear & create new timetable
    TimetableEntry.objects.all().delete()
    entries = [
        TimetableEntry(
            subject_id=entry["subject_id"],
            room_id=entry["room_id"],
            time_slot_id=entry["time_slot_id"],
        )
        for entry in timetable
    ]
    TimetableEntry.objects.bulk_create(entries)

    return {"success": True, "count": len(entries)}

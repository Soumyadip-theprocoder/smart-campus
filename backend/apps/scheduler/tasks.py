"""
Timetable generation tasks.

Orchestrates OR-Tools CP-SAT solver runs for single-department,
academic-block, or campus-wide scheduling scopes.  Phase 17 adds
wave orchestration, cohort non-overlap, common course merging,
2-hour lab blocks, and block-affinity routing.
"""

import logging
import time
from collections import defaultdict

from django.db.models import Q
from .breaks import normalize_breaks, slot_overlaps_break
from .ortools_adapter import ORToolsSolverAdapter
from .solver_interface import SolverInput
from .models import Room, Subject, TimeSlot, TimetableEntry, TimetableVersion, Resource, Department, InstitutionSettings

logger = logging.getLogger(__name__)


# ── Academic Block definitions ──────────────────────────────────────
ACADEMIC_BLOCKS = {
    "Block A": "Computing & AI",
    "Block B": "Engineering",
    "Block C": "Basic & Applied Sciences",
    "Block D": "Health Sciences",
    "Block E": "Management & Commerce",
    "Block F": "Law & Social Sciences",
    "Block G": "Arts & Humanities",
    "Block H": "Agriculture & Environmental Sciences",
    "Block I": "Interdisciplinary Studies",
}


def _identify_merge_groups(subjects):
    """Identify common courses across departments by matching subject codes.

    Subjects with the same code prefix (first 6 chars) assigned to multiple
    departments are candidates for merging. Returns a dict mapping
    merge_group_id -> list of subject dicts.
    """
    code_depts = defaultdict(list)
    for s in subjects:
        dept_ids = s.get("department_ids", [])
        if len(dept_ids) > 1:
            code_depts[s["code"]].append(s)

    merge_groups = {}
    for code, subjs in code_depts.items():
        if len(subjs) >= 1 and len(subjs[0].get("department_ids", [])) > 1:
            mg_id = f"MG-{code}"
            merge_groups[mg_id] = subjs
            for s in subjs:
                s["merge_group_id"] = mg_id

    return merge_groups


def _build_subject_dicts(subject_qs, merge_common_courses=False, allow_spillover=False):
    """Convert Subject queryset to solver-ready dicts with Phase 17 fields."""
    central_room_ids = set(
        Room.objects.filter(
            building__icontains="Central", room_type__in=["seminar", "lecture"]
        ).values_list("id", flat=True)
    )

    # Precompute department -> room_ids and department -> block_name to eliminate N+1 queries
    dept_room_map = defaultdict(set)
    dept_building_map = defaultdict(str)
    for r in Room.objects.prefetch_related("departments").all():
        for d in r.departments.all():
            dept_room_map[d.id].add(r.id)
            if not dept_building_map[d.id] and r.building and r.building.startswith("Block"):
                dept_building_map[d.id] = r.building

    subjects = []
    for s in subject_qs:
        dept_ids = [d.id for d in s.departments.all()]
        resource_ids = [res.id for res in s.resources.all()]

        # Determine allowed_blocks from all departments' rooms or buildings
        allowed_blocks = set()
        primary_block = ""
        for d_id in dept_ids:
            b = dept_building_map.get(d_id)
            if b:
                allowed_blocks.add(b)
                if not primary_block:
                    primary_block = b

        # Determine allowed room IDs (rooms assigned to subject's departments
        # plus any central/seminar rooms)
        if dept_ids:
            allowed_room_ids = set()
            for d_id in dept_ids:
                allowed_room_ids.update(dept_room_map.get(d_id, set()))
            allowed_room_ids.update(central_room_ids)
        else:
            allowed_room_ids = None

        subj_dict = {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "faculty_id": s.faculty_id,
            # Lab subjects use practical batch capacity (30) rather than whole lecture cohort capacity
            "required_capacity": 30 if s.subject_type == "lab" and s.required_capacity > 35 else s.required_capacity,
            "sessions_per_week": s.sessions_per_week,
            "resource_ids": resource_ids,
            "required_tas": s.required_tas,
            "elective_group_id": s.elective_group_id if hasattr(s, 'elective_group_id') else None,
            "semester": s.semester,
            # Phase 17 fields
            "is_lab": s.subject_type == "lab",
            "block_name": primary_block,
            "allowed_blocks": allowed_blocks,
            "department_ids": dept_ids,
            "subject_type": s.subject_type,
        }

        # Only set hard allowed_room_ids if departments are assigned and spillover is NOT enabled.
        # (When allow_spillover is True, block affinity is guided via the solver's PENALTY_SPILLOVER).
        if allowed_room_ids is not None and not allow_spillover:
            subj_dict["allowed_room_ids"] = allowed_room_ids

        # Set cohort_key for each department+semester combination
        if dept_ids and s.semester:
            # Use first department as the primary cohort
            subj_dict["cohort_key"] = (dept_ids[0], s.semester)

        subjects.append(subj_dict)

    return subjects


def estimate_generation_eta(config):
    """
    Estimate the execution duration and load category based on real database volume.
    """
    scope_type = config.get("scope_type", "department")
    dept_id = config.get("department_id")
    semester = config.get("semester")
    block_name = config.get("block_name")
    term = config.get("term")

    # If department scope with no specific department selected, auto-upgrade to whole campus
    if scope_type == "department" and not dept_id:
        scope_type = "all"

    from apps.scheduler.models import Department

    if scope_type == "department":
        if semester:
            base_eta = 3.0
            load_label = "Low Load (Single Cohort ~2–4s)"
        else:
            base_eta = 6.0
            load_label = "Moderate Load (Department ~4–8s)"
    elif scope_type == "block":
        dept_count = Department.objects.filter(rooms__building__icontains=block_name).values("id").distinct().count() if block_name else 25
        dept_count = max(4, dept_count)
        base_eta = round(dept_count * 1.5, 1)
        load_label = f"High Load ({dept_count} Block Waves, ~{int(base_eta // 60)}m {int(base_eta % 60)}s)" if base_eta >= 60 else f"High Load ({dept_count} Block Waves, ~{int(base_eta)}s)"
    else:  # "all" (Whole Campus)
        dept_count = Department.objects.count() or 178
        term_factor = 0.55 if term in ("odd", "even") else 1.0
        est_waves = round(dept_count * 0.92 * term_factor)
        base_eta = round(est_waves * 1.4, 1)  # ~160 waves * 1.4s = ~224s (~3.5 minutes)
        mins = int(base_eta // 60)
        secs = int(base_eta % 60)
        load_label = f"Enterprise Campus Master (~{est_waves} Waves, ~{mins}m {secs}s)"

    multiplier = 1.0
    if config.get("balance_faculty_workload"):
        multiplier += 0.10
    if config.get("consecutive_labs"):
        multiplier += 0.05
    if config.get("avoid_back_to_back"):
        multiplier += 0.05

    total_eta = round(base_eta * multiplier, 1)

    if total_eta < 60:
        formatted = f"~{int(total_eta)}s"
    elif total_eta < 3600:
        mins = int(total_eta // 60)
        secs = int(total_eta % 60)
        formatted = f"~{mins}m {secs}s" if secs else f"~{mins}m"
    else:
        hrs = int(total_eta // 3600)
        mins = int((total_eta % 3600) // 60)
        formatted = f"~{hrs}h {mins}m"

    return {
        "estimated_seconds": total_eta,
        "formatted_eta": formatted,
        "load_label": load_label,
        "effective_scope_type": scope_type,
    }


def _update_progress(tracking_id, **kwargs):
    """Safely update task progress in the database."""
    if not tracking_id:
        return
    try:
        from apps.scheduler.models import SchedulerTaskProgress
        from django.utils import timezone
        kwargs["updated_at"] = timezone.now()
        SchedulerTaskProgress.objects.filter(task_id=tracking_id).update(**kwargs)
    except Exception as e:
        logger.warning("Could not update task progress for %s: %s", tracking_id, e)


def _is_cancelled(tracking_id):
    """Check if task has been marked as cancelled in the database."""
    if not tracking_id:
        return False
    try:
        from apps.scheduler.models import SchedulerTaskProgress
        return SchedulerTaskProgress.objects.filter(task_id=tracking_id, status="cancelled").exists()
    except Exception:
        return False


def generate_timetable_task(config):
    """
    Background task to generate a timetable.
    Uses the OR-Tools CP-SAT solver via the hexagonal solver interface.

    Phase 17: Supports multi-department wave orchestration with scope types:
      - "department": Single department + optional semester
      - "block": All departments in an academic block
      - "all": Campus-wide (all departments, all blocks)
    """
    tracking_id = config.get("tracking_id") or config.get("task_id")
    t_start = time.time()

    # Parse scope & auto-switch if department scope is passed with no department_id
    scope_type = config.get("scope_type", "department")
    department_id = config.get("department_id")
    if scope_type == "department" and not department_id:
        scope_type = "all"
        config["scope_type"] = "all"

    _update_progress(
        tracking_id,
        status="running",
        start_time=t_start,
        percent=5.0,
        current_wave_name="Filtering subjects and rooms for scope...",
    )

    block_name = config.get("block_name")
    semester = config.get("semester")
    merge_common_courses = config.get("merge_common_courses", False)
    consecutive_labs = config.get("consecutive_labs", False)
    allow_spillover = config.get("allow_spillover", False)

    # Filter subjects based on scope
    subject_qs = Subject.objects.select_related("faculty").prefetch_related(
        "resources", "departments"
    )
    subject_ids = config.get("subject_ids")

    term = config.get("term")
    if term == "odd":
        subject_qs = subject_qs.filter(semester__in=[1, 3, 5, 7, 9])
    elif term == "even":
        subject_qs = subject_qs.filter(semester__in=[2, 4, 6, 8, 10])

    if scope_type == "department" and department_id:
        subject_qs = subject_qs.filter(departments__id=department_id)
        if semester:
            subject_qs = subject_qs.filter(semester=semester)
        if subject_ids:
            subject_qs = subject_qs.filter(id__in=subject_ids)
    elif scope_type == "block" and block_name:
        # Find all departments with rooms in this block
        block_dept_ids = Department.objects.filter(
            rooms__building__icontains=block_name
        ).values_list("id", flat=True).distinct()
        if block_dept_ids:
            subject_qs = subject_qs.filter(departments__id__in=block_dept_ids)
        else:
            err = f"No departments found for block '{block_name}'."
            _update_progress(tracking_id, status="failed", error=err, elapsed_seconds=round(time.time() - t_start, 1))
            return {"success": False, "error": err}
        if semester:
            subject_qs = subject_qs.filter(semester=semester)
        if subject_ids:
            subject_qs = subject_qs.filter(id__in=subject_ids)
    elif scope_type == "all":
        # Whole campus: schedule all subjects across campus for the chosen term/semester
        if semester:
            subject_qs = subject_qs.filter(semester=semester)
    elif subject_ids:
        # Fallback if specific subject_ids passed without scope
        subject_qs = subject_qs.filter(id__in=subject_ids)
        if semester:
            subject_qs = subject_qs.filter(semester=semester)
    elif semester:
        subject_qs = subject_qs.filter(semester=semester)

    subject_qs = subject_qs.distinct()

    # Build subject dicts with Phase 17 fields
    subjects = _build_subject_dicts(subject_qs, merge_common_courses, allow_spillover=allow_spillover)

    if not subjects:
        return {"success": False, "error": "No subjects found for the selected scope."}

    # Identify merge groups if enabled
    if merge_common_courses:
        _identify_merge_groups(subjects)

    # Filter rooms by scope
    room_qs = Room.objects.all()
    room_ids = config.get("room_ids")
    if scope_type == "department" and department_id:
        if room_ids:
            room_qs = room_qs.filter(id__in=room_ids)
        else:
            room_qs = room_qs.filter(
                Q(departments__id=department_id) | Q(building__icontains="Central", room_type__in=["seminar", "lecture"])
            ).distinct()
    elif scope_type == "block" and block_name:
        if allow_spillover:
            room_qs = Room.objects.all()
        else:
            room_qs = room_qs.filter(
                Q(building__icontains=block_name) | Q(building__icontains="Central", room_type__in=["seminar", "lecture"])
            ).distinct()
        if not room_qs.exists():
            return {"success": False, "error": f"No rooms found for block '{block_name}'."}
    elif scope_type == "all":
        room_qs = Room.objects.all()
    elif room_ids:
        room_qs = room_qs.filter(id__in=room_ids)


    rooms = []
    for r in room_qs:
        room_dict = {
            "id": r.id,
            "room_number": r.room_number,
            "capacity": r.capacity,
            "room_type": r.room_type,
            "building": r.building,
            "block_name": r.building if r.building and r.building.startswith("Block") else "",
        }
        rooms.append(room_dict)

    # Get all time slots for the solver's reference map (interleaved hour-first ordering)
    DAY_ORDER = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
    all_time_slots = sorted(
        list(TimeSlot.objects.all().values("id", "day", "start_time", "end_time")),
        key=lambda ts: (str(ts["start_time"]), DAY_ORDER.get(ts["day"], 99))
    )

    timeslot_ids = config.get("timeslot_ids")
    timeslot_ids_set = set(timeslot_ids) if timeslot_ids else {ts["id"] for ts in all_time_slots}

    # Resolve breaks using tiered hierarchy:
    # 1. Explicit custom_breaks passed in config (unless no_breaks / clear_breaks requested)
    # 2. For single department scope: Department.default_breaks (falling back to InstitutionSettings.default_breaks)
    # 3. For campus-wide and block scopes: InstitutionSettings.default_breaks
    custom_breaks = normalize_breaks(config.get("custom_breaks"))
    if not custom_breaks and not (config.get("no_breaks") or config.get("clear_breaks")):
        if scope_type == "department" and department_id:
            try:
                dept_obj = Department.objects.filter(id=department_id).first()
                if dept_obj and dept_obj.default_breaks:
                    custom_breaks = normalize_breaks(dept_obj.default_breaks)
            except Exception as e:
                logger.warning(f"Failed to fetch department default_breaks: {e}")

        if not custom_breaks:
            try:
                inst_settings = InstitutionSettings.objects.first()
                if inst_settings and inst_settings.default_breaks:
                    custom_breaks = normalize_breaks(inst_settings.default_breaks)
            except Exception as e:
                logger.warning(f"Failed to fetch institution default_breaks: {e}")

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
    if not rooms or not valid_time_slots:
        return {"success": False, "error": "Missing rooms or time slots."}

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
        int(k): [int(x_val) for x_val in v] for k, v in excluded_slots.items()
    }

    # Exclude invalid time slots for all subjects
    if invalid_ts_ids:
        invalid_ts_list = list(invalid_ts_ids)
        for s in subjects:
            sid = s["id"]
            if sid not in excluded_slots_int:
                excluded_slots_int[sid] = []
            excluded_slots_int[sid].extend(invalid_ts_list)

    pref_room_types_int = {int(k): v for k, v in preferred_room_types.items()}

    # ── Wave orchestration for multi-department scheduling ──────────
    if (scope_type in ("all", "block") and len(subjects) > 50) or len(subjects) > 60:
        # Group subjects by block for wave solving
        return _wave_solve(
            subjects=subjects,
            rooms=rooms,
            all_time_slots=all_time_slots,
            valid_time_slots=valid_time_slots,
            resources=resources,
            locked_entries=locked_entries,
            excluded_slots_int=excluded_slots_int,
            pref_room_types_int=pref_room_types_int,
            avoid_back_to_back=avoid_back_to_back,
            max_classes_per_day=max_classes_per_day,
            balance_faculty_workload=balance_faculty_workload,
            auto_schedule_office_hours=auto_schedule_office_hours,
            merge_common_courses=merge_common_courses,
            consecutive_labs=consecutive_labs,
            allow_spillover=allow_spillover,
            config=config,
            db_locked_set=db_locked_set,
            tracking_id=tracking_id,
            t_start=t_start,
        )

    # ── Single-pass solve (department or small scale) ───────────────
    _update_progress(
        tracking_id,
        total_waves=1,
        current_wave=1,
        current_wave_name=f"Solving timetable ({len(subjects)} subjects)...",
        percent=30.0,
    )
    solver_input = SolverInput(
        subjects=subjects,
        rooms=rooms,
        time_slots=all_time_slots,
        resources=resources,
        locked_entries=locked_entries,
        excluded_slots=excluded_slots_int,
        preferred_room_types=pref_room_types_int,
        avoid_back_to_back=avoid_back_to_back,
        max_classes_per_day=max_classes_per_day,
        balance_faculty_workload=balance_faculty_workload,
        merge_common_courses=merge_common_courses,
        consecutive_labs=consecutive_labs,
        allow_spillover=allow_spillover,
    )

    if _is_cancelled(tracking_id):
        return {"success": False, "cancelled": True, "error": "Timetable generation was cancelled by user."}

    solver = ORToolsSolverAdapter(solver_input)
    result = solver.solve()

    if _is_cancelled(tracking_id):
        return {"success": False, "cancelled": True, "error": "Timetable generation was cancelled by user."}

    if not result.success:
        err = result.error or "Could not generate a conflict-free timetable."
        _update_progress(tracking_id, status="failed", error=err, elapsed_seconds=round(time.time() - t_start, 1))
        return {
            "success": False,
            "error": err,
        }

    _update_progress(
        tracking_id,
        percent=85.0,
        sessions_scheduled=len(result.timetable),
        current_wave_name="Saving timetable entries to database...",
    )

    return _save_timetable(
        result=result,
        config=config,
        subjects=subjects,
        rooms=rooms,
        valid_time_slots=valid_time_slots,
        db_locked_set=db_locked_set,
        auto_schedule_office_hours=auto_schedule_office_hours,
        exam_mode=exam_mode,
        tracking_id=tracking_id,
        t_start=t_start,
    )


def _wave_solve(
    subjects, rooms, all_time_slots, valid_time_slots=None, resources=None,
    locked_entries=None, excluded_slots_int=None, pref_room_types_int=None,
    avoid_back_to_back=False, max_classes_per_day=1, balance_faculty_workload=False,
    auto_schedule_office_hours=False, merge_common_courses=False,
    consecutive_labs=False, allow_spillover=True, config=None, db_locked_set=None,
    tracking_id=None, t_start=None,
):
    """
    Multi-department wave orchestrator.

    Splits subjects into waves by their block_name, solves each wave
    sequentially, and propagates locked reservations (room+timeslot
    assignments from completed waves) into subsequent waves.
    """
    if valid_time_slots is None:
        valid_time_slots = all_time_slots
    resources = resources or []
    locked_entries = locked_entries or []
    excluded_slots_int = excluded_slots_int or {}
    pref_room_types_int = pref_room_types_int or {}
    config = config or {}
    db_locked_set = db_locked_set or set()

    # Form cohesive department waves without splitting single cohorts across waves
    block_name = config.get("block_name")
    scoped_dept_ids = set()
    if block_name:
        scoped_dept_ids = set(
            Department.objects.filter(rooms__building__icontains=block_name)
            .values_list("id", flat=True)
            .distinct()
        )

    dept_groups = defaultdict(list)
    no_dept = []
    for s in subjects:
        ck = s.get("cohort_key")
        ck_dept = ck[0] if (ck and isinstance(ck, (list, tuple)) and ck[0]) else None
        d_ids = s.get("department_ids", [])

        target_dept = ck_dept
        if scoped_dept_ids and (target_dept not in scoped_dept_ids):
            # Prefer a department in the scoped block for this shared course
            in_scope = [d for d in d_ids if d in scoped_dept_ids]
            if in_scope:
                target_dept = in_scope[0]

        if target_dept:
            dept_groups[target_dept].append(s)
        elif d_ids:
            dept_groups[d_ids[0]].append(s)
        else:
            no_dept.append(s)

    dept_names = dict(Department.objects.values_list("id", "name"))
    waves = []
    for d_id in sorted(dept_groups.keys()):
        d_subjs = dept_groups[d_id]
        d_name = dept_names.get(d_id, f"Dept {d_id}")
        d_label = d_name[:25]

        # Keep cohort integrity intact: for departments <= 30 subjects, solve as a single wave
        if len(d_subjs) <= 30:
            waves.append((d_label, d_subjs, d_id))
        else:
            # For larger departments, group by semester clusters (e.g. Sem 1-4 vs Sem 5+)
            # so that no single cohort (department + semester) is EVER split across waves!
            sem_lower = [s for s in d_subjs if (s.get("semester") or 1) <= 4]
            sem_upper = [s for s in d_subjs if (s.get("semester") or 1) > 4]

            if len(sem_lower) > 30:
                sem_1_2 = [s for s in sem_lower if (s.get("semester") or 1) <= 2]
                sem_3_4 = [s for s in sem_lower if (s.get("semester") or 1) > 2]
                if sem_1_2:
                    waves.append((f"{d_label} (Sem 1-2)", sem_1_2, d_id))
                if sem_3_4:
                    waves.append((f"{d_label} (Sem 3-4)", sem_3_4, d_id))
            elif sem_lower:
                waves.append((f"{d_label} (Sem 1-4)", sem_lower, d_id))

            if len(sem_upper) > 30:
                sem_5_6 = [s for s in sem_upper if (s.get("semester") or 1) <= 6]
                sem_7_8 = [s for s in sem_upper if (s.get("semester") or 1) > 6]
                if sem_5_6:
                    waves.append((f"{d_label} (Sem 5-6)", sem_5_6, d_id))
                if sem_7_8:
                    waves.append((f"{d_label} (Sem 7+)", sem_7_8, d_id))
            elif sem_upper:
                waves.append((f"{d_label} (Sem 5+)", sem_upper, d_id))

    if no_dept:
        waves.append(("General Subjects", no_dept, None))

    # Precompute dept_room_map and central_room_ids for fast wave room resolution
    dept_room_map = defaultdict(set)
    for r in Room.objects.prefetch_related("departments").all():
        for d in r.departments.all():
            dept_room_map[d.id].add(r.id)
    central_room_ids = set(
        Room.objects.filter(
            building__icontains="Central", room_type__in=["seminar", "lecture"]
        ).values_list("id", flat=True)
    )

    # Solve waves sequentially, accumulating reservations
    all_timetable = []
    accumulated_locked = list(locked_entries)
    unscheduled_waves = []
    total_cohorts = 0
    total_merged = 0
    total_lab_blocks = 0
    total_waves = len(waves)
    est_initial_eta = round(total_waves * 1.4, 1)

    _update_progress(
        tracking_id,
        total_waves=total_waves,
        current_wave=0,
        percent=5.0,
        eta_remaining_seconds=est_initial_eta,
        current_wave_name=f"Starting multi-wave solver ({total_waves} waves)...",
    )

    try:
        for w_idx, (wave_label, wave_subjects, d_id) in enumerate(waves, 1):
            if _is_cancelled(tracking_id):
                print(f"--> Wave solve cancelled by user at wave {w_idx}/{total_waves}.", flush=True)
                logger.info("Task %s cancelled by user at wave %d/%d", tracking_id, w_idx, total_waves)
                break

            if not wave_subjects:
                continue

            elapsed_so_far = time.time() - t_start if t_start else 0.0
            avg_wave_sec = (elapsed_so_far / max(1, w_idx - 1)) if w_idx > 1 else 1.4
            rem_waves = max(0, total_waves - (w_idx - 1))
            in_flight_eta = max(2.0, round(rem_waves * avg_wave_sec, 1))

            _update_progress(
                tracking_id,
                total_waves=total_waves,
                current_wave=w_idx,
                eta_remaining_seconds=in_flight_eta,
                current_wave_name=f"Wave {w_idx}/{total_waves}: {wave_label}",
            )

            t_wave_start = time.time()
            print(f"--> Wave [{wave_label}]: starting with {len(wave_subjects)} subjects...", flush=True)
            logger.info("Wave solve: label=%s, subjects=%d", wave_label, len(wave_subjects))

            # Restrict rooms to this department's assigned rooms + central facilities
            scope_type = config.get("scope_type")
            if scope_type == "block":
                wave_rooms = rooms
            elif allow_spillover or scope_type == "all":
                # For whole campus or when spillover is allowed, provide all campus rooms so
                # the solver can spillover if local block rooms are saturated at a given timeslot.
                # Block affinity is preserved via PENALTY_SPILLOVER in the objective function.
                wave_rooms = rooms
            else:
                target_room_ids = (set(dept_room_map.get(d_id, set())) | central_room_ids) if d_id else set()
                if not target_room_ids or len(target_room_ids) < 8:
                    wave_blocks = {s["block_name"] for s in wave_subjects if s.get("block_name")}
                    for r in rooms:
                        r_bldg = r.get("building", "")
                        if any(wb in r_bldg for wb in wave_blocks) or "Central" in r_bldg or "Main Block" in r_bldg:
                            target_room_ids.add(r["id"])

                wave_rooms = [r for r in rooms if r["id"] in target_room_ids] if target_room_ids else rooms
            wave_room_ids = {r["id"] for r in wave_rooms}

            wave_faculty_ids = {s["faculty_id"] for s in wave_subjects if s.get("faculty_id")}

            # Filter locked reservations relevant to this wave's rooms and faculty
            wave_locked = [
                le for le in accumulated_locked
                if le.get("room_id") in wave_room_ids or (le.get("faculty_id") and le["faculty_id"] in wave_faculty_ids)
            ]

            wave_timeout = max(8.0, min(18.0, round(len(wave_subjects) * 0.22, 1)))
            solver_input = SolverInput(
                subjects=wave_subjects,
                rooms=wave_rooms,
                time_slots=all_time_slots,
                resources=resources,
                locked_entries=wave_locked,
                excluded_slots=excluded_slots_int,
                preferred_room_types=pref_room_types_int,
                avoid_back_to_back=avoid_back_to_back,
                max_classes_per_day=max_classes_per_day,
                balance_faculty_workload=balance_faculty_workload,
                merge_common_courses=merge_common_courses,
                consecutive_labs=consecutive_labs,
                allow_spillover=allow_spillover,
                max_time_in_seconds=wave_timeout,
            )

            solver = ORToolsSolverAdapter(solver_input)
            result = solver.solve()
            t_wave_end = time.time()

            if not result.success:
                # Fallback quick retry with all campus rooms and spillover enabled
                if len(wave_rooms) < len(rooms):
                    _update_progress(
                        tracking_id,
                        current_wave_name=f"Wave {w_idx}/{total_waves}: {wave_label} (Retrying with campus spillover)...",
                    )
                    print(f"--> Wave [{wave_label}]: Retrying with all campus rooms...", flush=True)
                    solver_input.rooms = rooms
                    solver_input.allow_spillover = True
                    solver_input.locked_entries = list(accumulated_locked)
                    solver_input.max_time_in_seconds = max(10.0, min(22.0, round(len(wave_subjects) * 0.28, 1)))
                    solver = ORToolsSolverAdapter(solver_input)
                    result = solver.solve()
                    t_wave_end = time.time()

            if not result.success:
                print(f"--> Wave [{wave_label}]: WARNING: Could not schedule ({result.error}). Continuing with remaining campus departments...", flush=True)
                logger.warning("Wave %s could not be scheduled: %s", wave_label, result.error)
                unscheduled_waves.append({
                    "wave": wave_label,
                    "subjects_count": len(wave_subjects),
                    "error": str(result.error or "Room/timeslot conflict"),
                })
                elapsed = time.time() - t_start if t_start else (t_wave_end - t_wave_start)
                avg_wave_sec = elapsed / max(1, w_idx)
                rem_waves = max(0, total_waves - w_idx)
                eta_sec = max(2.0, round(rem_waves * avg_wave_sec, 1)) if rem_waves > 0 else 2.0
                pct = min(94.0, round(5.0 + (w_idx / total_waves) * 88.0, 1))
                _update_progress(
                    tracking_id,
                    current_wave=w_idx,
                    sessions_scheduled=len(all_timetable),
                    percent=pct,
                    elapsed_seconds=round(elapsed, 1),
                    eta_remaining_seconds=eta_sec,
                    current_wave_name=f"Wave {w_idx}/{total_waves}: {wave_label} skipped (conflict)",
                )
                continue

            print(f"--> Wave [{wave_label}]: SUCCESS in {t_wave_end - t_wave_start:.2f}s ({len(result.timetable)} sessions assigned)", flush=True)

            all_timetable.extend(result.timetable)
            total_cohorts += result.cohort_stats
            total_merged += result.merged_sessions_count
            total_lab_blocks += result.lab_blocks_count

            elapsed = time.time() - t_start if t_start else (t_wave_end - t_wave_start)
            avg_wave_sec = elapsed / max(1, w_idx)
            rem_waves = max(0, total_waves - w_idx)
            eta_sec = max(2.0, round(rem_waves * avg_wave_sec, 1)) if rem_waves > 0 else 2.0
            pct = min(94.0, round(5.0 + (w_idx / total_waves) * 88.0, 1))

            _update_progress(
                tracking_id,
                current_wave=w_idx,
                sessions_scheduled=len(all_timetable),
                percent=pct,
                elapsed_seconds=round(elapsed, 1),
                eta_remaining_seconds=eta_sec,
                current_wave_name=f"Wave {w_idx}/{total_waves}: {wave_label} completed",
            )

            # Lock solved assignments as reservations for next waves
            for entry in result.timetable:
                accumulated_locked.append({
                    "subject_id": entry["subject_id"],
                    "faculty_id": entry.get("faculty_id"),
                    "room_id": entry["room_id"],
                    "time_slot_id": entry["time_slot_id"],
                })
    except BaseException as e:
        print(f"--> Multi-wave solve interrupted or halted ({e}). Saving {len(all_timetable)} placed sessions...", flush=True)
        logger.exception("Multi-wave loop interrupted: %s", e)
        unscheduled_waves.append({
            "wave": "Remaining waves",
            "subjects_count": 0,
            "error": f"Interrupted: {e}",
        })

    if _is_cancelled(tracking_id):
        elapsed = round(time.time() - t_start, 1) if t_start else 0.0
        ret_dict = {
            "success": False,
            "cancelled": True,
            "count": len(all_timetable),
            "error": "Timetable generation was cancelled by user.",
        }
        _update_progress(
            tracking_id,
            status="cancelled",
            error="Timetable generation was cancelled by user.",
            current_wave_name="Generation cancelled by user",
            eta_remaining_seconds=0.0,
            elapsed_seconds=elapsed,
            sessions_scheduled=len(all_timetable),
            result_data=ret_dict,
        )
        return ret_dict

    if len(all_timetable) == 0:
        err = "Could not schedule any classes across the campus waves."
        _update_progress(tracking_id, status="failed", error=err, elapsed_seconds=round(time.time() - t_start, 1))
        return {
            "success": False,
            "error": err,
        }

    # Build a combined result saving all successfully placed sessions into draft
    from .solver_interface import SolverResult
    combined_result = SolverResult(
        success=True,
        timetable=all_timetable,
        cohort_stats=total_cohorts,
        merged_sessions_count=total_merged,
        lab_blocks_count=total_lab_blocks,
    )

    exam_mode = config.get("exam_mode", False)

    return _save_timetable(
        result=combined_result,
        config=config,
        subjects=subjects,
        rooms=rooms,
        valid_time_slots=valid_time_slots,
        db_locked_set=db_locked_set,
        auto_schedule_office_hours=auto_schedule_office_hours,
        exam_mode=exam_mode,
        tracking_id=tracking_id,
        t_start=t_start,
        unscheduled_waves=unscheduled_waves,
        total_waves=total_waves,
    )


def _save_timetable(
    result, config, subjects, rooms, valid_time_slots,
    db_locked_set, auto_schedule_office_hours, exam_mode,
    tracking_id=None, t_start=None,
    unscheduled_waves=None, total_waves=None,
):
    """Save solver result to the database as TimetableEntry objects."""
    timetable = result.timetable

    version_id = config.get("version_id")
    draft_name = config.get("draft_name", "Draft")

    if version_id:
        version = TimetableVersion.objects.filter(id=version_id).first()
        if not version:
            return {"success": False, "error": "Invalid version ID."}
    else:
        version = TimetableVersion.objects.create(name=draft_name, is_published=False)

    # Clear unlocked entries for this version
    TimetableEntry.objects.filter(version=version, is_locked=False).delete()

    seen_room_slots = set()
    entries = []
    for entry in timetable:
        rs_key = (entry["room_id"], entry["time_slot_id"])
        tup = (entry["subject_id"], entry["room_id"], entry["time_slot_id"])
        if tup not in db_locked_set and rs_key not in seen_room_slots:
            seen_room_slots.add(rs_key)
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
        faculty_ids = {s["faculty_id"] for s in subjects if s.get("faculty_id")}
        used_room_slots = {(e.room_id, e.time_slot_id) for e in entries}
        # Prioritize staff rooms, cabins, and seminar rooms; fallback to lecture rooms; never use labs
        candidate_rooms = sorted(
            [r for r in rooms if (r.get("room_type") if isinstance(r, dict) else getattr(r, "room_type", "")) != "lab"],
            key=lambda r: 0 if (r.get("room_type") if isinstance(r, dict) else getattr(r, "room_type", "")) in ("staff_room", "cabin", "seminar", "office") else 1
        )
        if not candidate_rooms:
            candidate_rooms = rooms

        faculty_subject_map = {s["id"]: s["faculty_id"] for s in subjects if s.get("faculty_id")}
        for fac_id in faculty_ids:
            busy_slots = {
                e.time_slot_id for e in entries
                if e.subject_id and faculty_subject_map.get(e.subject_id) == fac_id
            }
            assigned = False
            for ts in valid_time_slots:
                if ts["id"] in busy_slots:
                    continue
                for room in candidate_rooms:
                    room_id = room["id"] if isinstance(room, dict) else room.id
                    if (room_id, ts["id"]) not in used_room_slots:
                        entries.append(
                            TimetableEntry(
                                version=version,
                                event_title="Office Hours",
                                event_type="office_hours",
                                event_color="#10b981",
                                faculty_id=fac_id,
                                room_id=room_id,
                                time_slot_id=ts["id"],
                                is_locked=False
                            )
                        )
                        used_room_slots.add((room_id, ts["id"]))
                        assigned = True
                        break
                if assigned:
                    break

    _update_progress(
        tracking_id,
        percent=96.0,
        current_wave_name="Saving timetable entries to database...",
        eta_remaining_seconds=1.5,
    )

    created_entries = TimetableEntry.objects.bulk_create(entries)

    # TA Assignment
    from apps.accounts.models import Student
    available_tas = list(Student.objects.filter(is_ta=True).prefetch_related('ta_qualified_subjects'))
    ta_assignments = []
    subject_req_tas_map = {s["id"]: s.get("required_tas", 0) for s in subjects}
    ta_qualified_map = {ta.id: set(ta.ta_qualified_subjects.values_list("id", flat=True)) for ta in available_tas}

    for entry in created_entries:
        if not entry.subject_id:
            continue
        subj_req_tas = subject_req_tas_map.get(entry.subject_id, 0)
        if subj_req_tas > 0:
            assigned = 0
            for ta in available_tas:
                if assigned >= subj_req_tas:
                    break
                if entry.subject_id in ta_qualified_map[ta.id]:
                    ta_assignments.append(TimetableEntry.teaching_assistants.through(
                        timetableentry_id=entry.id,
                        student_id=ta.id
                    ))
                    assigned += 1

    if ta_assignments:
        TimetableEntry.teaching_assistants.through.objects.bulk_create(ta_assignments)

    ret_dict = {
        "success": True,
        "count": len(entries),
        "version_id": version.id,
        "version_name": version.name,
        "cohort_stats": result.cohort_stats,
        "merged_sessions_count": result.merged_sessions_count,
        "lab_blocks_count": result.lab_blocks_count,
        "unscheduled_waves": unscheduled_waves or [],
        "total_waves": total_waves,
    }

    elapsed = round(time.time() - t_start, 1) if t_start else 0.0
    status_msg = (
        f"Timetable generated successfully! ({len(entries)} sessions)"
        if not unscheduled_waves
        else f"Draft created with {len(entries)} sessions ({len(unscheduled_waves)} conflict cohorts skipped)"
    )
    _update_progress(
        tracking_id,
        status="completed",
        percent=100.0,
        eta_remaining_seconds=0.0,
        elapsed_seconds=elapsed,
        sessions_scheduled=len(entries),
        result_data=ret_dict,
        current_wave_name=status_msg,
    )

    return ret_dict

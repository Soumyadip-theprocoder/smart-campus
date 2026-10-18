"""
Debug Middle Layer for Timetable Generator Inputs.

Intercepts, audits, formats, and persists all generator input payloads
coming from the frontend or API clients. Enables instant programmatic
and terminal inspection without requiring browser subagents.
"""

import json
import logging
import os
import time
from pathlib import Path
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("scheduler.debug")


def _get_client_ip(request):
    """Safely extract remote client IP address."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def analyze_generator_payload(payload):
    """
    Perform pre-flight analysis, validation checks, and telemetry summarization
    on an incoming timetable generator configuration payload.
    """
    from apps.scheduler.models import Department, Subject, Room, TimeSlot

    scope_type = payload.get("scope_type", "department")
    department_id = payload.get("department_id")
    block_name = payload.get("block_name")
    draft_name = payload.get("draft_name", "Untitled Draft")
    semester = payload.get("semester")
    term = payload.get("term")

    # Resolve department details if provided
    dept_name = None
    dept_code = None
    if department_id:
        try:
            d = Department.objects.filter(id=int(department_id)).first()
            if d:
                dept_name = d.name
                dept_code = d.code
        except Exception:
            pass

    # Resolve scope label
    if scope_type == "block":
        scope_label = f"Block: {block_name or 'Academic Block'}"
    elif scope_type == "all":
        scope_label = "Whole Campus (Enterprise)"
    else:
        scope_label = f"Dept: {dept_name or f'#{department_id}'}"

    # Resource Counts
    subject_ids = payload.get("subject_ids") or []
    room_ids = payload.get("room_ids") or []
    timeslot_ids = payload.get("timeslot_ids") or []
    breaks = payload.get("custom_breaks") or payload.get("breaks") or []
    excluded_slots = payload.get("excluded_slots") or {}
    preferred_rooms = payload.get("preferred_room_types") or {}
    locked_entries = payload.get("locked_entries") or []

    # Constraint flags matrix
    constraints = {
        "merge_common_courses": bool(payload.get("merge_common_courses")),
        "consecutive_labs": bool(payload.get("consecutive_labs")),
        "allow_spillover": bool(payload.get("allow_spillover")),
        "avoid_back_to_back": bool(payload.get("avoid_back_to_back")),
        "max_classes_per_day": payload.get("max_classes_per_day", 1),
        "balance_faculty_workload": bool(payload.get("balance_faculty_workload")),
        "optimize_cohort_contiguity": bool(payload.get("optimize_cohort_contiguity")),
        "exam_mode": bool(payload.get("exam_mode")),
        "office_hours_per_faculty": payload.get("office_hours_per_faculty", 0),
    }

    # Diagnostics & Pre-flight Warnings
    warnings = []
    if scope_type == "department" and not department_id:
        warnings.append("[WARN] Scope is 'department' but department_id is missing (will auto-upgrade to 'all').")
    if scope_type == "block" and not block_name:
        warnings.append("[WARN] Scope is 'block' but block_name is not specified.")
    if scope_type == "department" and len(subject_ids) == 0:
        warnings.append("[WARN] No subject_ids explicitly sent; solver will query all department courses.")
    if len(timeslot_ids) == 0:
        warnings.append("[ERROR] timeslot_ids is empty! Generation will fail unless default institution slots are used.")
    if len(breaks) > 0 and len(timeslot_ids) > 0:
        warnings.append(f"[INFO] {len(breaks)} custom break(s) active filtering time slots.")

    summary = {
        "draft_name": draft_name,
        "scope_type": scope_type,
        "scope_label": scope_label,
        "department_id": department_id,
        "department_name": dept_name,
        "department_code": dept_code,
        "block_name": block_name,
        "semester": semester,
        "term": term,
        "counts": {
            "subjects": len(subject_ids),
            "rooms": len(room_ids),
            "timeslots": len(timeslot_ids),
            "breaks": len(breaks),
            "excluded_slots": len(excluded_slots),
            "preferred_room_types": len(preferred_rooms),
            "locked_entries": len(locked_entries),
        },
        "constraints": constraints,
        "warnings": warnings,
        "is_healthy": len([w for w in warnings if w.startswith("[ERROR]")]) == 0,
    }

    return summary


def capture_generator_inputs(request, endpoint="generate", tracking_id=None):
    """
    Primary interception function.
    Audits the incoming frontend generator request, persists it to DB,
    writes a standalone JSON debug dump, and prints a formatted terminal banner.
    """
    from apps.scheduler.models import SchedulerInputLog

    if hasattr(request, "data") and request.data:
        if hasattr(request.data, "dict"):
            payload = request.data.dict()
        elif hasattr(request.data, "copy"):
            payload = dict(request.data.copy())
        else:
            payload = dict(request.data)
    else:
        payload = {}

    # Extract user & network metadata
    user = getattr(request, "user", None)
    username = user.username if (user and user.is_authenticated) else "anonymous"
    ip_addr = _get_client_ip(request)

    task_id = tracking_id or payload.get("tracking_id") or payload.get("task_id") or ""
    summary = analyze_generator_payload(payload)

    # 1. Persist to SchedulerInputLog in DB
    try:
        log_entry = SchedulerInputLog.objects.create(
            task_id=task_id,
            endpoint=endpoint,
            draft_name=summary.get("draft_name", ""),
            scope_type=summary.get("scope_type", "department"),
            scope_label=summary.get("scope_label", ""),
            department_id=summary.get("department_id"),
            block_name=summary.get("block_name") or "",
            raw_payload=payload,
            summary=summary,
            user_username=username,
            ip_address=ip_addr,
        )
    except Exception as e:
        logger.error("Failed to save SchedulerInputLog: %s", e)
        log_entry = None

    # 2. Write to local JSON dump files for immediate file-based inspection
    dump_data = {
        "captured_at": timezone.now().isoformat(),
        "task_id": task_id,
        "endpoint": endpoint,
        "user": username,
        "ip_address": ip_addr,
        "summary": summary,
        "raw_payload": payload,
    }

    try:
        dump_path = Path(settings.BASE_DIR) / "latest_generator_input.json"
        with open(dump_path, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("Could not write latest_generator_input.json: %s", e)

    # 3. Log formatted ANSI terminal banner for developers/agents viewing server output
    _print_terminal_banner(task_id, endpoint, username, ip_addr, summary)

    return {
        "log_id": log_entry.id if log_entry else None,
        "task_id": task_id,
        "summary": summary,
        "dump_data": dump_data,
    }


def _print_terminal_banner(task_id, endpoint, username, ip_addr, summary):
    """Print a clean, structured terminal summary of incoming frontend inputs safely."""
    try:
        c = summary.get("counts", {})
        ct = summary.get("constraints", {})

        banner = f"""
+------------------------------------------------------------------------+
| [INTERCEPTOR] SCHEDULER FRONTEND INPUT (Middle Layer Debug)            |
+------------------------------------------------------------------------+
  Endpoint:    /api/scheduler/{endpoint}/
  Task ID:     {task_id or 'Pre-flight / None'}
  User:        {username} ({ip_addr or 'localhost'})
  Draft Name:  {summary.get('draft_name')}
  Scope:       {summary.get('scope_label')} (type: {summary.get('scope_type')})
  Resources:   Subjects: {c.get('subjects', 0)} | Rooms: {c.get('rooms', 0)} | Slots: {c.get('timeslots', 0)} | Breaks: {c.get('breaks', 0)}
  Constraints: Consecutive Labs: {ct.get('consecutive_labs')} | Merge Common: {ct.get('merge_common_courses')}
               Avoid Back-to-Back: {ct.get('avoid_back_to_back')} | Spillover: {ct.get('allow_spillover')}
               Balance Workload: {ct.get('balance_faculty_workload')} | Max Classes/Day: {ct.get('max_classes_per_day')}
"""
        warnings = summary.get("warnings", [])
        if warnings:
            banner += "  Warnings:\n"
            for w in warnings:
                clean_w = w.encode("ascii", "replace").decode("ascii")
                banner += f"    * {clean_w}\n"

        banner += "+------------------------------------------------------------------------+"
        print(banner)
    except Exception as e:
        logger.debug("Could not print terminal banner: %s", e)


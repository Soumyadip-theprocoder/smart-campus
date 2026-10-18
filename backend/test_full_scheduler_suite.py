"""
Master Automated Verification Suite for Smart Campus Timetable Scheduler.
Covers all options, constraints, scopes, and REST API operations.

Suites:
1. Generator Scopes & Filters (Department, Block, All-Campus, Odd/Even Term)
2. Advanced Constraints (Consecutive Labs, Avoid Back-to-Back, Cohort Contiguity,
   Custom Breaks, Office Hours, Exam Mode, Merged Courses, Spillover, Locked Entries,
   Excluded Slots, Preferred Rooms, Max Classes/Day, Balance Faculty Workload)
3. Interactive REST APIs (Lock/Unlock, Smart Swaps, Absence Reporting,
   Version Management, Workload Metrics)
"""

import os
import sys
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIClient
from apps.accounts.models import User, Student
from apps.scheduler.models import (
    Department, Room, Subject, TimeSlot, TimetableEntry,
    TimetableVersion, Resource, Faculty, InstitutionSettings,
    AbsenceReport, TimetableSwapRequest, StudentElectiveEnrollment
)
from apps.scheduler.tasks import generate_timetable_task
from apps.scheduler.ortools_adapter import ORToolsSolverAdapter
from apps.scheduler.solver_interface import SolverInput


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def check(self, test_name, condition, details=""):
        status = "PASS" if condition else "FAIL"
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        msg = f"[{status}] {test_name}: {details}"
        print(msg)
        self.results.append((test_name, condition, details))
        if not condition:
            print(f"   >>> FAILURE IN: {test_name} - {details}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"SCHEDULER TEST SUITE SUMMARY: {self.passed}/{total} PASSED ({self.failed} FAILED)")
        print("=" * 70)
        return self.failed == 0


def run_full_suite():
    t = TestRunner()
    print("=" * 70)
    print("STARTING FULL TIMETABLE SCHEDULER THOROUGH TEST SUITE")
    print("=" * 70)

    # Reusable objects
    d1 = Department.objects.first()
    all_rooms = list(Room.objects.all().values("id", "room_number", "capacity", "room_type", "building"))
    for r in all_rooms:
        r["block_name"] = r["building"] if r.get("building") and r["building"].startswith("Block") else ""
    lab_rooms = [r for r in all_rooms if r.get("room_type") == "lab"]
    lec_rooms = [r for r in all_rooms if r.get("room_type") == "lecture"]
    test_rooms = lab_rooms[:4] + lec_rooms[:4]

    day_priority = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
    all_ts = sorted(
        list(TimeSlot.objects.all().values("id", "day", "start_time", "end_time")),
        key=lambda ts: (str(ts["start_time"]), day_priority.get(ts["day"], 99))
    )
    teaching_ts = [ts for ts in all_ts if str(ts["start_time"]) not in ["11:00:00", "15:00:00"]][:30]

    # =========================================================================
    # SUITE 1: SCOPE TYPES & TERM FILTERS
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 1: GENERATOR SCOPES & TERM FILTERS")
    print("-" * 50)

    # 1.1 Scope = Department
    cfg_dept = {
        "scope_type": "department",
        "department_id": d1.id,
        "semester": 1,
        "term": "odd",
        "draft_name": "Suite_Test_Dept_Scope",
    }
    res_dept = generate_timetable_task(cfg_dept)
    t.check("1.1 Scope Department Success", res_dept.get("success"), f"Count: {res_dept.get('count')}")
    if res_dept.get("success"):
        v_dept = TimetableVersion.objects.get(id=res_dept["version_id"])
        e_dept = TimetableEntry.objects.filter(version=v_dept)
        all_sem1 = all(e.subject.semester == 1 for e in e_dept if e.subject)
        t.check("1.1 Scope Department Semester Filter", all_sem1, f"All entries are semester 1 ({e_dept.count()} entries)")

    # 1.2 Scope = Academic Block
    block_a_subjs = list(Subject.objects.filter(departments__id=318, semester=1).values_list("id", flat=True))
    cfg_block = {
        "scope_type": "block",
        "block_name": "Block A",
        "subject_ids": block_a_subjs,
        "semester": 1,
        "term": "odd",
        "allow_spillover": False,
        "draft_name": "Suite_Test_Block_Scope",
    }
    res_block = generate_timetable_task(cfg_block)
    t.check("1.2 Scope Block Success", res_block.get("success"), f"Count: {res_block.get('count')}")
    if res_block.get("success"):
        v_block = TimetableVersion.objects.get(id=res_block["version_id"])
        e_block = TimetableEntry.objects.filter(version=v_block)
        bldgs = set(e.room.building for e in e_block if e.room and e.room.building)
        all_block_a = all("Block A" in b or "Central" in b for b in bldgs)
        t.check("1.2 Scope Block Room Affinity", all_block_a and len(bldgs) > 0, f"Rooms used: {bldgs}")

    # 1.3 Term Filter: Odd vs Even
    odd_subjs = Subject.objects.filter(departments=d1, semester__in=[1, 3, 5, 7, 9])
    even_subjs = Subject.objects.filter(departments=d1, semester__in=[2, 4, 6, 8, 10])
    t.check("1.3 Term Odd/Even Data Available", odd_subjs.exists() and even_subjs.exists(),
            f"Odd count: {odd_subjs.count()}, Even count: {even_subjs.count()}")

    # =========================================================================
    # SUITE 2: ADVANCED GENERATOR CONSTRAINTS
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 2: ADVANCED GENERATOR CONSTRAINTS")
    print("-" * 50)

    # 2.1 Consecutive Labs + Avoid Back-to-Back (Mutual Exclusion Verification)
    subjs_labs = [
        {
            "id": 9501,
            "code": "SUITE-LAB-1",
            "name": "Suite Practical Lab",
            "faculty_id": 1,
            "required_capacity": 20,
            "sessions_per_week": 2,
            "is_lab": True,
            "subject_type": "lab",
        },
        {
            "id": 9502,
            "code": "SUITE-LEC-1",
            "name": "Suite Lecture Theory",
            "faculty_id": 1,
            "required_capacity": 20,
            "sessions_per_week": 2,
            "is_lab": False,
            "subject_type": "lecture",
        },
    ]
    inp_labs = SolverInput(
        subjects=subjs_labs,
        rooms=test_rooms,
        time_slots=teaching_ts[:20],
        consecutive_labs=True,
        avoid_back_to_back=True,
        max_classes_per_day=2,
    )
    res_labs = ORToolsSolverAdapter(inp_labs).solve()
    t.check("2.1 Consecutive Labs + Avoid Back-to-Back Solved", res_labs.success, f"Error: {res_labs.error}")
    if res_labs.success:
        l_entries = [e for e in res_labs.timetable if e["subject_id"] == 9501]
        is_paired = (
            len(l_entries) == 2 and
            l_entries[0]["day"] == l_entries[1]["day"] and
            l_entries[0]["room_id"] == l_entries[1]["room_id"]
        )
        t.check("2.1 Lab Block Uninterrupted Pair", is_paired,
                f"Day: {l_entries[0]['day']}, Room: {l_entries[0]['room_number']}")

    # 2.2 Custom Breaks Respected
    cfg_breaks = {
        "scope_type": "department",
        "department_id": d1.id,
        "semester": 1,
        "term": "odd",
        "custom_breaks": [{"start_time": "12:00", "end_time": "13:00"}],
        "draft_name": "Suite_Test_Break_Filter",
    }
    res_breaks = generate_timetable_task(cfg_breaks)
    t.check("2.2 Custom Breaks Generation", res_breaks.get("success"))
    if res_breaks.get("success"):
        v_brk = TimetableVersion.objects.get(id=res_breaks["version_id"])
        brk_clashes = TimetableEntry.objects.filter(
            version=v_brk,
            time_slot__start_time__lt="13:00",
            time_slot__end_time__gt="12:00"
        ).count()
        t.check("2.2 Zero Classes During Break", brk_clashes == 0, f"Clashes during 12-13: {brk_clashes}")

    # 2.3 Auto-Schedule Office Hours
    cfg_oh = {
        "scope_type": "department",
        "department_id": d1.id,
        "semester": 1,
        "term": "odd",
        "auto_schedule_office_hours": True,
        "custom_breaks": [{"start_time": "12:00", "end_time": "13:00"}],
        "draft_name": "Suite_Test_Office_Hours",
    }
    res_oh = generate_timetable_task(cfg_oh)
    t.check("2.3 Office Hours Generation", res_oh.get("success"))
    if res_oh.get("success"):
        v_oh = TimetableVersion.objects.get(id=res_oh["version_id"])
        oh_entries = TimetableEntry.objects.filter(version=v_oh, event_type="office_hours")
        t.check("2.3 Office Hours Created", oh_entries.exists(), f"Created {oh_entries.count()} office hour slots")
        oh_in_lab = oh_entries.filter(room__room_type="lab").count()
        t.check("2.3 Office Hours Not in Labs", oh_in_lab == 0, f"Office hours in labs: {oh_in_lab}")

    # 2.4 Exam Mode
    cfg_exam = {
        "scope_type": "department",
        "department_id": d1.id,
        "semester": 1,
        "term": "odd",
        "exam_mode": True,
        "draft_name": "Suite_Test_Exam_Mode",
    }
    res_exam = generate_timetable_task(cfg_exam)
    t.check("2.4 Exam Mode Generation", res_exam.get("success"))
    if res_exam.get("success"):
        v_exam = TimetableVersion.objects.get(id=res_exam["version_id"])
        ex_entries = TimetableEntry.objects.filter(version=v_exam)
        all_exams = all(e.event_type == "exam" for e in ex_entries)
        t.check("2.4 Exam Mode Event Type Integrity", all_exams and ex_entries.exists(),
                f"All {ex_entries.count()} entries marked as exam")

    # 2.5 Common Course Merging
    subjs_merge = [
        {"id": 9601, "code": "MATH-CS", "name": "Discrete Math", "faculty_id": 5, "required_capacity": 30, "sessions_per_week": 1, "merge_group_id": "MG-DISCRETE"},
        {"id": 9602, "code": "MATH-IT", "name": "Discrete Math", "faculty_id": 5, "required_capacity": 30, "sessions_per_week": 1, "merge_group_id": "MG-DISCRETE"},
    ]
    inp_merge = SolverInput(
        subjects=subjs_merge,
        rooms=test_rooms,
        time_slots=teaching_ts[:10],
        merge_common_courses=True,
    )
    res_merge = ORToolsSolverAdapter(inp_merge).solve()
    t.check("2.5 Common Course Merging Solved", res_merge.success)
    if res_merge.success:
        t1 = res_merge.timetable[0]
        t2 = res_merge.timetable[1]
        co_scheduled = (t1["time_slot_id"] == t2["time_slot_id"] and t1["room_id"] == t2["room_id"])
        t.check("2.5 Common Courses Co-scheduled (Same Slot & Room)", co_scheduled,
                f"Slot: {t1['time_slot_id']}, Room: {t1['room_number']}")

    # 2.6 Allow Spillover False vs True
    spill_subjs = [
        {"id": 9701, "code": "AFFIN-A", "name": "Block A Only", "faculty_id": 8, "required_capacity": 20, "sessions_per_week": 1, "block_name": "Block A"}
    ]
    spill_rooms = [
        {"id": 881, "room_number": "A-TEST", "capacity": 30, "room_type": "lecture", "building": "Block A", "block_name": "Block A"},
        {"id": 882, "room_number": "B-TEST", "capacity": 30, "room_type": "lecture", "building": "Block B", "block_name": "Block B"},
    ]
    inp_spill = SolverInput(
        subjects=spill_subjs,
        rooms=spill_rooms,
        time_slots=teaching_ts[:5],
        allow_spillover=False,
    )
    res_spill = ORToolsSolverAdapter(inp_spill).solve()
    t.check("2.6 Allow Spillover=False Places in Primary Block",
            res_spill.success and res_spill.timetable[0]["room_id"] == 881,
            f"Assigned room={res_spill.timetable[0]['room_id'] if res_spill.success else 'None'}")

    # 2.7 Locked Entries Persistence
    first_entry = TimetableEntry.objects.filter(version=v_dept).first()
    if first_entry:
        pinned_sid = first_entry.subject_id
        pinned_rid = first_entry.room_id
        pinned_tsid = first_entry.time_slot_id
        cfg_lock = {
            "scope_type": "department",
            "department_id": d1.id,
            "semester": 1,
            "term": "odd",
            "locked_entries": [{"subject_id": pinned_sid, "room_id": pinned_rid, "time_slot_id": pinned_tsid}],
            "draft_name": "Suite_Test_Locked_Entry",
        }
        res_lock = generate_timetable_task(cfg_lock)
        t.check("2.7 Locked Entries Generation", res_lock.get("success"))
        if res_lock.get("success"):
            v_lock = TimetableVersion.objects.get(id=res_lock["version_id"])
            persisted = TimetableEntry.objects.filter(
                version=v_lock,
                subject_id=pinned_sid,
                room_id=pinned_rid,
                time_slot_id=pinned_tsid,
            ).exists()
            t.check("2.7 Locked Entry Preserved Exactly", persisted,
                    f"Subject {pinned_sid} locked to Room {pinned_rid} at Slot {pinned_tsid}")

    # 2.8 Excluded Slots Constraint
    ex_ts = teaching_ts[0]["id"]
    inp_ex = SolverInput(
        subjects=[{"id": 9801, "code": "EXCL-TEST", "name": "Excl Slot Test", "faculty_id": 9, "required_capacity": 20, "sessions_per_week": 1}],
        rooms=test_rooms[:2],
        time_slots=teaching_ts[:5],
        excluded_slots={9801: [ex_ts]},
    )
    res_ex = ORToolsSolverAdapter(inp_ex).solve()
    t.check("2.8 Excluded Slots Constraint Respected",
            res_ex.success and res_ex.timetable[0]["time_slot_id"] != ex_ts,
            f"Scheduled slot: {res_ex.timetable[0]['time_slot_id'] if res_ex.success else 'None'} vs excluded {ex_ts}")

    # 2.9 Preferred Room Types
    inp_pref = SolverInput(
        subjects=[{"id": 9901, "code": "PREF-TEST", "name": "Pref Type Test", "faculty_id": 9, "required_capacity": 20, "sessions_per_week": 1}],
        rooms=test_rooms,
        time_slots=teaching_ts[:5],
        preferred_room_types={9901: "lab"},
    )
    res_pref = ORToolsSolverAdapter(inp_pref).solve()
    pref_rid = res_pref.timetable[0]["room_id"] if res_pref.success else None
    assigned_r = next((r for r in test_rooms if r["id"] == pref_rid), {})
    t.check("2.9 Preferred Room Types Respected",
            res_pref.success and assigned_r.get("room_type") == "lab",
            f"Assigned room: {assigned_r.get('room_number')} ({assigned_r.get('room_type')})")

    # 2.10 Max Classes Per Day (Limit = 1)
    inp_max1 = SolverInput(
        subjects=[{"id": 9950, "code": "MAX1-TEST", "name": "Max 1 Per Day", "faculty_id": 11, "required_capacity": 20, "sessions_per_week": 3}],
        rooms=test_rooms[:2],
        time_slots=teaching_ts[:15],
        max_classes_per_day=1,
    )
    res_max1 = ORToolsSolverAdapter(inp_max1).solve()
    if res_max1.success:
        days_used = [e["day"] for e in res_max1.timetable]
        t.check("2.10 Max Classes Per Day = 1 Respected", len(set(days_used)) == 3, f"Scheduled across distinct days: {days_used}")
    else:
        t.check("2.10 Max Classes Per Day = 1 Respected", False, res_max1.error)

    # 2.11 Balance Faculty Workload
    inp_bal = SolverInput(
        subjects=[
            {"id": 9961, "code": "BAL-1", "name": "Bal 1", "faculty_id": 20, "required_capacity": 20, "sessions_per_week": 2},
            {"id": 9962, "code": "BAL-2", "name": "Bal 2", "faculty_id": 20, "required_capacity": 20, "sessions_per_week": 2},
        ],
        rooms=test_rooms[:2],
        time_slots=teaching_ts[:15],
        balance_faculty_workload=True,
    )
    res_bal = ORToolsSolverAdapter(inp_bal).solve()
    t.check("2.11 Balance Faculty Workload Enabled", res_bal.success, f"Assigned {len(res_bal.timetable)} sessions")

    # 2.12 Cohort Schedule Contiguity
    subjs_contig = [
        {"id": 9971, "code": "CONTIG-1", "name": "Contig 1", "faculty_id": 21, "required_capacity": 20, "sessions_per_week": 2, "cohort_key": (999, 1)},
        {"id": 9972, "code": "CONTIG-2", "name": "Contig 2", "faculty_id": 22, "required_capacity": 20, "sessions_per_week": 2, "cohort_key": (999, 1)},
    ]
    inp_contig = SolverInput(
        subjects=subjs_contig,
        rooms=test_rooms[:3],
        time_slots=teaching_ts[:12],
    )
    res_contig = ORToolsSolverAdapter(inp_contig).solve()
    t.check("2.12 Cohort Schedule Contiguity Optimization", res_contig.success, f"Assigned {len(res_contig.timetable)} sessions")

    # =========================================================================
    # SUITE 3: INTERACTIVE REST APIS
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 3: INTERACTIVE REST APIS & OPERATIONS")
    print("-" * 50)

    client = APIClient()
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        client.force_authenticate(user=admin_user)

    # 3.1 Lock / Unlock Entry API
    test_entry = TimetableEntry.objects.filter(version=v_dept).first()
    if test_entry:
        orig_locked = test_entry.is_locked
        patch_res = client.patch(f"/api/scheduler/timetable/{test_entry.id}/", {"is_locked": not orig_locked})
        t.check("3.1 Lock/Unlock Entry API", patch_res.status_code == 200 and patch_res.data.get("is_locked") == (not orig_locked),
                f"Status: {patch_res.status_code}, is_locked toggled to: {patch_res.data.get('is_locked')}")
        # Restore original
        client.patch(f"/api/scheduler/timetable/{test_entry.id}/", {"is_locked": orig_locked})

    # 3.2 Smart Swap Suggestions API (GET /api/scheduler/timetable/<id>/smart-swaps/)
    if test_entry:
        swap_sug_res = client.get(f"/api/scheduler/timetable/{test_entry.id}/smart-swaps/")
        t.check("3.2 Smart Swap Suggestions API", swap_sug_res.status_code == 200,
                f"Status: {swap_sug_res.status_code}, total suggestions: {swap_sug_res.data.get('total_suggestions') if swap_sug_res.status_code == 200 else 0}")

    # 3.3 Create Swap Request API (POST /api/scheduler/swaps/)
    faculty_obj = Faculty.objects.select_related("user").first()
    fac_client = APIClient()
    if faculty_obj and faculty_obj.user:
        fac_client.force_authenticate(user=faculty_obj.user)
    else:
        fac_client = client

    if test_entry:
        swap_payload = {
            "target_entry": test_entry.id,
            "requested_time_slot": teaching_ts[2]["id"],
            "reason": "Academic conference duty",
        }
        swap_req_res = fac_client.post("/api/scheduler/swaps/", swap_payload)
        t.check("3.3 Create Swap Request API", swap_req_res.status_code in [200, 201],
                f"Status: {swap_req_res.status_code}")

    # 3.4 Absence Reporting API (POST /api/scheduler/absences/)
    if test_entry:
        abs_payload = {
            "date": "2026-10-19",
            "reason": "Medical emergency",
            "timetable_entry": test_entry.id,
        }
        abs_res = fac_client.post("/api/scheduler/absences/", abs_payload)
        t.check("3.4 Absence Reporting API", abs_res.status_code in [200, 201],
                f"Status: {abs_res.status_code}")

    # 3.5 Timetable Versions API
    ver_list_res = client.get("/api/scheduler/versions/")
    t.check("3.5 List Timetable Versions API", ver_list_res.status_code == 200 and len(ver_list_res.data) > 0,
            f"Versions found: {len(ver_list_res.data)}")

    # 3.6 Workload & Accreditation Metrics API (/api/scheduler/analytics/accreditation/)
    workload_res = client.get("/api/scheduler/analytics/accreditation/")
    has_workload = workload_res.status_code == 200 and "faculty_workload" in workload_res.data
    t.check("3.6 Faculty Workload & Accreditation Metrics API", has_workload,
            f"Status: {workload_res.status_code}, faculty workloads calculated: {len(workload_res.data.get('faculty_workload', [])) if has_workload else 0}")

    # 3.7 Bulk Delete Versions API
    drafts_to_del = list(TimetableVersion.objects.filter(is_published=False, name__startswith="Suite_Test_").values_list("id", flat=True))
    if drafts_to_del:
        bulk_del_res = client.post("/api/scheduler/versions/bulk-delete/", {"ids": drafts_to_del})
        t.check("3.7 Bulk Delete Draft Versions API", bulk_del_res.status_code == 200,
                f"Deleted {len(drafts_to_del)} test draft versions")

    # 3.8 Task Cancel API (POST /api/scheduler/task-cancel/<id>/)
    from apps.scheduler.models import SchedulerTaskProgress
    dummy_task = SchedulerTaskProgress.objects.create(
        task_id="suite-test-cancel-999",
        status="running",
        scope_label="Test Scope",
        percent=45.0,
        sessions_scheduled=120,
    )
    cancel_res = client.post(f"/api/scheduler/task-cancel/{dummy_task.task_id}/")
    dummy_task.refresh_from_db()
    cancel_ok = cancel_res.status_code == 200 and dummy_task.status == "cancelled"
    t.check("3.8 Task Cancel API", cancel_ok,
            f"Status: {cancel_res.status_code}, DB task status: {dummy_task.status}")
    dummy_task.delete()

    # =========================================================================
    # SUITE 4: Middle Layer Debug Interceptor & Diagnostics
    # =========================================================================
    print("\n--- SUITE 4: Middle Layer Debug Interceptor & Diagnostics ---")
    from apps.scheduler.debug_layer import analyze_generator_payload
    from apps.scheduler.models import SchedulerInputLog

    target_dept = Department.objects.first()

    # 4.1 Schema validation & telemetry summary analysis
    sample_payload = {
        "scope_type": "department",
        "department_id": target_dept.id if target_dept else 1,
        "draft_name": "Debug Suite Test Run",
        "semester": 1,
        "term": "odd",
        "subject_ids": [101, 102],
        "room_ids": [201],
        "timeslot_ids": [301, 302],
        "consecutive_labs": True,
        "merge_common_courses": True,
        "avoid_back_to_back": True,
    }
    summary = analyze_generator_payload(sample_payload)
    t.check(
        "4.1 Payload Pre-flight Analysis",
        summary["counts"]["subjects"] == 2 and summary["constraints"]["consecutive_labs"] is True and summary["is_healthy"] is True,
        f"Healthy: {summary['is_healthy']}, Subjects: {summary['counts']['subjects']}, Constraints checked: {len(summary['constraints'])}"
    )

    # 4.2 Diagnostic Warning Detection on Incomplete Payload
    bad_payload = {"scope_type": "department"}  # missing department_id and timeslot_ids
    bad_summary = analyze_generator_payload(bad_payload)
    has_warnings = len(bad_summary["warnings"]) >= 2 and bad_summary["is_healthy"] is False
    t.check(
        "4.2 Diagnostic Warning & Health Check",
        has_warnings,
        f"Identified {len(bad_summary['warnings'])} warnings: {bad_summary['warnings']}"
    )

    # 4.3 End-to-end Interception via Generate Timetable API
    gen_req_payload = {
        "scope_type": "department",
        "department_id": target_dept.id if target_dept else 1,
        "draft_name": "Suite Interceptor Test Draft",
        "semester": 1,
        "term": "odd",
        "consecutive_labs": True,
        "merge_common_courses": True,
    }
    post_res = client.post("/api/scheduler/generate/", gen_req_payload)
    t.check(
        "4.3 Middle Layer Interception on /api/scheduler/generate/",
        post_res.status_code in [200, 202] and "task_id" in post_res.data,
        f"Status: {post_res.status_code}, Task ID: {post_res.data.get('task_id')}"
    )

    intercepted_task_id = post_res.data.get("task_id")
    if intercepted_task_id:
        # Check DB log
        log_entry = SchedulerInputLog.objects.filter(task_id=intercepted_task_id).first()
        t.check(
            "4.4 SchedulerInputLog DB Record Persisted",
            log_entry is not None and log_entry.draft_name == "Suite Interceptor Test Draft",
            f"Found log with ID {getattr(log_entry, 'id', None)}, scope: {getattr(log_entry, 'scope_label', None)}"
        )

        # Check SchedulerTaskProgress.input_payload
        progress_entry = SchedulerTaskProgress.objects.filter(task_id=intercepted_task_id).first()
        t.check(
            "4.5 SchedulerTaskProgress Preserved input_payload",
            progress_entry is not None and progress_entry.input_payload is not None,
            f"Preserved payload keys: {list(progress_entry.input_payload.keys()) if progress_entry and progress_entry.input_payload else 'None'}"
        )

        # 4.6 Query Debug API (GET /api/scheduler/debug/inputs/)
        debug_api_res = client.get("/api/scheduler/debug/inputs/")
        t.check(
            "4.6 Debug Inputs API List Endpoint (GET /api/scheduler/debug/inputs/)",
            debug_api_res.status_code == 200 and debug_api_res.data.get("success") is True and debug_api_res.data.get("total_captured", 0) > 0,
            f"Status: {debug_api_res.status_code}, total captured: {debug_api_res.data.get('total_captured')}"
        )

        # 4.7 Query Debug API for specific Task (GET /api/scheduler/debug/inputs/<task_id>/)
        task_debug_res = client.get(f"/api/scheduler/debug/inputs/{intercepted_task_id}/")
        t.check(
            "4.7 Task-Specific Debug Inputs API (GET /api/scheduler/debug/inputs/<task_id>/)",
            task_debug_res.status_code == 200 and task_debug_res.data.get("task_id") == intercepted_task_id,
            f"Status: {task_debug_res.status_code}, matched task: {task_debug_res.data.get('task_id')}"
        )

    # =========================================================================
    # SUITE 5: ROLE-BASED TIMETABLE ACCESS CONTROL (STUDENT vs FACULTY vs ADMIN)
    # =========================================================================
    print("\n" + "-" * 50)
    print("SUITE 5: ROLE-BASED TIMETABLE ACCESS CONTROL")
    print("-" * 50)

    # 5.0 Setup Role Test Fixtures
    r_role1 = Room.objects.first() or Room.objects.create(room_number="R-ROLE-1", capacity=40)
    r_role2 = Room.objects.filter(capacity__gte=30).exclude(id=r_role1.id).first() or Room.objects.create(room_number="R-ROLE-2", capacity=40)
    r_role3 = Room.objects.exclude(id__in=[r_role1.id, r_role2.id]).first() or Room.objects.create(room_number="R-ROLE-3", capacity=40)

    ts_role1 = TimeSlot.objects.first()
    ts_role2 = TimeSlot.objects.exclude(id=ts_role1.id).first()
    ts_role3 = TimeSlot.objects.exclude(id__in=[ts_role1.id, ts_role2.id]).first()
    ts_role4 = TimeSlot.objects.exclude(id__in=[ts_role1.id, ts_role2.id, ts_role3.id]).first()

    d_cs = Department.objects.filter(name__icontains="Computer").first() or Department.objects.create(name="Suite Computer Science", dept_id="S-CS")
    d_ee = Department.objects.filter(name__icontains="Electrical").first() or Department.objects.create(name="Suite Electrical Eng", dept_id="S-EE")

    # Faculty 1 (Alice - CS)
    u_alice, _ = User.objects.get_or_create(email="alice.faculty@smartcampus.edu", defaults={"username": "alice.faculty", "first_name": "Alice", "last_name": "Smith", "role": "faculty"})
    f_alice, _ = Faculty.objects.get_or_create(user=u_alice, defaults={"employee_id": "FAC-ALICE-1", "department": d_cs, "designation": "Associate Professor"})

    # Faculty 2 (Bob - EE)
    u_bob, _ = User.objects.get_or_create(email="bob.faculty@smartcampus.edu", defaults={"username": "bob.faculty", "first_name": "Bob", "last_name": "Jones", "role": "faculty"})
    f_bob, _ = Faculty.objects.get_or_create(user=u_bob, defaults={"employee_id": "FAC-BOB-2", "department": d_ee, "designation": "Assistant Professor"})

    # Student 1 (Sam - CS, Sem 1, TA)
    u_sam, _ = User.objects.get_or_create(email="sam.student@smartcampus.edu", defaults={"username": "sam.student", "first_name": "Sam", "last_name": "Wilson", "role": "student"})
    s_sam, _ = Student.objects.get_or_create(user=u_sam, defaults={"enrollment_number": "STU-SAM-1", "department": d_cs, "semester": 1, "is_ta": True})
    s_sam.is_ta = True
    s_sam.department = d_cs
    s_sam.semester = 1
    s_sam.save()

    # Subjects
    subj_core_cs, _ = Subject.objects.get_or_create(code="S5-CS101", defaults={"name": "Intro to Programming", "faculty": f_alice, "semester": 1, "is_elective": False, "required_capacity": 30})
    subj_core_cs.departments.set([d_cs])

    subj_elec_cs, _ = Subject.objects.get_or_create(code="S5-CS901", defaults={"name": "Cloud Computing", "faculty": f_alice, "semester": 1, "is_elective": True, "required_capacity": 30, "elective_group": "BASKET-CLOUD"})
    subj_elec_cs.departments.set([d_cs])

    subj_core_ee, _ = Subject.objects.get_or_create(code="S5-EE101", defaults={"name": "Circuit Theory", "faculty": f_bob, "semester": 1, "is_elective": False, "required_capacity": 30})
    subj_core_ee.departments.set([d_ee])

    # Student Elective Enrollment
    StudentElectiveEnrollment.objects.get_or_create(student=s_sam, elective_group="BASKET-CLOUD", defaults={"subject": subj_elec_cs})

    # Versions: 1 Published Live, 1 Sandbox Draft
    v_live, _ = TimetableVersion.objects.get_or_create(name="Suite 5 Live Version", defaults={"is_published": True})
    TimetableVersion.objects.all().update(is_published=False)
    v_live.is_published = True
    v_live.save()

    v_draft_test, _ = TimetableVersion.objects.get_or_create(name="Suite 5 Secret Draft", defaults={"is_published": False})
    v_draft_test.is_published = False
    v_draft_test.save()

    # Timetable Entries on Live Version
    entry_a, _ = TimetableEntry.objects.get_or_create(version=v_live, subject=subj_core_cs, defaults={"room": r_role1, "time_slot": ts_role1, "faculty": f_alice})
    entry_b, _ = TimetableEntry.objects.get_or_create(version=v_live, subject=subj_elec_cs, defaults={"room": r_role2, "time_slot": ts_role2, "faculty": f_alice})
    entry_c, _ = TimetableEntry.objects.get_or_create(version=v_live, subject=subj_core_ee, time_slot=ts_role3, defaults={"room": r_role3, "faculty": f_bob})
    entry_c.teaching_assistants.set([s_sam])

    entry_d, _ = TimetableEntry.objects.get_or_create(version=v_live, subject=subj_core_ee, time_slot=ts_role4, defaults={"room": r_role1, "faculty": f_bob})

    # Substitute Duty: Alice covers entry_d for Bob
    AbsenceReport.objects.filter(timetable_entry=entry_d).delete()
    AbsenceReport.objects.create(timetable_entry=entry_d, faculty=f_bob, substitute=f_alice, status="approved", date="2026-10-20", reason="Conference coverage")

    # Entry on Draft Version
    entry_draft, _ = TimetableEntry.objects.get_or_create(version=v_draft_test, subject=subj_core_cs, defaults={"room": r_role1, "time_slot": ts_role4, "faculty": f_alice})

    # --- 5.1 Student Timetable Visibility & Role Scoping ---
    client_student = APIClient()
    client_student.force_authenticate(user=u_sam)
    res_student_tt = client_student.get("/api/scheduler/timetable/")
    student_entries = res_student_tt.data if isinstance(res_student_tt.data, list) else res_student_tt.data.get("results", [])
    student_entry_ids = {e["id"] for e in student_entries}

    has_core = entry_a.id in student_entry_ids
    has_elective = entry_b.id in student_entry_ids
    has_ta = entry_c.id in student_entry_ids
    has_unenrolled = entry_d.id in student_entry_ids
    has_draft = entry_draft.id in student_entry_ids

    t.check(
        "5.1 Student Timetable Scoping (Core + Elective + TA Duty)",
        res_student_tt.status_code == 200 and has_core and has_elective and has_ta and not has_unenrolled and not has_draft,
        f"Found {len(student_entry_ids)} entries. Core: {has_core}, Elective: {has_elective}, TA: {has_ta}, Excluded Other: {not has_unenrolled}, Excluded Draft: {not has_draft}"
    )

    # --- 5.2 Student Protection & Security (Draft access denied, Generator forbidden) ---
    res_student_draft = client_student.get(f"/api/scheduler/timetable/?version={v_draft_test.id}")
    student_draft_entries = res_student_draft.data if isinstance(res_student_draft.data, list) else res_student_draft.data.get("results", [])
    res_student_gen = client_student.post("/api/scheduler/generate/", {"scope_type": "all"})
    res_student_versions = client_student.get("/api/scheduler/versions/")
    student_vers = res_student_versions.data if isinstance(res_student_versions.data, list) else res_student_versions.data.get("results", [])
    only_published_seen = all(v.get("is_published") for v in student_vers)

    t.check(
        "5.2 Student Security: Draft Hidden, Versions Filtered, Generator 403 Forbidden",
        len(student_draft_entries) == 0 and res_student_gen.status_code == 403 and only_published_seen,
        f"Draft entries returned: {len(student_draft_entries)}, Gen status: {res_student_gen.status_code}, Only published in list: {only_published_seen}"
    )

    # --- 5.3 Faculty Timetable Visibility & Role Scoping ---
    client_faculty = APIClient()
    client_faculty.force_authenticate(user=u_alice)
    res_faculty_tt = client_faculty.get("/api/scheduler/timetable/")
    faculty_entries = res_faculty_tt.data if isinstance(res_faculty_tt.data, list) else res_faculty_tt.data.get("results", [])
    faculty_entry_ids = {e["id"] for e in faculty_entries}

    fac_has_teaching = entry_a.id in faculty_entry_ids and entry_b.id in faculty_entry_ids
    fac_has_substitute = entry_d.id in faculty_entry_ids
    fac_has_other = entry_c.id in faculty_entry_ids
    fac_has_draft = entry_draft.id in faculty_entry_ids

    t.check(
        "5.3 Faculty Timetable Scoping (Assigned Teaching + Approved Substitute)",
        res_faculty_tt.status_code == 200 and fac_has_teaching and fac_has_substitute and not fac_has_other and not fac_has_draft,
        f"Found {len(faculty_entry_ids)} entries. Teaching: {fac_has_teaching}, Substitute: {fac_has_substitute}, Excluded Other: {not fac_has_other}, Excluded Draft: {not fac_has_draft}"
    )

    # --- 5.4 Faculty Protection & Security ---
    res_fac_draft = client_faculty.get(f"/api/scheduler/timetable/?version={v_draft_test.id}")
    fac_draft_entries = res_fac_draft.data if isinstance(res_fac_draft.data, list) else res_fac_draft.data.get("results", [])
    res_fac_gen = client_faculty.post("/api/scheduler/generate/", {"scope_type": "all"})

    t.check(
        "5.4 Faculty Security: Draft Hidden & Generator 403 Forbidden",
        len(fac_draft_entries) == 0 and res_fac_gen.status_code == 403,
        f"Draft entries: {len(fac_draft_entries)}, Gen status: {res_fac_gen.status_code}"
    )

    # --- 5.5 Admin Full Campus & Draft Timetable Inspection ---
    client_admin = APIClient()
    admin_u = User.objects.filter(is_superuser=True).first() or User.objects.create_superuser("admin.master", "admin.master@smartcampus.edu", "adminpass123")
    client_admin.force_authenticate(user=admin_u)

    res_admin_live = client_admin.get("/api/scheduler/timetable/")
    admin_live_entries = res_admin_live.data if isinstance(res_admin_live.data, list) else res_admin_live.data.get("results", [])
    admin_live_ids = {e["id"] for e in admin_live_entries}

    res_admin_draft = client_admin.get(f"/api/scheduler/timetable/?version={v_draft_test.id}")
    admin_draft_entries = res_admin_draft.data if isinstance(res_admin_draft.data, list) else res_admin_draft.data.get("results", [])
    admin_draft_ids = {e["id"] for e in admin_draft_entries}

    admin_sees_all_live = {entry_a.id, entry_b.id, entry_c.id, entry_d.id}.issubset(admin_live_ids)
    admin_sees_draft = entry_draft.id in admin_draft_ids

    t.check(
        "5.5 Administrator Full Campus Timetable & Sandbox Draft Inspection",
        admin_sees_all_live and admin_sees_draft,
        f"Admin sees all live entries: {admin_sees_all_live}, Admin sees draft entry: {admin_sees_draft}"
    )

    return t.summary()


if __name__ == "__main__":
    success = run_full_suite()
    sys.exit(0 if success else 1)

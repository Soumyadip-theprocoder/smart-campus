"""
Tests for the OR-Tools CP-SAT Timetable Solver.
Verifies constraint satisfaction, edge cases, and solution quality
against the solver-agnostic interface.
"""

from django.test import TestCase

from apps.scheduler.ortools_adapter import ORToolsSolverAdapter
from apps.scheduler.solver_interface import SolverInput


class ORToolsSolverBasicTests(TestCase):
    """Basic tests for the ORToolsSolverAdapter."""

    def _make_subjects(self, data):
        """Helper to create subject dicts for the solver."""
        return [
            {
                "id": i + 1,
                "code": d["code"],
                "name": d.get("name", d["code"]),
                "faculty_id": d["faculty_id"],
                "required_capacity": d.get("capacity", 30),
                "sessions_per_week": d.get("sessions", 2),
                "elective_group_id": d.get("elective_group_id"),
                "resource_ids": d.get("resource_ids", []),
            }
            for i, d in enumerate(data)
        ]

    def _make_rooms(self, data):
        return [
            {
                "id": i + 1,
                "room_number": d["number"],
                "capacity": d["capacity"],
                "room_type": d.get("type", "lecture"),
                "building": d.get("building", "Main"),
            }
            for i, d in enumerate(data)
        ]

    def _make_slots(self, days, periods):
        slots = []
        slot_id = 1
        for day in days:
            for start_h, end_h in periods:
                slots.append(
                    {
                        "id": slot_id,
                        "day": day,
                        "start_time": f"{start_h:02d}:00",
                        "end_time": f"{end_h:02d}:00",
                    }
                )
                slot_id += 1
        return slots

    def _solve(self, subjects, rooms, slots, **kwargs):
        """Helper to create SolverInput, build adapter, and solve."""
        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            **kwargs,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        return adapter.solve()

    # ─── Basic scheduling ───────────────────────────────────────────

    def test_simple_schedule(self):
        """Two subjects, two rooms, enough slots — should find a solution."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 2},
                {"code": "CS2", "faculty_id": 2, "sessions": 2},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE", "WED"], [(9, 10), (10, 11)])

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success, f"Solver should find a solution: {result.error}")
        self.assertEqual(len(result.timetable), 4)  # 2 subjects * 2 sessions

    def test_no_faculty_conflict(self):
        """Same faculty should never be scheduled at the same time."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 3},
                {"code": "CS2", "faculty_id": 1, "sessions": 3},  # same faculty
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(
            ["MON", "TUE", "WED", "THU", "FRI"], [(9, 10), (10, 11)]
        )

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success)
        self.assertEqual(len(result.timetable), 6)
        # Check no faculty time conflicts
        time_slots_used = {}
        for entry in result.timetable:
            fac_id = entry["faculty_id"]
            ts_id = entry["time_slot_id"]
            key = (fac_id, ts_id)
            self.assertNotIn(key, time_slots_used,
                             f"Faculty {fac_id} double-booked at time slot {ts_id}")
            time_slots_used[key] = entry["subject_code"]

    def test_no_room_conflict(self):
        """Same room should never be booked twice at the same time."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 2},
                {"code": "CS2", "faculty_id": 2, "sessions": 2},
            ]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])  # only 1 room
        slots = self._make_slots(["MON", "TUE", "WED", "THU"], [(9, 10), (10, 11)])

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success)
        room_time_set = set()
        for entry in result.timetable:
            key = (entry["room_id"], entry["time_slot_id"])
            self.assertNotIn(key, room_time_set,
                             f"Room {entry['room_number']} double-booked at slot {entry['time_slot_id']}")
            room_time_set.add(key)

    def test_room_capacity_constraint(self):
        """Subject requiring 100 seats shouldn't be placed in a 40-seat room."""
        subjects = self._make_subjects(
            [{"code": "BIG", "faculty_id": 1, "capacity": 100, "sessions": 1}]
        )
        rooms = self._make_rooms([{"number": "Small", "capacity": 40}])
        slots = self._make_slots(["MON"], [(9, 10)])

        result = self._solve(subjects, rooms, slots)

        self.assertFalse(result.success, "Should fail — no room with enough capacity")

    # ─── Excluded slots ─────────────────────────────────────────────

    def test_excluded_slots(self):
        """Subject should not be placed in an excluded time slot."""
        subjects = self._make_subjects(
            [{"code": "CS1", "faculty_id": 1, "sessions": 1}]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(["MON", "TUE"], [(9, 10)])
        # Exclude slot 1 (MON 9-10)
        excluded_slots = {1: [1]}

        result = self._solve(subjects, rooms, slots, excluded_slots=excluded_slots)

        self.assertTrue(result.success)
        self.assertEqual(result.timetable[0]["day"], "TUE")

    # ─── Locked entries ─────────────────────────────────────────────

    def test_locked_entries(self):
        """Locked entries should be preserved in the solution."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 1},
                {"code": "CS2", "faculty_id": 2, "sessions": 1},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE"], [(9, 10), (10, 11)])
        locked = [{"subject_id": 1, "time_slot_id": 1, "room_id": 1}]

        result = self._solve(subjects, rooms, slots, locked_entries=locked)

        self.assertTrue(result.success)
        cs1_entry = next(e for e in result.timetable if e["subject_code"] == "CS1")
        self.assertEqual(cs1_entry["time_slot_id"], 1)
        self.assertEqual(cs1_entry["room_id"], 1)

    # ─── Max classes per day ────────────────────────────────────────

    def test_max_classes_per_day(self):
        """Subject with 3 sessions and max 1/day needs 3 distinct days."""
        subjects = self._make_subjects(
            [{"code": "CS1", "faculty_id": 1, "sessions": 3}]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(
            ["MON", "TUE", "WED"], [(9, 10), (10, 11), (11, 12)]
        )

        result = self._solve(subjects, rooms, slots, max_classes_per_day=1)

        self.assertTrue(result.success)
        days = [e["day"] for e in result.timetable]
        self.assertEqual(len(set(days)), 3, "Each session should be on a different day")

    # ─── Avoid back-to-back ─────────────────────────────────────────

    def test_avoid_back_to_back(self):
        """Same faculty should not have consecutive slots when avoid_back_to_back is True."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 1},
                {"code": "CS2", "faculty_id": 1, "sessions": 1},
            ]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(["MON"], [(9, 10), (10, 11), (14, 15)])

        result = self._solve(subjects, rooms, slots, avoid_back_to_back=True)

        self.assertTrue(result.success)
        entries = sorted(result.timetable, key=lambda e: e["start_time"])
        if len(entries) == 2 and entries[0]["day"] == entries[1]["day"]:
            # They should NOT be 9-10 and 10-11
            self.assertFalse(
                entries[0]["end_time"] == entries[1]["start_time"],
                "Should not be back-to-back"
            )

    # ─── Balance faculty workload ───────────────────────────────────

    def test_balance_faculty_workload(self):
        """Faculty should not have more than 3 classes on the same day."""
        subjects = self._make_subjects(
            [
                {"code": f"CS{i}", "faculty_id": 1, "sessions": 1}
                for i in range(5)
            ]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(
            ["MON", "TUE", "WED", "THU", "FRI"],
            [(9, 10), (10, 11), (11, 12), (13, 14), (14, 15)]
        )

        result = self._solve(subjects, rooms, slots, balance_faculty_workload=True)

        self.assertTrue(result.success)
        from collections import Counter
        day_counts = Counter(e["day"] for e in result.timetable)
        for day, count in day_counts.items():
            self.assertLessEqual(count, 3,
                                 f"Faculty has {count} classes on {day}, max is 3")

    # ─── Elective group conflict ────────────────────────────────────

    def test_elective_group_conflict(self):
        """Subjects in the same elective group should not overlap."""
        subjects = self._make_subjects(
            [
                {"code": "EL1", "faculty_id": 1, "sessions": 1, "elective_group_id": 10},
                {"code": "EL2", "faculty_id": 2, "sessions": 1, "elective_group_id": 10},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE"], [(9, 10)])

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success)
        ts_ids = [e["time_slot_id"] for e in result.timetable]
        self.assertNotEqual(ts_ids[0], ts_ids[1],
                            "Elective group subjects should not be in the same timeslot")

    # ─── Resource pool capacity ─────────────────────────────────────

    def test_resource_pool_capacity(self):
        """Two subjects using the same single-quantity resource can't overlap."""
        subjects = self._make_subjects(
            [
                {"code": "LAB1", "faculty_id": 1, "sessions": 1, "resource_ids": [1]},
                {"code": "LAB2", "faculty_id": 2, "sessions": 1, "resource_ids": [1]},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE"], [(9, 10)])
        resources = [{"id": 1, "name": "Projector", "quantity": 1}]

        result = self._solve(subjects, rooms, slots, resources=resources)

        self.assertTrue(result.success)
        ts_ids = [e["time_slot_id"] for e in result.timetable]
        self.assertNotEqual(ts_ids[0], ts_ids[1],
                            "Subjects sharing a single-quantity resource can't overlap")

    # ─── Building transit ───────────────────────────────────────────

    def test_building_transit(self):
        """Same faculty back-to-back in different buildings should be avoided."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 1},
                {"code": "CS2", "faculty_id": 1, "sessions": 1},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40, "building": "East"},
                {"number": "R2", "capacity": 40, "building": "West"},
            ]
        )
        # 3 slots on Monday: 9-10, 10-11, 14-15 (not consecutive)
        slots = self._make_slots(["MON"], [(9, 10), (10, 11), (14, 15)])

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success)
        entries = sorted(result.timetable, key=lambda e: e["start_time"])
        # If they are in consecutive slots, they must be in the same building
        for i in range(len(entries) - 1):
            if entries[i]["end_time"] == entries[i + 1]["start_time"]:
                bldg_a = next(r["building"] for r in rooms if r["id"] == entries[i]["room_id"])
                bldg_b = next(r["building"] for r in rooms if r["id"] == entries[i + 1]["room_id"])
                self.assertEqual(bldg_a, bldg_b,
                                 "Back-to-back entries for same faculty must share a building")

    # ─── Minimize changes (rescheduling) ────────────────────────────

    def test_minimize_changes(self):
        """Solver should prefer the previous assignment when rescheduling."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 2},
                {"code": "CS2", "faculty_id": 2, "sessions": 2},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE", "WED", "THU"], [(9, 10), (10, 11)])

        # First solve without previous assignment
        result1 = self._solve(subjects, rooms, slots)
        self.assertTrue(result1.success)

        # Build previous_assignment from first result
        prev = {}
        session_counters = {}
        for entry in result1.timetable:
            sid = entry["subject_id"]
            session_counters.setdefault(sid, 0)
            idx = session_counters[sid]
            prev[(sid, idx)] = (entry["time_slot_id"], entry["room_id"])
            session_counters[sid] += 1

        # Re-solve with previous_assignment hint
        solver_input = SolverInput(
            subjects=subjects, rooms=rooms, time_slots=slots
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result2 = adapter.solve(previous_assignment=prev)

        self.assertTrue(result2.success)
        # Most entries should match the original
        matches = 0
        for entry in result2.timetable:
            sid = entry["subject_id"]
            # Check if this entry matches any in the original
            for orig in result1.timetable:
                if (orig["subject_id"] == sid and
                        orig["time_slot_id"] == entry["time_slot_id"] and
                        orig["room_id"] == entry["room_id"]):
                    matches += 1
                    break
        self.assertGreaterEqual(matches, len(result1.timetable) - 1,
                                "Most entries should be preserved when rescheduling")

    # ─── Preferred room types (soft) ────────────────────────────────

    def test_preferred_room_types(self):
        """Subject should prefer the lab room when preferred_room_types is set."""
        subjects = self._make_subjects(
            [{"code": "LAB1", "faculty_id": 1, "sessions": 1}]
        )
        rooms = self._make_rooms(
            [
                {"number": "Lecture1", "capacity": 40, "type": "lecture"},
                {"number": "Lab1", "capacity": 40, "type": "lab"},
            ]
        )
        slots = self._make_slots(["MON"], [(9, 10)])
        pref = {1: "lab"}

        result = self._solve(subjects, rooms, slots, preferred_room_types=pref)

        self.assertTrue(result.success)
        self.assertEqual(result.timetable[0]["room_number"], "Lab1",
                         "Should prefer the lab room")

    # ─── Edge cases ─────────────────────────────────────────────────

    def test_impossible_schedule(self):
        """More sessions than available slots should fail gracefully."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 5},
            ]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(["MON"], [(9, 10)])  # only 1 slot

        result = self._solve(subjects, rooms, slots)

        self.assertFalse(result.success, "Should fail — not enough slots")

    def test_single_subject_single_session(self):
        """Simplest possible case."""
        subjects = self._make_subjects(
            [{"code": "CS1", "faculty_id": 1, "sessions": 1}]
        )
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(["MON"], [(9, 10)])

        result = self._solve(subjects, rooms, slots)

        self.assertTrue(result.success)
        self.assertEqual(len(result.timetable), 1)

    def test_empty_subjects(self):
        """No subjects should produce an empty timetable (not a crash)."""
        rooms = self._make_rooms([{"number": "R1", "capacity": 40}])
        slots = self._make_slots(["MON"], [(9, 10)])

        result = self._solve([], rooms, slots)

        self.assertTrue(result.success)
        self.assertEqual(len(result.timetable), 0)


class Phase17MultiDepartmentSchedulerTests(TestCase):
    """Phase 17 enterprise multi-department routine scheduler tests."""

    def _make_slots(self, days, periods):
        slots = []
        slot_id = 1
        for day in days:
            for start_h, end_h in periods:
                slots.append(
                    {
                        "id": slot_id,
                        "day": day,
                        "start_time": f"{start_h:02d}:00",
                        "end_time": f"{end_h:02d}:00",
                    }
                )
                slot_id += 1
        return slots

    def test_semester_cohort_non_overlap(self):
        """Subjects in the same semester cohort must never overlap at the same timeslot."""
        # Two subjects for cohort (Department 1, Semester 1)
        subjects = [
            {
                "id": 1,
                "code": "MATH101",
                "name": "Mathematics I",
                "faculty_id": 10,
                "required_capacity": 30,
                "sessions_per_week": 2,
                "cohort_key": (1, 1),
            },
            {
                "id": 2,
                "code": "PHYS101",
                "name": "Physics I",
                "faculty_id": 11,
                "required_capacity": 30,
                "sessions_per_week": 2,
                "cohort_key": (1, 1),
            },
        ]
        # Two rooms available — without cohort constraint, they could be co-scheduled
        rooms = [
            {"id": 1, "room_number": "R101", "capacity": 40, "room_type": "lecture"},
            {"id": 2, "room_number": "R102", "capacity": 40, "room_type": "lecture"},
        ]
        slots = self._make_slots(["MON", "TUE"], [(9, 10), (10, 11)])

        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result = adapter.solve()

        self.assertTrue(result.success, f"Solver failed: {result.error}")
        self.assertEqual(len(result.timetable), 4)

        # Verify that for any time slot, only ONE cohort subject is scheduled
        slot_counts = {}
        for entry in result.timetable:
            ts_id = entry["time_slot_id"]
            slot_counts[ts_id] = slot_counts.get(ts_id, 0) + 1

        for ts_id, count in slot_counts.items():
            self.assertEqual(
                count, 1, f"Cohort conflict detected: {count} subjects scheduled in slot {ts_id}"
            )
        self.assertEqual(result.cohort_stats, 1)

    def test_consecutive_lab_blocks(self):
        """Lab subjects must be scheduled in consecutive 2-hour blocks in a laboratory room."""
        subjects = [
            {
                "id": 1,
                "code": "CS-LAB1",
                "name": "Data Structures Lab",
                "faculty_id": 1,
                "required_capacity": 30,
                "sessions_per_week": 2,
                "is_lab": True,
            }
        ]
        rooms = [
            {"id": 1, "room_number": "LEC-1", "capacity": 40, "room_type": "lecture"},
            {"id": 2, "room_number": "LAB-1", "capacity": 40, "room_type": "lab"},
        ]
        # MON has consecutive slots (9-10, 10-11); TUE has isolated slot (9-10)
        slots = [
            {"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"},
            {"id": 2, "day": "MON", "start_time": "10:00", "end_time": "11:00"},
            {"id": 3, "day": "TUE", "start_time": "09:00", "end_time": "10:00"},
        ]

        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            consecutive_labs=True,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result = adapter.solve()

        self.assertTrue(result.success, f"Solver failed: {result.error}")
        self.assertEqual(len(result.timetable), 2)

        # Both sessions must be in the lab room
        for entry in result.timetable:
            self.assertEqual(entry["room_number"], "LAB-1", "Lab must be scheduled in lab room")

        # Must be consecutive on Monday (slot 1 and 2)
        scheduled_slots = {entry["time_slot_id"] for entry in result.timetable}
        self.assertEqual(scheduled_slots, {1, 2}, "Must occupy consecutive slots on the same day")
        self.assertEqual(result.lab_blocks_count, 1)

    def test_common_course_merging(self):
        """Shared common courses across departments must be merged into concurrent slots."""
        subjects = [
            {
                "id": 1,
                "code": "ENV101-CSE",
                "name": "Environmental Studies",
                "faculty_id": 5,
                "required_capacity": 30,
                "sessions_per_week": 1,
                "merge_group_id": "MG-ENV101",
            },
            {
                "id": 2,
                "code": "ENV101-ECE",
                "name": "Environmental Studies",
                "faculty_id": 5,
                "required_capacity": 30,
                "sessions_per_week": 1,
                "merge_group_id": "MG-ENV101",
            },
        ]
        rooms = [
            {"id": 1, "room_number": "SEM-101", "capacity": 80, "room_type": "seminar"},
            {"id": 2, "room_number": "LH-101", "capacity": 100, "room_type": "lecture"},
        ]
        slots = self._make_slots(["MON", "TUE"], [(9, 10), (10, 11)])

        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            merge_common_courses=True,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result = adapter.solve()

        self.assertTrue(result.success, f"Solver failed: {result.error}")
        self.assertEqual(len(result.timetable), 2)

        # Both subjects must be scheduled at the exact same time slot
        ts_1 = result.timetable[0]["time_slot_id"]
        ts_2 = result.timetable[1]["time_slot_id"]
        self.assertEqual(ts_1, ts_2, "Merged courses must share the identical time slot")
        self.assertGreaterEqual(result.merged_sessions_count, 1)

    def test_block_affinity(self):
        """Departmental subject should prefer room in designated Academic Block."""
        subjects = [
            {
                "id": 1,
                "code": "AI101",
                "name": "Intro to AI",
                "faculty_id": 1,
                "required_capacity": 30,
                "sessions_per_week": 1,
                "block_name": "Block A",
            }
        ]
        rooms = [
            {"id": 1, "room_number": "B-201", "capacity": 40, "room_type": "lecture", "block_name": "Block B"},
            {"id": 2, "room_number": "A-101", "capacity": 40, "room_type": "lecture", "block_name": "Block A"},
        ]
        slots = self._make_slots(["MON"], [(9, 10)])

        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            allow_spillover=True,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result = adapter.solve()

        self.assertTrue(result.success, f"Solver failed: {result.error}")
        self.assertEqual(result.timetable[0]["room_number"], "A-101",
                         "Subject should be assigned to designated Block A room")

    def test_multi_department_wave_execution(self):
        """Wave solver should successfully sequence multiple blocks and pass locked reservations."""
        from apps.scheduler.tasks import _wave_solve
        from apps.scheduler.models import Subject, Room, TimeSlot

        ts1 = TimeSlot.objects.create(day="MON", start_time="09:00", end_time="10:00")
        ts2 = TimeSlot.objects.create(day="MON", start_time="10:00", end_time="11:00")

        r1 = Room.objects.create(room_number="WAVE-A101", capacity=40, room_type="lecture", building="Block A")
        r2 = Room.objects.create(room_number="WAVE-B101", capacity=40, room_type="lecture", building="Block B")

        s1 = Subject.objects.create(code="WAVE-CS101", name="Intro to CS", required_capacity=30, sessions_per_week=1)
        s2 = Subject.objects.create(code="WAVE-ME101", name="Thermodynamics", required_capacity=30, sessions_per_week=1)

        subjects = [
            # Block A subjects
            {
                "id": s1.id,
                "code": s1.code,
                "name": s1.name,
                "faculty_id": None,
                "required_capacity": 30,
                "sessions_per_week": 1,
                "block_name": "Block A",
                "cohort_key": (1, 1),
                "required_tas": 0,
            },
            # Block B subjects
            {
                "id": s2.id,
                "code": s2.code,
                "name": s2.name,
                "faculty_id": None,
                "required_capacity": 30,
                "sessions_per_week": 1,
                "block_name": "Block B",
                "cohort_key": (2, 1),
                "required_tas": 0,
            },
        ]
        rooms = [
            {"id": r1.id, "room_number": r1.room_number, "capacity": 40, "room_type": "lecture", "block_name": "Block A", "building": "Block A"},
            {"id": r2.id, "room_number": r2.room_number, "capacity": 40, "room_type": "lecture", "block_name": "Block B", "building": "Block B"},
        ]
        slots = [
            {"id": ts1.id, "day": "MON", "start_time": "09:00", "end_time": "10:00"},
            {"id": ts2.id, "day": "MON", "start_time": "10:00", "end_time": "11:00"},
        ]

        res = _wave_solve(
            subjects=subjects,
            rooms=rooms,
            all_time_slots=slots,
            resources=[],
            locked_entries=[],
            excluded_slots_int={},
            pref_room_types_int={},
            avoid_back_to_back=False,
            max_classes_per_day=1,
            balance_faculty_workload=False,
            auto_schedule_office_hours=False,
            merge_common_courses=False,
            consecutive_labs=False,
            allow_spillover=True,
            config={"draft_name": "Test Wave Sandbox"},
            db_locked_set=set(),
        )

        self.assertTrue(res.get("success"), f"Wave solve failed: {res.get('error')}")
        self.assertEqual(res.get("count"), 2)

    def test_balanced_day_distribution(self):
        """Subjects of a cohort must be distributed evenly across all active days rather than clustered."""
        # 4 subjects with 3 sessions each = 12 sessions total
        subjects = [
            {
                "id": 1,
                "code": "MATH101",
                "name": "Mathematics I",
                "faculty_id": 1,
                "required_capacity": 30,
                "sessions_per_week": 3,
                "cohort_key": (1, 1),
            },
            {
                "id": 2,
                "code": "CS101",
                "name": "Intro to CS",
                "faculty_id": 2,
                "required_capacity": 30,
                "sessions_per_week": 3,
                "cohort_key": (1, 1),
            },
            {
                "id": 3,
                "code": "ENG101",
                "name": "English Communication",
                "faculty_id": 3,
                "required_capacity": 30,
                "sessions_per_week": 3,
                "cohort_key": (1, 1),
            },
            {
                "id": 4,
                "code": "PHY101",
                "name": "Physics",
                "faculty_id": 4,
                "required_capacity": 30,
                "sessions_per_week": 3,
                "cohort_key": (1, 1),
            },
        ]
        rooms = [
            {"id": 1, "room_number": "R101", "capacity": 40, "room_type": "lecture"},
            {"id": 2, "room_number": "R102", "capacity": 40, "room_type": "lecture"},
        ]
        # 6 days (MON through SAT), 4 time slots per day = 24 slots total
        slots = self._make_slots(
            ["MON", "TUE", "WED", "THU", "FRI", "SAT"],
            [(9, 10), (10, 11), (11, 12), (12, 13)]
        )

        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            max_classes_per_day=1,
        )
        adapter = ORToolsSolverAdapter(solver_input)
        result = adapter.solve()

        self.assertTrue(result.success, f"Solver failed: {result.error}")
        self.assertEqual(len(result.timetable), 12)

        # Count sessions per day
        from collections import Counter
        day_counts = Counter(entry["day"] for entry in result.timetable)

        # Target: 12 sessions across 6 days = exactly 2 sessions per day!
        # Every day should have at least 1 session and at most 3 sessions
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            count = day_counts.get(day, 0)
            self.assertGreaterEqual(
                count, 1, f"Day {day} has 0 sessions scheduled! Expected balanced distribution."
            )
            self.assertLessEqual(
                count, 3, f"Day {day} has {count} sessions (overloaded)! Expected <= 3."
            )


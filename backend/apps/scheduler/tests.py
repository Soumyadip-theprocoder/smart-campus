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

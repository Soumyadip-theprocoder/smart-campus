"""
Tests for the CSP Timetable Solver.
Verifies constraint satisfaction, edge cases, and solution quality.
"""

from apps.scheduler.csp_solver import ScheduleCSP
from django.test import TestCase


class CSPSolverBasicTests(TestCase):
    """Basic tests for the ScheduleCSP solver."""

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

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertTrue(len(timetable) > 0, "Solver should find a solution")
        self.assertEqual(len(timetable), 4)  # 2 subjects * 2 sessions

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

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 6)
        # Check no faculty time conflicts
        time_slots_used = {}
        for entry in timetable:
            ts = entry["day"] + entry["start_time"]
            fid = entry["faculty_id"]
            key = (fid, ts)
            self.assertNotIn(
                key, time_slots_used, f"Faculty {fid} double-booked at {ts}"
            )
            time_slots_used[key] = entry["subject_code"]

    def test_no_room_conflict(self):
        """Same room should never host two classes at the same time."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 2},
                {"code": "CS2", "faculty_id": 2, "sessions": 2},
                {"code": "CS3", "faculty_id": 3, "sessions": 2},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},  # only one room!
            ]
        )
        slots = self._make_slots(
            ["MON", "TUE", "WED", "THU", "FRI", "SAT"],
            [(9, 10), (10, 11), (11, 12)],
        )

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 6)
        room_slots = set()
        for entry in timetable:
            key = (entry["room_number"], entry["day"], entry["start_time"])
            self.assertNotIn(
                key, room_slots, f"Room {entry['room_number']} double-booked"
            )
            room_slots.add(key)

    def test_room_capacity_constraint(self):
        """Subject requiring capacity 50 should not be assigned to a room with capacity 30."""
        subjects = self._make_subjects(
            [
                {"code": "BIG", "faculty_id": 1, "capacity": 50, "sessions": 1},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "SMALL", "capacity": 30},
                {"number": "LARGE", "capacity": 60},
            ]
        )
        slots = self._make_slots(["MON"], [(9, 10)])

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 1)
        self.assertEqual(timetable[0]["room_number"], "LARGE")

    def test_same_subject_not_twice_per_day(self):
        """By default, a subject should not appear twice on the same day."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 3},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE", "WED"], [(9, 10), (10, 11), (11, 12)])

        csp = ScheduleCSP(subjects, rooms, slots, max_classes_per_day=1)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 3)
        days_used = [e["day"] for e in timetable]
        self.assertEqual(
            len(days_used),
            len(set(days_used)),
            "Same subject scheduled twice on the same day",
        )

    def test_impossible_schedule_returns_empty(self):
        """When constraints are unsatisfiable, solver should return empty list."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 3},
                {"code": "CS2", "faculty_id": 1, "sessions": 3},  # same faculty
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
            ]
        )
        # Only 2 slots, but need 6 sessions — impossible with same faculty
        slots = self._make_slots(["MON"], [(9, 10), (10, 11)])

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(
            len(timetable), 0, "Should return empty for impossible schedule"
        )

    def test_locked_entries_respected(self):
        """Locked entries should appear exactly as specified in the solution."""
        subjects = self._make_subjects(
            [
                {"code": "CS1", "faculty_id": 1, "sessions": 2},
            ]
        )
        rooms = self._make_rooms(
            [
                {"number": "R1", "capacity": 40},
                {"number": "R2", "capacity": 40},
            ]
        )
        slots = self._make_slots(["MON", "TUE"], [(9, 10), (10, 11)])

        locked = [
            {"subject_id": 1, "room_id": 2, "time_slot_id": 1}
        ]  # CS1 locked to R2 on MON 9-10

        csp = ScheduleCSP(subjects, rooms, slots, locked_entries=locked)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 2)
        locked_entry = [
            e for e in timetable if e["day"] == "MON" and e["start_time"] == "09:00"
        ]
        self.assertEqual(len(locked_entry), 1)
        self.assertEqual(locked_entry[0]["room_number"], "R2")


class CSPSolverEdgeCaseTests(TestCase):
    """Edge case tests for the solver."""

    def test_single_subject_single_session(self):
        subjects = [
            {
                "id": 1,
                "code": "SOLO",
                "name": "Solo",
                "faculty_id": 1,
                "required_capacity": 10,
                "sessions_per_week": 1,
            }
        ]
        rooms = [{"id": 1, "room_number": "R1", "capacity": 20, "building": "Main"}]
        slots = [{"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"}]

        csp = ScheduleCSP(subjects, rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 1)
        self.assertEqual(timetable[0]["subject_code"], "SOLO")

    def test_empty_subjects(self):
        rooms = [{"id": 1, "room_number": "R1", "capacity": 20, "building": "Main"}]
        slots = [{"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"}]

        csp = ScheduleCSP([], rooms, slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 0)

    def test_zero_rooms(self):
        subjects = [
            {
                "id": 1,
                "code": "SOLO",
                "faculty_id": 1,
                "sessions_per_week": 1,
                "required_capacity": 10,
            }
        ]
        slots = [{"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"}]

        csp = ScheduleCSP(subjects, [], slots)
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 0)

    def test_zero_slots(self):
        subjects = [
            {
                "id": 1,
                "code": "SOLO",
                "faculty_id": 1,
                "sessions_per_week": 1,
                "required_capacity": 10,
            }
        ]
        rooms = [{"id": 1, "room_number": "R1", "capacity": 20}]

        csp = ScheduleCSP(subjects, rooms, [])
        timetable = csp.get_timetable()

        self.assertEqual(len(timetable), 0)

    def test_conflicting_locked_entries(self):
        subjects = [
            {
                "id": 1,
                "code": "S1",
                "faculty_id": 1,
                "sessions_per_week": 1,
                "required_capacity": 10,
            }
        ]
        rooms = [{"id": 1, "room_number": "R1", "capacity": 20}]
        slots = [{"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"}]

        # Two subjects locked to the same room and same time
        locked = [
            {"subject_id": 1, "room_id": 1, "time_slot_id": 1},
            {
                "subject_id": 2,
                "room_id": 1,
                "time_slot_id": 1,
            },  # Subject 2 doesn't exist but let's simulate a bad lock
        ]

        csp = ScheduleCSP(subjects, rooms, slots, locked_entries=locked)
        # Should either ignore the invalid lock, fail gracefully, or return empty
        timetable = csp.get_timetable()
        self.assertEqual(len(timetable), 0)

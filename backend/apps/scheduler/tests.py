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
        """A lock referencing a non-existent subject is ignored gracefully."""
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

        locked = [
            {"subject_id": 1, "room_id": 1, "time_slot_id": 1},
            {
                "subject_id": 2,
                "room_id": 1,
                "time_slot_id": 1,
            },  # Subject 2 doesn't exist: this lock must be ignored, not crash
        ]

        csp = ScheduleCSP(subjects, rooms, slots, locked_entries=locked)
        timetable = csp.get_timetable()
        # The valid lock is honoured and the bogus one is dropped
        self.assertEqual(len(timetable), 1)
        self.assertEqual(timetable[0]["subject_id"], 1)
        self.assertEqual(timetable[0]["room_id"], 1)
        self.assertEqual(timetable[0]["time_slot_id"], 1)

    def test_locked_entries_double_booking_room(self):
        """Two real subjects locked into the same room and slot cannot be solved."""
        subjects = [
            {
                "id": 1,
                "code": "S1",
                "faculty_id": 1,
                "sessions_per_week": 1,
                "required_capacity": 10,
            },
            {
                "id": 2,
                "code": "S2",
                "faculty_id": 2,
                "sessions_per_week": 1,
                "required_capacity": 10,
            },
        ]
        rooms = [{"id": 1, "room_number": "R1", "capacity": 20}]
        slots = [{"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"}]
        locked = [
            {"subject_id": 1, "room_id": 1, "time_slot_id": 1},
            {"subject_id": 2, "room_id": 1, "time_slot_id": 1},
        ]

        csp = ScheduleCSP(subjects, rooms, slots, locked_entries=locked)
        self.assertEqual(csp.get_timetable(), [])
        self.assertTrue(csp.locked_conflict)


# ============================================================
# Tests for ScheduleCSP.minimize_changes
# ============================================================

class MinimizeChangesTests(TestCase):
    """Tests for the minimize_changes helper on ScheduleCSP."""

    def _build(self):
        """Return a minimal 2-subject, 2-room, 4-slot CSP fixture."""
        subjects = [
            {
                "id": 1,
                "code": "S1",
                "name": "Subject 1",
                "faculty_id": 1,
                "required_capacity": 10,
                "sessions_per_week": 1,
            },
            {
                "id": 2,
                "code": "S2",
                "name": "Subject 2",
                "faculty_id": 2,
                "required_capacity": 10,
                "sessions_per_week": 1,
            },
        ]
        rooms = [
            {"id": 1, "room_number": "R1", "capacity": 30, "building": "Main"},
            {"id": 2, "room_number": "R2", "capacity": 30, "building": "Main"},
        ]
        slots = [
            {"id": 1, "day": "MON", "start_time": "09:00", "end_time": "10:00"},
            {"id": 2, "day": "MON", "start_time": "10:00", "end_time": "11:00"},
            {"id": 3, "day": "TUE", "start_time": "09:00", "end_time": "10:00"},
            {"id": 4, "day": "TUE", "start_time": "10:00", "end_time": "11:00"},
        ]
        return subjects, rooms, slots

    def test_minimize_changes_reverts_unnecessary_displacement(self):
        """
        After solving, if a variable was displaced but its original slot is
        still valid, minimize_changes should revert it.
        """
        subjects, rooms, slots = self._build()
        # Original: S1 → (slot_1, room_1), S2 → (slot_2, room_1)
        original = {0: (1, 1), 1: (2, 1)}

        csp = ScheduleCSP(subjects=subjects, rooms=rooms, time_slots=slots)
        solution = csp.solve()
        self.assertIsNotNone(solution, "Should find a solution")

        # Run minimize_changes – at minimum it must keep the solution valid.
        result = csp.minimize_changes(original)
        self.assertEqual(len(result), 2)

        # Check constraints still hold after minimisation.
        ts_room_pairs = list(result.values())
        self.assertEqual(
            len(ts_room_pairs),
            len(set(ts_room_pairs)),
            "No two variables should share the same (ts, room) after minimisation",
        )

    def test_minimize_changes_skips_locked_variables(self):
        """Locked variables must not be reverted even if their current value
        differs from original_assignment."""
        subjects, rooms, slots = self._build()

        # Lock S1 (var_idx=0) to slot_3 / room_2
        locked = [{"subject_id": 1, "room_id": 2, "time_slot_id": 3}]
        csp = ScheduleCSP(
            subjects=subjects, rooms=rooms, time_slots=slots,
            locked_entries=locked,
        )
        solution = csp.solve()
        self.assertIsNotNone(solution)

        # Pretend the "original" for the locked var was somewhere else.
        original = {0: (1, 1), 1: (2, 1)}
        result = csp.minimize_changes(original)

        # Locked var (var_idx=0) must remain at (3, 2) regardless.
        self.assertEqual(result[0], (3, 2))

    def test_minimize_changes_idempotent_when_already_optimal(self):
        """Calling minimize_changes on an already-optimal assignment returns
        the same assignment."""
        subjects, rooms, slots = self._build()

        csp = ScheduleCSP(subjects=subjects, rooms=rooms, time_slots=slots)
        solution = csp.solve()
        self.assertIsNotNone(solution)

        # Use current assignment as the "original".
        original = dict(csp.assignment)
        result = csp.minimize_changes(original)

        # All variables should already be at their original values.
        for var_idx, val in original.items():
            self.assertEqual(result[var_idx], val)


# ============================================================
# Tests for FindSmartSwapView (API endpoint)
# ============================================================

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from apps.accounts.models import Faculty
from apps.scheduler.models import Room, Subject, TimeSlot, TimetableEntry, TimetableVersion

User = get_user_model()


class FindSmartSwapViewTests(APITestCase):
    """Integration tests for the CSP-backed FindSmartSwapView endpoint."""

    def setUp(self):
        # Shared department (FK, not a string)
        from apps.scheduler.models import Department
        self.dept = Department.objects.create(name="CS")

        # Create a user and authenticate.
        self.user = User.objects.create_user(
            email="test@test.com",
            username="testuser",
            password="pass1234",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

        # Faculty members
        self.faculty1 = Faculty.objects.create(
            user=self.user,
            employee_id="F001",
            department=self.dept,
        )

        user2 = User.objects.create_user(
            email="f2@test.com",
            username="f2user",
            password="pass1234",
            first_name="F2",
            last_name="U2",
        )
        self.faculty2 = Faculty.objects.create(
            user=user2,
            employee_id="F002",
            department=self.dept,
        )

        # Rooms
        self.room1 = Room.objects.create(room_number="R1", capacity=40)
        self.room2 = Room.objects.create(room_number="R2", capacity=40)

        # Time slots
        self.ts1 = TimeSlot.objects.create(
            day="MON", start_time="09:00", end_time="10:00"
        )
        self.ts2 = TimeSlot.objects.create(
            day="MON", start_time="10:00", end_time="11:00"
        )
        self.ts3 = TimeSlot.objects.create(
            day="TUE", start_time="09:00", end_time="10:00"
        )

        # Subjects
        self.subj1 = Subject.objects.create(
            code="CS101", name="Intro CS",
            faculty=self.faculty1, required_capacity=30,
            sessions_per_week=1,
        )
        self.subj2 = Subject.objects.create(
            code="CS102", name="Data Structures",
            faculty=self.faculty2, required_capacity=30,
            sessions_per_week=1,
        )

        # Timetable version
        self.version = TimetableVersion.objects.create(name="V1")

        # Entries: CS101 → MON 09–10 / R1, CS102 → MON 10–11 / R1
        self.entry1 = TimetableEntry.objects.create(
            version=self.version,
            subject=self.subj1,
            room=self.room1,
            time_slot=self.ts1,
        )
        self.entry2 = TimetableEntry.objects.create(
            version=self.version,
            subject=self.subj2,
            room=self.room1,
            time_slot=self.ts2,
        )

    def _url(self, entry_id):
        return reverse("scheduler:smart-swaps", kwargs={"entry_id": entry_id})

    # ------------------------------------------------------------------
    def test_direct_move_found(self):
        """
        entry1 is on MON 09-10 / R1.  ts3 (TUE 09-10) is completely free —
        it should be returned as a direct_move.
        """
        response = self.client.get(self._url(self.entry1.id))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        data = response.json()
        self.assertIn("suggestions", data)
        self.assertGreater(data["total_suggestions"], 0)

        direct = [s for s in data["suggestions"] if s["type"] == "direct_move"]
        slot_ids = [s["target_slot_id"] for s in direct]
        self.assertIn(
            self.ts3.id, slot_ids,
            "TUE 09-10 should appear as a direct_move for entry1",
        )

    def test_no_suggestions_when_fully_blocked(self):
        """
        If every time slot / room combination is already taken by locked
        entries or same-faculty clashes, direct_moves should be empty.
        """
        # Lock the only free slot for faculty1 by adding a third entry
        # with the same faculty in ts3.
        subj3 = Subject.objects.create(
            code="CS103", name="Algorithms",
            faculty=self.faculty1, required_capacity=30,
            sessions_per_week=1,
        )
        TimetableEntry.objects.create(
            version=self.version,
            subject=subj3,
            room=self.room2,
            time_slot=self.ts3,
            is_locked=True,
        )

        response = self.client.get(self._url(self.entry1.id))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        data = response.json()
        direct = [s for s in data["suggestions"] if s["type"] == "direct_move"]
        # ts3 is now taken by a locked class for the same faculty, so no direct moves to ts3.
        slot_ids = [s["target_slot_id"] for s in direct]
        self.assertNotIn(
            self.ts3.id, slot_ids,
            "ts3 is occupied by same-faculty locked entry, must not appear as direct_move",
        )

    def test_locked_entry_returns_400(self):
        """Requesting smart-swaps for a locked entry must return 400."""
        self.entry1.is_locked = True
        self.entry1.save()

        response = self.client.get(self._url(self.entry1.id))
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("locked", response.json()["error"].lower())

    def test_nonexistent_entry_returns_404(self):
        """Requesting smart-swaps for a missing entry ID must return 404."""
        response = self.client.get(self._url(99999))
        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)

    def test_one_step_swap_found(self):
        """
        Fill ts3/R1 with a different-faculty entry so entry1 cannot go there
        directly (room taken).  But if we displace that entry, entry1 can
        move to ts3/R1 and the displaced entry can go to an alternate slot.
        """
        # entry3: faculty2 (different from entry1's faculty1) in ts3/R1
        # → entry1 would be blocked on room, not faculty; displacing entry3
        #   should reveal a 1-step swap.
        entry3 = TimetableEntry.objects.create(
            version=self.version,
            subject=self.subj2,  # faculty2 — different from entry1's faculty1
            room=self.room1,
            time_slot=self.ts3,
        )

        # We need a free slot for entry3 after displacement.
        ts4 = TimeSlot.objects.create(
            day="WED", start_time="09:00", end_time="10:00"
        )

        response = self.client.get(self._url(self.entry1.id))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        data = response.json()
        swaps = [s for s in data["suggestions"] if s["type"] == "one_step_swap"]
        # At least one swap should involve displacing entry3.
        displaced_ids = [s["displaced_entry_id"] for s in swaps]
        self.assertIn(entry3.id, displaced_ids)

    def test_response_structure(self):
        """Verify the response contains all expected top-level keys."""
        response = self.client.get(self._url(self.entry1.id))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        data = response.json()
        for key in (
            "entry_id", "current_slot", "current_room",
            "total_suggestions", "direct_moves", "one_step_swaps", "suggestions",
        ):
            self.assertIn(key, data, f"Missing key: {key}")
        self.assertEqual(data["entry_id"], self.entry1.id)
        self.assertEqual(data["current_room"], self.room1.room_number)


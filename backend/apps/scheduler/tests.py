"""
Comprehensive unit tests for the CSP Timetable Solver.

Tests cover:
  1. Basic solving — correct number of sessions generated
  2. Faculty conflict — no faculty teaches 2 classes at same time
  3. Room conflict — no room hosts 2 classes at same time
  4. Room capacity — rooms satisfy required capacity
  5. Max classes per day — same subject doesn't exceed daily limit
  6. Excluded time slots — blocked slots are never assigned
  7. Locked entries — pre-assigned slots remain unchanged
  8. Preferred room types — preferred rooms tried first
  9. Back-to-back avoidance — consecutive slots avoided for same faculty
  10. Impossible constraints — solver returns empty when unsolvable
  11. Single subject / single room edge cases
  12. Large-scale stress test
  13. Django API integration test
"""
from datetime import time
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.scheduler.csp_solver import ScheduleCSP
from apps.accounts.models import User, Faculty
from apps.scheduler.models import Subject, Room, TimeSlot, TimetableEntry


# ─────────────────────────────────────────────────────────────────────
# Helper: build test data dicts for the pure-Python CSP solver
# ─────────────────────────────────────────────────────────────────────

def make_subjects(specs):
    """
    specs: list of (id, code, faculty_id, sessions_per_week, required_capacity)
    """
    return [
        {
            'id': s[0], 'code': s[1], 'name': f'Subject {s[1]}',
            'faculty_id': s[2], 'sessions_per_week': s[3],
            'required_capacity': s[4],
        }
        for s in specs
    ]


def make_rooms(specs):
    """specs: list of (id, room_number, capacity, room_type?)"""
    return [
        {
            'id': r[0], 'room_number': r[1], 'capacity': r[2],
            'room_type': r[3] if len(r) > 3 else 'lecture',
        }
        for r in specs
    ]


def make_timeslots(specs):
    """specs: list of (id, day, start_time, end_time)"""
    return [
        {'id': t[0], 'day': t[1], 'start_time': t[2], 'end_time': t[3]}
        for t in specs
    ]


def build_standard_timeslots():
    """5 days × 6 slots = 30 time slots."""
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    hours = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]
    slots = []
    ts_id = 1
    for day in days:
        for start, end in hours:
            slots.append({'id': ts_id, 'day': day, 'start_time': start, 'end_time': end})
            ts_id += 1
    return slots


# ═════════════════════════════════════════════════════════════════════
# Pure-Python CSP Solver Tests (no Django DB required)
# ═════════════════════════════════════════════════════════════════════

class TestCSPBasicSolving(TestCase):
    """Test that the solver produces a valid timetable."""

    def test_basic_single_subject(self):
        """One subject, one room, enough slots → should solve."""
        subjects = make_subjects([(1, 'CS101', 1, 3, 30)])
        rooms = make_rooms([(1, 'R101', 40)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 3, "Should schedule 3 sessions")

    def test_correct_session_count(self):
        """Multiple subjects → total sessions = sum of sessions_per_week."""
        subjects = make_subjects([
            (1, 'CS101', 1, 3, 30),
            (2, 'CS102', 2, 2, 30),
            (3, 'MA201', 3, 4, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60), (2, 'R102', 60)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 3 + 2 + 4, "Should schedule 9 total sessions")

    def test_output_format(self):
        """Check that output contains all required keys."""
        subjects = make_subjects([(1, 'CS101', 1, 1, 30)])
        rooms = make_rooms([(1, 'R101', 40)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 1)
        entry = result[0]
        required_keys = [
            'subject_id', 'subject_code', 'faculty_id',
            'room_id', 'room_number', 'time_slot_id',
            'day', 'start_time', 'end_time',
        ]
        for key in required_keys:
            self.assertIn(key, entry, f"Missing key: {key}")

    def test_sorted_output(self):
        """Timetable entries should be sorted by day then start_time."""
        subjects = make_subjects([
            (1, 'CS101', 1, 3, 30),
            (2, 'CS102', 2, 3, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5}
        for i in range(len(result) - 1):
            a = (day_order[result[i]['day']], result[i]['start_time'])
            b = (day_order[result[i + 1]['day']], result[i + 1]['start_time'])
            self.assertLessEqual(a, b, "Output should be sorted by day then time")


class TestCSPFacultyConflict(TestCase):
    """Constraint 1: No faculty member teaches 2 classes at the same time."""

    def test_no_faculty_conflict(self):
        """Same faculty, multiple subjects → never double-booked."""
        # Faculty 1 teaches both subjects
        subjects = make_subjects([
            (1, 'CS101', 1, 3, 30),
            (2, 'CS102', 1, 3, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60), (2, 'R102', 60)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 6)

        # Check: no two entries share the same time_slot_id
        # when they have the same faculty_id
        for i, a in enumerate(result):
            for j, b in enumerate(result):
                if i < j and a['faculty_id'] == b['faculty_id']:
                    self.assertNotEqual(
                        a['time_slot_id'], b['time_slot_id'],
                        f"Faculty conflict: {a['subject_code']} and {b['subject_code']} "
                        f"both assigned to slot {a['time_slot_id']}"
                    )


class TestCSPRoomConflict(TestCase):
    """Constraint 2: No room hosts 2 classes at the same time."""

    def test_no_room_conflict(self):
        """Multiple subjects, single room → no overlapping assignments."""
        subjects = make_subjects([
            (1, 'CS101', 1, 3, 30),
            (2, 'CS102', 2, 3, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60)])  # Only 1 room!
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 6)

        # Check: no two entries share same (time_slot_id, room_id)
        assigned_slots = set()
        for entry in result:
            key = (entry['time_slot_id'], entry['room_id'])
            self.assertNotIn(
                key, assigned_slots,
                f"Room conflict: slot {entry['time_slot_id']} room {entry['room_number']} double-booked"
            )
            assigned_slots.add(key)


class TestCSPRoomCapacity(TestCase):
    """Constraint 3: Room capacity >= subject's required capacity."""

    def test_capacity_respected(self):
        """Subject requiring 50 seats → only assigned to rooms with cap >= 50."""
        subjects = make_subjects([(1, 'CS101', 1, 2, 50)])
        rooms = make_rooms([
            (1, 'R-Small', 20),   # Too small
            (2, 'R-Big', 60),     # Large enough
        ])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 2)
        for entry in result:
            self.assertEqual(entry['room_id'], 2, "Should only use the big room")
            self.assertEqual(entry['room_number'], 'R-Big')

    def test_no_room_large_enough(self):
        """Subject requires more capacity than any room → unsolvable."""
        subjects = make_subjects([(1, 'CS101', 1, 1, 200)])
        rooms = make_rooms([(1, 'R101', 50)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(result, [], "Should return empty — no room large enough")


class TestCSPMaxClassesPerDay(TestCase):
    """Constraint 4: Same subject not exceeding max_classes_per_day."""

    def test_default_max_one_per_day(self):
        """Default: max 1 session per subject per day."""
        subjects = make_subjects([(1, 'CS101', 1, 5, 30)])  # 5 sessions
        rooms = make_rooms([(1, 'R101', 60)])
        ts = build_standard_timeslots()  # 5 days × 6 slots

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        self.assertEqual(len(result), 5)

        # Each day should have at most 1 session of CS101
        from collections import Counter
        day_counts = Counter(e['day'] for e in result)
        for day, count in day_counts.items():
            self.assertLessEqual(count, 1, f"Max 1 class per day violated on {day}")

    def test_max_two_per_day(self):
        """Allow 2 sessions per subject per day."""
        subjects = make_subjects([(1, 'CS101', 1, 4, 30)])
        rooms = make_rooms([(1, 'R101', 60)])
        # Only 2 days
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
            (3, 'MON', time(11, 0), time(12, 0)),
            (4, 'TUE', time(9, 0), time(10, 0)),
            (5, 'TUE', time(10, 0), time(11, 0)),
            (6, 'TUE', time(11, 0), time(12, 0)),
        ])

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=2)
        result = solver.get_timetable()

        self.assertEqual(len(result), 4)
        from collections import Counter
        day_counts = Counter(e['day'] for e in result)
        for day, count in day_counts.items():
            self.assertLessEqual(count, 2, f"Max 2 per day violated on {day}")


class TestCSPExcludedSlots(TestCase):
    """Constraint 5: Excluded time slots per subject."""

    def test_excluded_slots_not_used(self):
        """Slots marked excluded should never appear in the result."""
        subjects = make_subjects([(1, 'CS101', 1, 2, 30)])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
            (3, 'TUE', time(9, 0), time(10, 0)),
            (4, 'WED', time(9, 0), time(10, 0)),
        ])

        # Exclude slots 1 and 2 (all of Monday)
        solver = ScheduleCSP(
            subjects, rooms, ts,
            excluded_slots={1: [1, 2]}
        )
        result = solver.get_timetable()

        self.assertEqual(len(result), 2)
        for entry in result:
            self.assertNotIn(
                entry['time_slot_id'], [1, 2],
                f"Excluded slot {entry['time_slot_id']} was assigned!"
            )
            self.assertNotEqual(entry['day'], 'MON')

    def test_all_slots_excluded_unsolvable(self):
        """If all slots excluded for a subject → unsolvable."""
        subjects = make_subjects([(1, 'CS101', 1, 1, 30)])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'TUE', time(9, 0), time(10, 0)),
        ])

        solver = ScheduleCSP(
            subjects, rooms, ts,
            excluded_slots={1: [1, 2]}  # Exclude ALL slots
        )
        result = solver.get_timetable()
        self.assertEqual(result, [])


class TestCSPLockedEntries(TestCase):
    """Constraint 6: Locked entries are pre-assigned and immovable."""

    def test_locked_entry_preserved(self):
        """A locked entry must appear in the solution at its specified slot/room."""
        subjects = make_subjects([(1, 'CS101', 1, 2, 30)])
        rooms = make_rooms([(1, 'R101', 60), (2, 'R102', 60)])
        ts = build_standard_timeslots()

        locked = [{'subject_id': 1, 'room_id': 2, 'time_slot_id': 5}]

        solver = ScheduleCSP(subjects, rooms, ts, locked_entries=locked)
        result = solver.get_timetable()

        self.assertEqual(len(result), 2)

        # Find the entry that was locked
        locked_found = [
            e for e in result
            if e['time_slot_id'] == 5 and e['room_id'] == 2 and e['subject_id'] == 1
        ]
        self.assertEqual(
            len(locked_found), 1,
            "Locked entry (subject=1, room=2, slot=5) not found in result"
        )


class TestCSPPreferredRoomTypes(TestCase):
    """Constraint 7: Preferred room types (soft constraint)."""

    def test_preferred_room_type_used(self):
        """When a lab is preferred, solver should use lab rooms first."""
        subjects = make_subjects([(1, 'CS101', 1, 1, 20)])
        rooms = make_rooms([
            (1, 'LH-101', 60, 'lecture'),
            (2, 'LAB-101', 30, 'lab'),
        ])
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
        ])

        solver = ScheduleCSP(
            subjects, rooms, ts,
            preferred_room_types={1: 'lab'}
        )
        result = solver.get_timetable()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['room_id'], 2, "Should prefer the lab room")
        self.assertEqual(result[0]['room_number'], 'LAB-101')


class TestCSPBackToBackAvoidance(TestCase):
    """Constraint 8: Avoid back-to-back classes for same faculty."""

    def test_back_to_back_avoided(self):
        """Same faculty, 2 subjects → should not be in consecutive slots."""
        subjects = make_subjects([
            (1, 'CS101', 1, 1, 30),
            (2, 'CS102', 1, 1, 30),  # Same faculty!
        ])
        rooms = make_rooms([(1, 'R101', 60), (2, 'R102', 60)])
        # Only 3 slots on Monday — slot 1→2 and 2→3 are consecutive
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
            (3, 'MON', time(11, 0), time(12, 0)),
            (4, 'TUE', time(9, 0), time(10, 0)),
            (5, 'TUE', time(10, 0), time(11, 0)),
        ])

        solver = ScheduleCSP(
            subjects, rooms, ts,
            avoid_back_to_back=True,
        )
        result = solver.get_timetable()

        self.assertEqual(len(result), 2)

        # Find entries for faculty 1
        fac1_entries = [e for e in result if e['faculty_id'] == 1]
        if len(fac1_entries) == 2:
            ts1 = solver._ts_map[fac1_entries[0]['time_slot_id']]
            ts2 = solver._ts_map[fac1_entries[1]['time_slot_id']]
            if ts1['day'] == ts2['day']:
                # They shouldn't be consecutive
                self.assertFalse(
                    ts1['end_time'] == ts2['start_time'] or ts2['end_time'] == ts1['start_time'],
                    "Back-to-back classes scheduled for same faculty!"
                )

    def test_back_to_back_allowed_when_disabled(self):
        """When avoid_back_to_back=False, consecutive slots are allowed."""
        subjects = make_subjects([
            (1, 'CS101', 1, 1, 30),
            (2, 'CS102', 1, 1, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60)])
        # Only 2 consecutive slots on Monday — forces back-to-back
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
        ])

        solver = ScheduleCSP(subjects, rooms, ts, avoid_back_to_back=False)
        result = solver.get_timetable()

        # With 1 room and 2 consecutive slots, the only option IS back-to-back
        self.assertEqual(len(result), 2, "Should solve even with back-to-back")


class TestCSPImpossibleConstraints(TestCase):
    """Test that the solver correctly returns empty for unsolvable problems."""

    def test_not_enough_slots(self):
        """More sessions than available slots → unsolvable."""
        subjects = make_subjects([(1, 'CS101', 1, 5, 30)])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'TUE', time(9, 0), time(10, 0)),
        ])  # Only 2 slots for 5 sessions, max 1 per day

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()
        self.assertEqual(result, [])

    def test_conflicting_faculty_insufficient_slots(self):
        """Same faculty, too many subjects for available unique slots → unsolvable."""
        # Faculty 1 teaches 3 subjects, 1 session each, but only 2 slots
        subjects = make_subjects([
            (1, 'CS101', 1, 1, 30),
            (2, 'CS102', 1, 1, 30),
            (3, 'CS103', 1, 1, 30),
        ])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
        ])  # Only 2 unique slots for 3 subjects taught by same faculty

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()
        self.assertEqual(result, [])

    def test_empty_subjects(self):
        """No subjects → 0 sessions (not an error)."""
        solver = ScheduleCSP([], make_rooms([(1, 'R101', 60)]), build_standard_timeslots())
        result = solver.get_timetable()
        self.assertEqual(result, [])


class TestCSPEdgeCases(TestCase):
    """Edge cases and boundary conditions."""

    def test_single_session_single_slot(self):
        """1 subject, 1 session, 1 slot, 1 room → exactly 1 entry."""
        subjects = make_subjects([(1, 'CS101', 1, 1, 10)])
        rooms = make_rooms([(1, 'R101', 20)])
        ts = make_timeslots([(1, 'MON', time(9, 0), time(10, 0))])

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['subject_code'], 'CS101')
        self.assertEqual(result[0]['day'], 'MON')

    def test_many_rooms_selects_valid(self):
        """Multiple rooms with varying capacity — all assignments valid."""
        subjects = make_subjects([(1, 'CS101', 1, 3, 40)])
        rooms = make_rooms([
            (1, 'R-10', 10),
            (2, 'R-30', 30),
            (3, 'R-50', 50),
            (4, 'R-80', 80),
        ])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        self.assertEqual(len(result), 3)
        for entry in result:
            self.assertIn(entry['room_id'], [3, 4],
                          "Should only use rooms with capacity >= 40")

    def test_zero_sessions_per_week(self):
        """Subject with 0 sessions → no entries generated."""
        subjects = make_subjects([(1, 'CS101', 1, 0, 30)])
        rooms = make_rooms([(1, 'R101', 60)])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()
        self.assertEqual(result, [])


class TestCSPStressTest(TestCase):
    """Stress test with realistic campus-scale data."""

    def test_realistic_campus_load(self):
        """6 subjects, 4 faculty, 6 rooms, 30 time slots — mirrors seeded data."""
        subjects = make_subjects([
            (1, 'CS301', 1, 3, 50),
            (2, 'CS302', 2, 3, 50),
            (3, 'CS303', 3, 3, 50),
            (4, 'MA201', 4, 2, 40),
            (5, 'EC201', 1, 2, 30),
            (6, 'CS304', 2, 3, 30),
        ])
        rooms = make_rooms([
            (1, 'LH-101', 60, 'lecture'),
            (2, 'LH-102', 60, 'lecture'),
            (3, 'LH-201', 40, 'lecture'),
            (4, 'LAB-301', 30, 'lab'),
            (5, 'LAB-302', 30, 'lab'),
            (6, 'SR-101', 20, 'seminar'),
        ])
        ts = build_standard_timeslots()

        total_sessions = 3 + 3 + 3 + 2 + 2 + 3  # = 16

        solver = ScheduleCSP(subjects, rooms, ts)
        result = solver.get_timetable()

        # Basic: all sessions scheduled
        self.assertEqual(len(result), total_sessions,
                         f"Expected {total_sessions} sessions, got {len(result)}")

        # Validate all constraints
        for i, a in enumerate(result):
            for j, b in enumerate(result):
                if i >= j:
                    continue
                # Faculty conflict check
                if a['time_slot_id'] == b['time_slot_id']:
                    self.assertNotEqual(
                        a['faculty_id'], b['faculty_id'],
                        f"Faculty conflict between {a['subject_code']} and {b['subject_code']}"
                    )
                # Room conflict check
                if a['time_slot_id'] == b['time_slot_id']:
                    self.assertNotEqual(
                        a['room_id'], b['room_id'],
                        f"Room conflict between {a['subject_code']} and {b['subject_code']}"
                    )

    def test_with_all_advanced_constraints(self):
        """Stress test with locked entries, excluded slots, and preferences."""
        subjects = make_subjects([
            (1, 'CS301', 1, 3, 50),
            (2, 'CS302', 2, 3, 50),
            (3, 'MA201', 3, 2, 30),
        ])
        rooms = make_rooms([
            (1, 'LH-101', 60, 'lecture'),
            (2, 'LAB-301', 30, 'lab'),
            (3, 'LH-201', 40, 'lecture'),
        ])
        ts = build_standard_timeslots()

        solver = ScheduleCSP(
            subjects, rooms, ts,
            locked_entries=[{'subject_id': 1, 'room_id': 1, 'time_slot_id': 1}],
            excluded_slots={2: [1, 2, 3, 4, 5, 6]},  # CS302 can't be on Monday
            preferred_room_types={3: 'lab'},
            avoid_back_to_back=True,
            max_classes_per_day=1,
        )
        result = solver.get_timetable()

        total = 3 + 3 + 2  # = 8
        self.assertEqual(len(result), total)

        # Verify locked entry is present
        locked = [e for e in result if e['subject_id'] == 1 and e['time_slot_id'] == 1 and e['room_id'] == 1]
        self.assertEqual(len(locked), 1, "Locked entry not found")

        # Verify CS302 not on Monday (slots 1-6)
        cs302_entries = [e for e in result if e['subject_code'] == 'CS302']
        for entry in cs302_entries:
            self.assertNotEqual(entry['day'], 'MON',
                                f"CS302 should not be on Monday (excluded)")


class TestCSPConsistencyMethod(TestCase):
    """Unit tests for the is_consistent internal method."""

    def setUp(self):
        self.subjects = make_subjects([
            (1, 'CS101', 1, 1, 30),
            (2, 'CS102', 1, 1, 30),  # Same faculty as CS101
        ])
        self.rooms = make_rooms([(1, 'R101', 60), (2, 'R102', 60)])
        self.ts = make_timeslots([
            (1, 'MON', time(9, 0), time(10, 0)),
            (2, 'MON', time(10, 0), time(11, 0)),
        ])
        self.solver = ScheduleCSP(self.subjects, self.rooms, self.ts)

    def test_consistent_when_no_conflict(self):
        """Different slot, different room → consistent."""
        self.solver.assignment[0] = (1, 1)  # CS101 → slot 1, room 1
        self.assertTrue(self.solver.is_consistent(1, (2, 2)))

    def test_inconsistent_faculty_conflict(self):
        """Same slot, same faculty → inconsistent."""
        self.solver.assignment[0] = (1, 1)  # CS101 by faculty 1 at slot 1
        self.assertFalse(self.solver.is_consistent(1, (1, 2)))  # CS102 same faculty, same slot

    def test_inconsistent_room_conflict(self):
        """Same slot, same room → inconsistent."""
        self.solver.assignment[0] = (1, 1)  # CS101 → slot 1, room 1
        # Change CS102's faculty to be different
        self.solver.variables[1]['faculty_id'] = 2
        self.assertFalse(self.solver.is_consistent(1, (1, 1)))  # Same room, same slot


# ═════════════════════════════════════════════════════════════════════
# Django Integration Tests (uses DB)
# ═════════════════════════════════════════════════════════════════════

class TestGenerateAPIEndpoint(TestCase):
    """Integration test for the POST /api/scheduler/generate/ endpoint."""

    def setUp(self):
        """Seed the database with test data."""
        # Create admin user
        self.admin = User.objects.create_user(
            email='admin@test.edu',
            username='admin_test',
            password='testpass123',
            role=User.Role.ADMIN,
            first_name='Test',
            last_name='Admin',
        )

        # Create faculty
        fac_user1 = User.objects.create_user(
            email='fac1@test.edu', username='fac1',
            password='testpass123', role=User.Role.FACULTY,
            first_name='John', last_name='Smith',
        )
        fac_user2 = User.objects.create_user(
            email='fac2@test.edu', username='fac2',
            password='testpass123', role=User.Role.FACULTY,
            first_name='Jane', last_name='Doe',
        )
        self.faculty1 = Faculty.objects.create(
            user=fac_user1, employee_id='F001', department='CS',
        )
        self.faculty2 = Faculty.objects.create(
            user=fac_user2, employee_id='F002', department='CS',
        )

        # Create subjects
        self.subj1 = Subject.objects.create(
            code='CS101', name='Intro to CS', faculty=self.faculty1,
            credits=3, required_capacity=30, sessions_per_week=2,
        )
        self.subj2 = Subject.objects.create(
            code='CS102', name='Data Structures', faculty=self.faculty2,
            credits=3, required_capacity=30, sessions_per_week=2,
        )

        # Create rooms
        self.room1 = Room.objects.create(
            room_number='R-101', capacity=50, building='Main', room_type='lecture',
        )
        self.room2 = Room.objects.create(
            room_number='R-102', capacity=40, building='Main', room_type='lecture',
        )

        # Create time slots (3 days × 2 slots = 6)
        for day in ['MON', 'TUE', 'WED']:
            TimeSlot.objects.create(day=day, start_time=time(9, 0), end_time=time(10, 0))
            TimeSlot.objects.create(day=day, start_time=time(10, 0), end_time=time(11, 0))

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_generate_creates_entries(self):
        """POST /api/scheduler/generate/ → creates TimetableEntry records."""
        response = self.client.post('/api/scheduler/generate/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('timetable', response.data)
        self.assertIn('message', response.data)

        # Should have 4 entries (2 subjects × 2 sessions/week)
        self.assertEqual(len(response.data['timetable']), 4)
        self.assertEqual(TimetableEntry.objects.count(), 4)

    def test_generate_replaces_old_entries(self):
        """Calling generate twice replaces old entries."""
        self.client.post('/api/scheduler/generate/', {}, format='json')
        self.assertEqual(TimetableEntry.objects.count(), 4)

        # Generate again
        response = self.client.post('/api/scheduler/generate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Should still be 4 (old deleted, new created)
        self.assertEqual(TimetableEntry.objects.count(), 4)

    def test_generate_with_subject_filter(self):
        """Generate with only 1 subject selected → only that subject scheduled."""
        response = self.client.post(
            '/api/scheduler/generate/',
            {'subject_ids': [self.subj1.id]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['timetable']), 2)  # Only CS101's 2 sessions
        for entry in response.data['timetable']:
            self.assertEqual(entry['subject_code'], 'CS101')

    def test_generate_unauthenticated_fails(self):
        """Unauthenticated request → 401."""
        client = APIClient()
        response = client.post('/api/scheduler/generate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_timetable_list_endpoint(self):
        """GET /api/scheduler/timetable/ returns generated entries."""
        self.client.post('/api/scheduler/generate/', {}, format='json')
        response = self.client.get('/api/scheduler/timetable/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 4)

    def test_generate_no_subjects_error(self):
        """If no subjects match filter → 400 error."""
        response = self.client.post(
            '/api/scheduler/generate/',
            {'subject_ids': [999]},  # Non-existent
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

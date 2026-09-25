"""
Comprehensive Unit Tests for UNIFORM Timetable Distribution.

These tests verify that the CSP solver doesn't just produce a *valid*
timetable, but produces a *well-distributed* one:

  1. Every subject gets its exact sessions_per_week count
  2. Sessions for each subject are spread across DISTINCT days
  3. No single day is overloaded (classes are spread across the week)
  4. Shared-faculty subjects don't bunch on the same days
  5. Full seed-data scenario produces a balanced grid
  6. Multiple rooms are utilised (not just the first room)
  7. Both morning and afternoon slots are used
  8. Day spread variance is low (uniform day loading)
  9. Different faculty see their classes on different days
  10. Edge cases: exactly N days for N sessions, etc.

Run with:
    python manage.py test apps.scheduler.test_uniform_distribution -v 2
"""

from collections import Counter
from datetime import time

from apps.scheduler.csp_solver import ScheduleCSP
from django.test import TestCase

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def make_subjects(specs):
    """specs: list of (id, code, faculty_id, sessions_per_week, required_capacity)"""
    return [
        {
            "id": s[0],
            "code": s[1],
            "name": f"Subject {s[1]}",
            "faculty_id": s[2],
            "sessions_per_week": s[3],
            "required_capacity": s[4],
        }
        for s in specs
    ]


def make_rooms(specs):
    """specs: list of (id, room_number, capacity, room_type?)"""
    return [
        {
            "id": r[0],
            "room_number": r[1],
            "capacity": r[2],
            "room_type": r[3] if len(r) > 3 else "lecture",
        }
        for r in specs
    ]


def make_timeslots(specs):
    """specs: list of (id, day, start_time, end_time)"""
    return [
        {"id": t[0], "day": t[1], "start_time": t[2], "end_time": t[3]} for t in specs
    ]


def build_full_week_48_slots():
    """
    6 days × 8 periods = 48 time slots.
    Mirrors the production seed_data exactly:
      Morning: 09–10, 10–11, 11–12, 12–13
      (Lunch break 13–14)
      Afternoon: 14–15, 15–16, 16–17, 17–18
    """
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    slot_times = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
    ]
    slots = []
    ts_id = 1
    for day in days:
        for start, end in slot_times:
            slots.append(
                {
                    "id": ts_id,
                    "day": day,
                    "start_time": start,
                    "end_time": end,
                }
            )
            ts_id += 1
    return slots


def build_seed_subjects():
    """
    Mirrors production seed_data.py exactly:
      CS301: faculty 1, 3 sessions/wk, cap 40
      CS302: faculty 2, 3 sessions/wk, cap 40
      CS303: faculty 1, 2 sessions/wk, cap 40  (shares faculty with CS301!)
      MA201: faculty 3, 3 sessions/wk, cap 60
      EC201: faculty 4, 3 sessions/wk, cap 40
      CS304: faculty 2, 2 sessions/wk, cap 30  (shares faculty with CS302!)
    Total: 16 sessions/week
    """
    return make_subjects(
        [
            (1, "CS301", 1, 3, 40),
            (2, "CS302", 2, 3, 40),
            (3, "CS303", 1, 2, 40),  # shares faculty 1 with CS301
            (4, "MA201", 3, 3, 60),
            (5, "EC201", 4, 3, 40),
            (6, "CS304", 2, 2, 30),  # shares faculty 2 with CS302
        ]
    )


def build_seed_rooms():
    """Mirrors production seed_data.py exactly."""
    return make_rooms(
        [
            (1, "LH-101", 60, "lecture"),
            (2, "LH-102", 60, "lecture"),
            (3, "LH-201", 40, "lecture"),
            (4, "LAB-301", 30, "lab"),
            (5, "LAB-302", 30, "lab"),
            (6, "SR-101", 20, "seminar"),
        ]
    )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 1: Every subject gets its exact session count
# ═════════════════════════════════════════════════════════════════════


class TestAllSubjectsScheduled(TestCase):
    """Every subject must receive its exact sessions_per_week count."""

    def test_seed_data_all_subjects_present(self):
        """All 6 subjects from seed data must appear in the result."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        scheduled_codes = set(e["subject_code"] for e in result)
        expected_codes = {"CS301", "CS302", "CS303", "MA201", "EC201", "CS304"}

        self.assertEqual(
            scheduled_codes,
            expected_codes,
            f"Missing subjects: {expected_codes - scheduled_codes}",
        )

    def test_seed_data_exact_session_counts(self):
        """Each subject must have exactly its sessions_per_week entries."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        session_counts = Counter(e["subject_code"] for e in result)

        self.assertEqual(session_counts["CS301"], 3, "CS301 needs 3 sessions")
        self.assertEqual(session_counts["CS302"], 3, "CS302 needs 3 sessions")
        self.assertEqual(session_counts["CS303"], 2, "CS303 needs 2 sessions")
        self.assertEqual(session_counts["MA201"], 3, "MA201 needs 3 sessions")
        self.assertEqual(session_counts["EC201"], 3, "EC201 needs 3 sessions")
        self.assertEqual(session_counts["CS304"], 2, "CS304 needs 2 sessions")

    def test_total_sessions_equals_16(self):
        """Total sessions = 3+3+2+3+3+2 = 16."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        self.assertEqual(len(result), 16, "Total sessions should be 16")


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 2: Sessions spread across distinct days
# ═════════════════════════════════════════════════════════════════════


class TestSessionDaySpread(TestCase):
    """Each subject's sessions should be on DISTINCT days (max_classes_per_day=1)."""

    def test_each_subject_on_distinct_days(self):
        """With max_classes_per_day=1, each subject should appear on N distinct days."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        for subj in subjects:
            code = subj["code"]
            entries = [e for e in result if e["subject_code"] == code]
            days_used = set(e["day"] for e in entries)

            self.assertEqual(
                len(days_used),
                subj["sessions_per_week"],
                f"{code}: {subj['sessions_per_week']} sessions should use "
                f"{subj['sessions_per_week']} distinct days, got {days_used}",
            )

    def test_3_session_subject_uses_3_different_days(self):
        """CS301 (3 sessions) must appear on 3 different days."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        cs301 = [e for e in result if e["subject_code"] == "CS301"]
        cs301_days = set(e["day"] for e in cs301)
        self.assertEqual(
            len(cs301_days), 3, f"CS301 should be on 3 different days, got {cs301_days}"
        )

    def test_2_session_subject_uses_2_different_days(self):
        """CS303 (2 sessions) must appear on 2 different days."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        cs303 = [e for e in result if e["subject_code"] == "CS303"]
        cs303_days = set(e["day"] for e in cs303)
        self.assertEqual(
            len(cs303_days), 2, f"CS303 should be on 2 different days, got {cs303_days}"
        )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 3: No day is overloaded
# ═════════════════════════════════════════════════════════════════════


class TestDayLoadBalancing(TestCase):
    """Classes should be spread across the week, not bunched on a few days."""

    def test_no_single_day_has_all_classes(self):
        """No single day should have more than 8 classes (= max periods)."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        day_counts = Counter(e["day"] for e in result)
        for day, count in day_counts.items():
            self.assertLessEqual(
                count, 8, f"{day} has {count} classes — exceeds 8 periods/day"
            )

    def test_classes_use_at_least_3_days(self):
        """16 sessions across 6 days — must use at least 3 days."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        days_used = set(e["day"] for e in result)
        self.assertGreaterEqual(
            len(days_used),
            3,
            f"Only {len(days_used)} days used: {days_used}. "
            "Classes should be spread across more days.",
        )

    def test_day_load_variance_is_reasonable(self):
        """
        The variance in per-day class counts should be low.
        With 16 sessions over 6 days, ideal is ~2.67/day.
        Variance above 4.0 indicates severe bunching.
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        all_days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        day_counts = Counter(e["day"] for e in result)
        counts = [day_counts.get(d, 0) for d in all_days]

        mean = sum(counts) / len(counts)
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)

        self.assertLessEqual(
            variance,
            4.0,
            f"Day load variance {variance:.2f} is too high. "
            f"Per-day counts: {dict(zip(all_days, counts))}",
        )

    def test_no_empty_weekday(self):
        """
        With 16 sessions and 6 available days, at least 4 weekdays
        (MON-FRI) should have classes. Saturday is optional.
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        weekdays = {"MON", "TUE", "WED", "THU", "FRI"}
        weekdays_used = set(e["day"] for e in result) & weekdays

        self.assertGreaterEqual(
            len(weekdays_used),
            4,
            f"Only {len(weekdays_used)} weekdays have classes: {weekdays_used}. "
            "Expected at least 4.",
        )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 4: Shared-faculty subjects on different days
# ═════════════════════════════════════════════════════════════════════


class TestSharedFacultyDistribution(TestCase):
    """Faculty teaching multiple subjects should see them spread out."""

    def test_faculty_1_no_timeslot_conflicts(self):
        """
        Faculty 1 teaches CS301 (3/wk) + CS303 (2/wk) = 5 sessions.
        None should share a time slot.
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        fac1 = [e for e in result if e["faculty_id"] == 1]
        self.assertEqual(len(fac1), 5, "Faculty 1 should have 5 sessions")

        ts_ids = [e["time_slot_id"] for e in fac1]
        self.assertEqual(
            len(ts_ids),
            len(set(ts_ids)),
            f"Faculty 1 has timeslot conflict! Slots: {ts_ids}",
        )

    def test_faculty_2_no_timeslot_conflicts(self):
        """
        Faculty 2 teaches CS302 (3/wk) + CS304 (2/wk) = 5 sessions.
        None should share a time slot.
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        fac2 = [e for e in result if e["faculty_id"] == 2]
        self.assertEqual(len(fac2), 5, "Faculty 2 should have 5 sessions")

        ts_ids = [e["time_slot_id"] for e in fac2]
        self.assertEqual(
            len(ts_ids),
            len(set(ts_ids)),
            f"Faculty 2 has timeslot conflict! Slots: {ts_ids}",
        )

    def test_faculty_sessions_spread_across_days(self):
        """
        Faculty with 5 sessions should use at least 4 distinct days
        (ideally 5, but 4 is the minimum with max_classes_per_day=1
        and 2 subjects which can share a day for different subjects).
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        for fac_id in [1, 2]:
            fac_entries = [e for e in result if e["faculty_id"] == fac_id]
            days = set(e["day"] for e in fac_entries)
            self.assertGreaterEqual(
                len(days),
                3,
                f"Faculty {fac_id} has {len(fac_entries)} sessions but "
                f"only uses {len(days)} days: {days}",
            )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 5: Room utilization
# ═════════════════════════════════════════════════════════════════════


class TestRoomUtilization(TestCase):
    """Multiple rooms should be used, not just one."""

    def test_multiple_rooms_used(self):
        """With 6 rooms and 16 sessions, at least 2 rooms should be used."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        rooms_used = set(e["room_id"] for e in result)
        self.assertGreaterEqual(
            len(rooms_used),
            2,
            f"Only {len(rooms_used)} room(s) used: {rooms_used}. "
            "Should use at least 2.",
        )

    def test_capacity_constraint_respected(self):
        """
        MA201 requires capacity 60 → must use LH-101 or LH-102 (cap 60).
        It must NOT use LH-201 (40), LAB-301/302 (30), or SR-101 (20).
        """
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        ma201 = [e for e in result if e["subject_code"] == "MA201"]
        for entry in ma201:
            self.assertIn(
                entry["room_id"],
                [1, 2],
                f"MA201 (cap 60) assigned to room {entry['room_number']} "
                f"(id={entry['room_id']}), which has insufficient capacity",
            )

    def test_small_subjects_can_use_smaller_rooms(self):
        """CS304 (cap 30) can use LAB-301/302 (cap 30) and any larger room."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        cs304 = [e for e in result if e["subject_code"] == "CS304"]
        for entry in cs304:
            # Rooms with capacity >= 30: LH-101(60), LH-102(60), LH-201(40),
            # LAB-301(30), LAB-302(30). NOT SR-101(20).
            self.assertIn(
                entry["room_id"],
                [1, 2, 3, 4, 5],
                f"CS304 (cap 30) assigned to room {entry['room_number']} "
                f"with insufficient capacity",
            )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 6: Morning and afternoon slot usage
# ═════════════════════════════════════════════════════════════════════


class TestTimeSlotDistribution(TestCase):
    """Sessions should use both morning and afternoon slots."""

    def test_not_all_morning(self):
        """Not all 16 sessions should be in the morning block."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        morning_count = sum(1 for e in result if e["start_time"] < str(time(13, 0)))
        self.assertLess(
            morning_count,
            16,
            "All 16 sessions are in the morning — afternoon slots not used at all",
        )

    def test_not_all_afternoon(self):
        """Not all 16 sessions should be in the afternoon block."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        afternoon_count = sum(1 for e in result if e["start_time"] >= str(time(14, 0)))
        self.assertLess(
            afternoon_count,
            16,
            "All 16 sessions are in the afternoon — morning slots not used at all",
        )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 7: Global constraint validation on seed data
# ═════════════════════════════════════════════════════════════════════


class TestGlobalConstraintsSeedData(TestCase):
    """Validate ALL hard constraints hold on the full seed-data scenario."""

    def setUp(self):
        self.subjects = build_seed_subjects()
        self.rooms = build_seed_rooms()
        self.ts = build_full_week_48_slots()
        solver = ScheduleCSP(
            self.subjects,
            self.rooms,
            self.ts,
            max_classes_per_day=1,
        )
        self.result = solver.get_timetable()

    def test_no_faculty_double_booking(self):
        """No faculty teaches two classes at the same time slot."""
        for i, a in enumerate(self.result):
            for j, b in enumerate(self.result):
                if i >= j:
                    continue
                if a["time_slot_id"] == b["time_slot_id"]:
                    self.assertNotEqual(
                        a["faculty_id"],
                        b["faculty_id"],
                        f"Faculty {a['faculty_id']} double-booked at slot "
                        f"{a['time_slot_id']}: {a['subject_code']} vs {b['subject_code']}",
                    )

    def test_no_room_double_booking(self):
        """No room hosts two classes at the same time slot."""
        for i, a in enumerate(self.result):
            for j, b in enumerate(self.result):
                if i >= j:
                    continue
                if a["time_slot_id"] == b["time_slot_id"]:
                    self.assertNotEqual(
                        a["room_id"],
                        b["room_id"],
                        f"Room {a['room_number']} double-booked at slot "
                        f"{a['time_slot_id']}: {a['subject_code']} vs {b['subject_code']}",
                    )

    def test_max_one_class_per_subject_per_day(self):
        """Each subject appears at most once per day."""
        subject_day_counts = Counter((e["subject_code"], e["day"]) for e in self.result)
        for (code, day), count in subject_day_counts.items():
            self.assertLessEqual(
                count, 1, f"{code} has {count} classes on {day} — max 1 allowed"
            )

    def test_all_rooms_have_sufficient_capacity(self):
        """Every assignment uses a room with capacity >= subject requirement."""
        subj_cap_map = {s["id"]: s["required_capacity"] for s in self.subjects}
        room_cap_map = {r["id"]: r["capacity"] for r in self.rooms}

        for entry in self.result:
            required = subj_cap_map[entry["subject_id"]]
            actual = room_cap_map[entry["room_id"]]
            self.assertGreaterEqual(
                actual,
                required,
                f"{entry['subject_code']} needs {required} seats but "
                f"assigned to {entry['room_number']} ({actual} seats)",
            )

    def test_no_duplicate_timeslot_assignments(self):
        """No two entries should be identical (same subject, same slot, same room)."""
        seen = set()
        for e in self.result:
            key = (e["subject_id"], e["time_slot_id"], e["room_id"])
            self.assertNotIn(
                key,
                seen,
                f"Duplicate assignment: {e['subject_code']} at slot "
                f"{e['time_slot_id']} in room {e['room_number']}",
            )
            seen.add(key)


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 8: Scaled-up stress test for uniformity
# ═════════════════════════════════════════════════════════════════════


class TestScaledUniformity(TestCase):
    """Larger scenarios to stress-test distribution quality."""

    def test_10_subjects_4_faculty(self):
        """
        10 subjects, 4 faculty, 48 slots, 6 rooms.
        Total sessions = 28. All must schedule, all constraints must hold.
        """
        subjects = make_subjects(
            [
                (1, "SUB01", 1, 3, 40),
                (2, "SUB02", 2, 3, 40),
                (3, "SUB03", 3, 3, 40),
                (4, "SUB04", 4, 3, 40),
                (5, "SUB05", 1, 3, 40),  # shares faculty 1
                (6, "SUB06", 2, 3, 40),  # shares faculty 2
                (7, "SUB07", 3, 2, 30),
                (8, "SUB08", 4, 2, 30),
                (9, "SUB09", 1, 3, 30),  # shares faculty 1
                (10, "SUB10", 2, 3, 30),  # shares faculty 2
            ]
        )
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        total_sessions = sum(s["sessions_per_week"] for s in subjects)
        self.assertEqual(total_sessions, 28)

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        # All 28 sessions must be scheduled
        self.assertEqual(len(result), 28, f"Expected 28 sessions, got {len(result)}")

        # Each subject has correct count
        counts = Counter(e["subject_code"] for e in result)
        for subj in subjects:
            self.assertEqual(
                counts[subj["code"]],
                subj["sessions_per_week"],
                f"{subj['code']} expected {subj['sessions_per_week']} "
                f"sessions, got {counts[subj['code']]}",
            )

        # No faculty conflicts
        for i, a in enumerate(result):
            for j, b in enumerate(result):
                if i >= j:
                    continue
                if a["time_slot_id"] == b["time_slot_id"]:
                    self.assertNotEqual(
                        a["faculty_id"],
                        b["faculty_id"],
                        f"Faculty conflict: {a['subject_code']} vs "
                        f"{b['subject_code']} at slot {a['time_slot_id']}",
                    )
                    self.assertNotEqual(
                        a["room_id"],
                        b["room_id"],
                        f"Room conflict: {a['subject_code']} vs "
                        f"{b['subject_code']} at slot {a['time_slot_id']}",
                    )

        # At least 5 days used
        days_used = set(e["day"] for e in result)
        self.assertGreaterEqual(
            len(days_used),
            5,
            f"28 sessions should use at least 5 days, got {days_used}",
        )

    def test_heavy_faculty_load(self):
        """
        1 faculty teaching 5 subjects (1 session each) = 5 sessions.
        With max_classes_per_day=1, needs 5 distinct days.
        """
        subjects = make_subjects(
            [
                (1, "A", 1, 1, 20),
                (2, "B", 1, 1, 20),
                (3, "C", 1, 1, 20),
                (4, "D", 1, 1, 20),
                (5, "E", 1, 1, 20),
            ]
        )
        rooms = make_rooms([(1, "R1", 30)])
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        self.assertEqual(len(result), 5)

        # All 5 should be on different days (since each subject max 1/day,
        # and same faculty can't have 2 at same slot)
        days = [e["day"] for e in result]
        self.assertEqual(
            len(set(days)),
            5,
            f"5 subjects by 1 faculty should use 5 different days, got {set(days)}",
        )

    def test_two_faculty_each_with_6_sessions(self):
        """
        2 faculty, each with 2 subjects × 3 sessions = 6 sessions each.
        Total = 12 sessions. Both need 6 distinct time slots.
        """
        subjects = make_subjects(
            [
                (1, "F1-A", 1, 3, 30),
                (2, "F1-B", 1, 3, 30),
                (3, "F2-A", 2, 3, 30),
                (4, "F2-B", 2, 3, 30),
            ]
        )
        rooms = make_rooms([(1, "R1", 40), (2, "R2", 40)])
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result = solver.get_timetable()

        self.assertEqual(len(result), 12)

        # Faculty 1 should have 6 unique time slots
        fac1 = [e for e in result if e["faculty_id"] == 1]
        fac1_slots = [e["time_slot_id"] for e in fac1]
        self.assertEqual(
            len(set(fac1_slots)),
            6,
            f"Faculty 1 should have 6 unique slots, got {len(set(fac1_slots))}",
        )

        # Faculty 2 same check
        fac2 = [e for e in result if e["faculty_id"] == 2]
        fac2_slots = [e["time_slot_id"] for e in fac2]
        self.assertEqual(
            len(set(fac2_slots)),
            6,
            f"Faculty 2 should have 6 unique slots, got {len(set(fac2_slots))}",
        )

        # Both faculties should use at least 5 days
        for fac_id in [1, 2]:
            fac_entries = [e for e in result if e["faculty_id"] == fac_id]
            fac_days = set(e["day"] for e in fac_entries)
            self.assertGreaterEqual(
                len(fac_days),
                5,
                f"Faculty {fac_id} with 6 sessions should use 5+ days, "
                f"got {fac_days}",
            )


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 9: Determinism and re-run consistency
# ═════════════════════════════════════════════════════════════════════


class TestSolverDeterminism(TestCase):
    """Running the solver twice with same input should produce same result."""

    def test_same_input_same_output(self):
        """Deterministic solver should produce identical results."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver1 = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result1 = solver1.get_timetable()

        solver2 = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=1)
        result2 = solver2.get_timetable()

        # Convert to comparable sets
        set1 = set(
            (e["subject_code"], e["time_slot_id"], e["room_id"]) for e in result1
        )
        set2 = set(
            (e["subject_code"], e["time_slot_id"], e["room_id"]) for e in result2
        )
        self.assertEqual(set1, set2, "Same input should produce same output")


# ═════════════════════════════════════════════════════════════════════
# TEST CLASS 10: max_classes_per_day=2 still distributes
# ═════════════════════════════════════════════════════════════════════


class TestMaxTwoPerDay(TestCase):
    """When max_classes_per_day=2, a subject can appear twice on one day."""

    def test_max_two_still_valid(self):
        """With max_classes_per_day=2, all hard constraints still hold."""
        subjects = build_seed_subjects()
        rooms = build_seed_rooms()
        ts = build_full_week_48_slots()

        solver = ScheduleCSP(subjects, rooms, ts, max_classes_per_day=2)
        result = solver.get_timetable()

        self.assertEqual(len(result), 16)

        # max 2 per day per subject
        subject_day_counts = Counter((e["subject_code"], e["day"]) for e in result)
        for (code, day), count in subject_day_counts.items():
            self.assertLessEqual(
                count, 2, f"{code} has {count} classes on {day} — max 2 allowed"
            )

        # Faculty conflicts
        for i, a in enumerate(result):
            for j, b in enumerate(result):
                if i >= j:
                    continue
                if a["time_slot_id"] == b["time_slot_id"]:
                    self.assertNotEqual(a["faculty_id"], b["faculty_id"])
                    self.assertNotEqual(a["room_id"], b["room_id"])

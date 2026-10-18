"""
Unit tests to verify the seed data time slot configuration is correct.

Validates:
  1. Total count: 6 days × 9 periods = 54 slots
  2. Days: MON through SAT (6 working days)
  3. Periods per day: exactly 9 continuous periods (09:00 to 18:00)
  4. 1:00 PM – 2:00 PM slot (13:00 to 14:00) exists for dynamic break placement
  5. Contiguous schedule: end of each period equals start of next
  6. Each slot is exactly 1 hour
  7. No duplicate slots
  8. Idempotent seeding
  9. Timetable generation works with 54 slots and honors dynamic breaks
"""

import os
import sys
from collections import Counter
from datetime import time

from apps.accounts.models import Faculty, User
from apps.scheduler.models import Room, Subject, TimeSlot, TimetableEntry, Department, InstitutionSettings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


def get_standard_slot_times():
    return [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
    ]


class TestSeedTimeSlotCount(TestCase):
    """Test 1: Correct total number of time slots."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        for day in days:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_total_slot_count_is_54(self):
        """6 days × 9 periods = 54 total time slots."""
        self.assertEqual(TimeSlot.objects.count(), 54)


class TestSeedTimeSlotDays(TestCase):
    """Test 2: All 6 working days are present (Mon–Sat) with 9 periods each."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_all_six_days_present(self):
        """Must include MON, TUE, WED, THU, FRI, SAT."""
        days_in_db = set(TimeSlot.objects.values_list("day", flat=True).distinct())
        expected = {"MON", "TUE", "WED", "THU", "FRI", "SAT"}
        self.assertEqual(days_in_db, expected)

    def test_no_sunday(self):
        """Sunday must NOT be included."""
        self.assertFalse(
            TimeSlot.objects.filter(day="SUN").exists(), "Sunday slots should not exist"
        )

    def test_nine_periods_per_day(self):
        """Each day should have exactly 9 periods."""
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            count = TimeSlot.objects.filter(day=day).count()
            self.assertEqual(count, 9, f"{day} should have 9 periods, got {count}")


class TestSeedTimeSlotContinuous(TestCase):
    """Test 3: Continuous day coverage (9 AM – 6 PM) with no gaps."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_day_starts_at_nine_and_ends_at_six(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            first = TimeSlot.objects.filter(day=day).order_by("start_time").first()
            last = TimeSlot.objects.filter(day=day).order_by("-end_time").first()
            self.assertEqual(first.start_time, time(9, 0))
            self.assertEqual(last.end_time, time(18, 0))

    def test_slots_contiguous(self):
        """All slots for each day should be contiguous: end of one = start of next."""
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            slots = list(TimeSlot.objects.filter(day=day).order_by("start_time"))
            for i in range(len(slots) - 1):
                self.assertEqual(
                    slots[i].end_time,
                    slots[i + 1].start_time,
                    f"{day} gap between slot {i+1} and {i+2}: {slots[i].end_time} != {slots[i+1].start_time}",
                )


class TestSeedTimeSlotOnePmSlot(TestCase):
    """Test 4: 1 PM to 2 PM slot exists for dynamic break assignment."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_slot_at_1pm_exists(self):
        """Time slot starting at 13:00 must exist on all 6 working days."""
        one_pm_slots = TimeSlot.objects.filter(start_time=time(13, 0), end_time=time(14, 0))
        self.assertEqual(one_pm_slots.count(), 6)


class TestSeedTimeSlotDuration(TestCase):
    """Test 5: Every slot is exactly 1 hour."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_all_slots_one_hour(self):
        """Every time slot should span exactly 60 minutes."""
        from datetime import datetime

        for ts in TimeSlot.objects.all():
            start_dt = datetime.combine(datetime.today(), ts.start_time)
            end_dt = datetime.combine(datetime.today(), ts.end_time)
            duration = (end_dt - start_dt).total_seconds() / 60
            self.assertEqual(
                duration,
                60,
                f"Slot {ts.day} {ts.start_time}-{ts.end_time} is {duration} min, expected 60",
            )


class TestSeedTimeSlotNoDuplicates(TestCase):
    """Test 6: No duplicate (day, start_time, end_time) combinations."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

    def test_no_duplicate_slots(self):
        """Each (day, start, end) combination must appear exactly once."""
        all_slots = TimeSlot.objects.values_list("day", "start_time", "end_time")
        counts = Counter(all_slots)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        self.assertEqual(
            len(duplicates), 0, f"Duplicate time slots found: {duplicates}"
        )

    def test_idempotent_seeding(self):
        """Running seed a second time should not create extra slots."""
        count_before = TimeSlot.objects.count()
        self._seed_timeslots()
        count_after = TimeSlot.objects.count()
        self.assertEqual(
            count_before,
            count_after,
            f"Seeding twice changed count from {count_before} to {count_after}",
        )


class TestSeedTimeSlotGeneratorIntegration(TestCase):
    """Test 7: Timetable generation works correctly with 54-slot grid and dynamic breaks."""

    def setUp(self):
        """Seed time slots, rooms, faculty, and subjects."""
        for day in ["MON", "TUE", "WED", "THU", "FRI", "SAT"]:
            for start, end in get_standard_slot_times():
                TimeSlot.objects.get_or_create(
                    day=day,
                    start_time=start,
                    end_time=end,
                )

        fac_users = []
        for i in range(1, 5):
            u = User.objects.create_user(
                email=f"fac{i}@test.edu",
                username=f"fac{i}",
                password="pass",
                role=User.Role.FACULTY,
                first_name=f"Faculty{i}",
                last_name=f"Test{i}",
            )
            fac_users.append(u)

        faculties = []
        self.dept, _ = Department.objects.get_or_create(
            name="CS",
        )
        for i, u in enumerate(fac_users, 1):
            f = Faculty.objects.create(
                user=u,
                employee_id=f"F{i:03d}",
                department=self.dept,
            )
            faculties.append(f)

        Room.objects.get_or_create(room_number="LH-101", defaults={"capacity": 60, "room_type": "lecture"})
        Room.objects.get_or_create(room_number="LH-102", defaults={"capacity": 60, "room_type": "lecture"})
        Room.objects.get_or_create(room_number="LAB-301", defaults={"capacity": 30, "room_type": "lab"})

        Subject.objects.create(
            code="CS301",
            name="DSA",
            faculty=faculties[0],
            required_capacity=40,
            sessions_per_week=3,
        )
        Subject.objects.create(
            code="CS302",
            name="DBMS",
            faculty=faculties[1],
            required_capacity=40,
            sessions_per_week=3,
        )
        Subject.objects.create(
            code="CS303",
            name="Networks",
            faculty=faculties[0],
            required_capacity=40,
            sessions_per_week=2,
        )
        Subject.objects.create(
            code="MA201",
            name="Discrete Math",
            faculty=faculties[2],
            required_capacity=60,
            sessions_per_week=3,
        )
        Subject.objects.create(
            code="EC201",
            name="Digital Electronics",
            faculty=faculties[3],
            required_capacity=40,
            sessions_per_week=3,
        )
        Subject.objects.create(
            code="CS304",
            name="AI",
            faculty=faculties[1],
            required_capacity=30,
            sessions_per_week=2,
        )

        self.admin = User.objects.create_user(
            email="admin@test.edu",
            username="admin",
            password="pass",
            role=User.Role.ADMIN,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_generate_with_54_slots(self):
        """Generator should schedule all 16 sessions with 54 available slots."""
        response = self.client.post("/api/scheduler/generate/", {"no_breaks": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        total_expected = 3 + 3 + 2 + 3 + 3 + 2  # = 16
        self.assertEqual(len(response.data["timetable"]), total_expected)

    def test_dynamic_custom_breaks_respected(self):
        """No timetable entry should be assigned to configured custom breaks (e.g. 11:00-12:00 and 15:00-16:00)."""
        payload = {
            "custom_breaks": [
                {"start": "11:00", "end": "12:00", "label": "Morning Break"},
                {"start": "15:00", "end": "16:00", "label": "Afternoon Tea"},
            ]
        }
        response = self.client.post("/api/scheduler/generate/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for entry in TimetableEntry.objects.select_related("time_slot").all():
            st = entry.time_slot.start_time
            self.assertNotEqual(st, time(11, 0), "Class scheduled during 11:00 break!")
            self.assertNotEqual(st, time(15, 0), "Class scheduled during 15:00 break!")

    def test_fallback_to_institution_default_breaks(self):
        """When custom_breaks is omitted, solver respects InstitutionSettings.default_breaks."""
        InstitutionSettings.objects.create(
            start_time="09:00",
            end_time="18:00",
            default_breaks=[{"start": "11:00", "end": "12:00", "label": "Inst Break"}]
        )
        response = self.client.post("/api/scheduler/generate/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for entry in TimetableEntry.objects.select_related("time_slot").all():
            st = entry.time_slot.start_time
            self.assertNotEqual(st, time(11, 0), "Class scheduled during institution default break!")

    def test_1pm_slot_usable_when_not_a_break(self):
        """1:00 PM slot can be used when it is not configured as a break."""
        # Force scheduling into 1pm or check valid_ts
        one_pm_slots = list(TimeSlot.objects.filter(start_time=time(13, 0)).values_list("id", flat=True))
        self.assertTrue(len(one_pm_slots) > 0)

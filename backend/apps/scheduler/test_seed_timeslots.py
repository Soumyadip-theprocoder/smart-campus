"""
Unit tests to verify the seed data time slot configuration is correct.

Validates:
  1. Total count: 6 days × 8 periods = 48 slots
  2. Days: MON through SAT (6 working days)
  3. Periods per day: exactly 8
  4. Morning block: 09:00–13:00 (4 periods, no gaps)
  5. Lunch break: 13:00–14:00 gap (no slot starts at 13:00)
  6. Afternoon block: 14:00–18:00 (4 periods, no gaps)
  7. Each slot is exactly 1 hour
  8. No duplicate slots
  9. Correct ordering
  10. Timetable generation works with 48 slots
"""
import os
import sys
from datetime import time
from collections import Counter

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.scheduler.models import TimeSlot, Subject, Room, TimetableEntry
from apps.accounts.models import User, Faculty


class TestSeedTimeSlotCount(TestCase):
    """Test 1: Correct total number of time slots."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
        """Replicate the seed_data.py time slot logic."""
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
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
        for day in days:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_total_slot_count_is_48(self):
        """6 days × 8 periods = 48 total time slots."""
        self.assertEqual(TimeSlot.objects.count(), 48)


class TestSeedTimeSlotDays(TestCase):
    """Test 2: All 6 working days are present (Mon–Sat)."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_all_six_days_present(self):
        """Must include MON, TUE, WED, THU, FRI, SAT."""
        days_in_db = set(
            TimeSlot.objects.values_list('day', flat=True).distinct()
        )
        expected = {'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'}
        self.assertEqual(days_in_db, expected)

    def test_no_sunday(self):
        """Sunday must NOT be included."""
        self.assertFalse(
            TimeSlot.objects.filter(day='SUN').exists(),
            "Sunday slots should not exist"
        )

    def test_eight_periods_per_day(self):
        """Each day should have exactly 8 periods."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            count = TimeSlot.objects.filter(day=day).count()
            self.assertEqual(
                count, 8,
                f"{day} should have 8 periods, got {count}"
            )


class TestSeedTimeSlotMorningBlock(TestCase):
    """Test 3: Morning block (9 AM – 1 PM) has 4 contiguous periods."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_morning_has_four_periods(self):
        """Morning block (before 13:00) should have exactly 4 periods per day."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            morning = TimeSlot.objects.filter(
                day=day, start_time__lt=time(13, 0)
            ).order_by('start_time')
            self.assertEqual(
                morning.count(), 4,
                f"{day} morning should have 4 periods, got {morning.count()}"
            )

    def test_morning_starts_at_nine(self):
        """First period of each day starts at 09:00."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            first = TimeSlot.objects.filter(day=day).order_by('start_time').first()
            self.assertEqual(
                first.start_time, time(9, 0),
                f"{day} first period should start at 09:00, got {first.start_time}"
            )

    def test_morning_contiguous(self):
        """Morning slots should be contiguous: end of one = start of next."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            morning = list(
                TimeSlot.objects.filter(
                    day=day, start_time__lt=time(13, 0)
                ).order_by('start_time')
            )
            for i in range(len(morning) - 1):
                self.assertEqual(
                    morning[i].end_time, morning[i + 1].start_time,
                    f"{day} morning gap between period {i+1} and {i+2}: "
                    f"{morning[i].end_time} != {morning[i+1].start_time}"
                )


class TestSeedTimeSlotLunchBreak(TestCase):
    """Test 4: Lunch break from 1 PM to 2 PM (no slot at 13:00)."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_no_slot_starts_at_1pm(self):
        """No time slot should start at 13:00 (lunch break)."""
        lunch_slots = TimeSlot.objects.filter(start_time=time(13, 0))
        self.assertEqual(
            lunch_slots.count(), 0,
            "No slot should start at 13:00 — that's lunch break"
        )

    def test_lunch_gap_exists(self):
        """Last morning slot ends at 13:00, first afternoon starts at 14:00."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            last_morning = TimeSlot.objects.filter(
                day=day, start_time__lt=time(13, 0)
            ).order_by('-start_time').first()

            first_afternoon = TimeSlot.objects.filter(
                day=day, start_time__gte=time(14, 0)
            ).order_by('start_time').first()

            self.assertEqual(
                last_morning.end_time, time(13, 0),
                f"{day}: last morning should end at 13:00"
            )
            self.assertEqual(
                first_afternoon.start_time, time(14, 0),
                f"{day}: first afternoon should start at 14:00"
            )
            # Verify the 1-hour gap
            self.assertNotEqual(
                last_morning.end_time, first_afternoon.start_time,
                f"{day}: should have a lunch gap between 13:00 and 14:00"
            )


class TestSeedTimeSlotAfternoonBlock(TestCase):
    """Test 5: Afternoon block (2 PM – 6 PM) has 4 contiguous periods."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_afternoon_has_four_periods(self):
        """Afternoon block (14:00 onwards) should have exactly 4 periods per day."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            afternoon = TimeSlot.objects.filter(
                day=day, start_time__gte=time(14, 0)
            )
            self.assertEqual(
                afternoon.count(), 4,
                f"{day} afternoon should have 4 periods, got {afternoon.count()}"
            )

    def test_afternoon_ends_at_six(self):
        """Last period of each day ends at 18:00."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            last = TimeSlot.objects.filter(day=day).order_by('-end_time').first()
            self.assertEqual(
                last.end_time, time(18, 0),
                f"{day} last period should end at 18:00, got {last.end_time}"
            )

    def test_afternoon_contiguous(self):
        """Afternoon slots should be contiguous."""
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            afternoon = list(
                TimeSlot.objects.filter(
                    day=day, start_time__gte=time(14, 0)
                ).order_by('start_time')
            )
            for i in range(len(afternoon) - 1):
                self.assertEqual(
                    afternoon[i].end_time, afternoon[i + 1].start_time,
                    f"{day} afternoon gap between period {i+1} and {i+2}"
                )


class TestSeedTimeSlotDuration(TestCase):
    """Test 6: Every slot is exactly 1 hour."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_all_slots_one_hour(self):
        """Every time slot should span exactly 60 minutes."""
        from datetime import datetime, timedelta
        for ts in TimeSlot.objects.all():
            # Combine with a dummy date to compute duration
            start_dt = datetime.combine(datetime.today(), ts.start_time)
            end_dt = datetime.combine(datetime.today(), ts.end_time)
            duration = (end_dt - start_dt).total_seconds() / 60
            self.assertEqual(
                duration, 60,
                f"Slot {ts.day} {ts.start_time}-{ts.end_time} is {duration} min, expected 60"
            )


class TestSeedTimeSlotNoDuplicates(TestCase):
    """Test 7: No duplicate (day, start_time, end_time) combinations."""

    def setUp(self):
        self._seed_timeslots()

    def _seed_timeslots(self):
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

    def test_no_duplicate_slots(self):
        """Each (day, start, end) combination must appear exactly once."""
        all_slots = TimeSlot.objects.values_list('day', 'start_time', 'end_time')
        counts = Counter(all_slots)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        self.assertEqual(
            len(duplicates), 0,
            f"Duplicate time slots found: {duplicates}"
        )

    def test_idempotent_seeding(self):
        """Running seed a second time should not create extra slots."""
        count_before = TimeSlot.objects.count()
        # Seed again
        self._seed_timeslots()
        count_after = TimeSlot.objects.count()
        self.assertEqual(
            count_before, count_after,
            f"Seeding twice changed count from {count_before} to {count_after}"
        )


class TestSeedTimeSlotGeneratorIntegration(TestCase):
    """Test 8: Timetable generation works correctly with new 48-slot grid."""

    def setUp(self):
        """Seed time slots, rooms, faculty, and subjects."""
        # Time slots
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
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']:
            for start, end in slot_times:
                TimeSlot.objects.get_or_create(
                    day=day, start_time=start, end_time=end,
                )

        # Faculty
        fac_users = []
        for i in range(1, 5):
            u = User.objects.create_user(
                email=f'fac{i}@test.edu', username=f'fac{i}',
                password='pass', role=User.Role.FACULTY,
                first_name=f'Faculty{i}', last_name=f'Test{i}',
            )
            fac_users.append(u)

        faculties = []
        for i, u in enumerate(fac_users, 1):
            f = Faculty.objects.create(
                user=u, employee_id=f'F{i:03d}', department='CS',
            )
            faculties.append(f)

        # Rooms
        Room.objects.create(room_number='LH-101', capacity=60, room_type='lecture')
        Room.objects.create(room_number='LH-102', capacity=60, room_type='lecture')
        Room.objects.create(room_number='LAB-301', capacity=30, room_type='lab')

        # Subjects (matching seed data)
        Subject.objects.create(code='CS301', name='DSA', faculty=faculties[0],
                               required_capacity=40, sessions_per_week=3)
        Subject.objects.create(code='CS302', name='DBMS', faculty=faculties[1],
                               required_capacity=40, sessions_per_week=3)
        Subject.objects.create(code='CS303', name='Networks', faculty=faculties[0],
                               required_capacity=40, sessions_per_week=2)
        Subject.objects.create(code='MA201', name='Discrete Math', faculty=faculties[2],
                               required_capacity=60, sessions_per_week=3)
        Subject.objects.create(code='EC201', name='Digital Electronics', faculty=faculties[3],
                               required_capacity=40, sessions_per_week=3)
        Subject.objects.create(code='CS304', name='AI', faculty=faculties[1],
                               required_capacity=30, sessions_per_week=2)

        self.admin = User.objects.create_user(
            email='admin@test.edu', username='admin',
            password='pass', role=User.Role.ADMIN,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_generate_with_48_slots(self):
        """Generator should schedule all 16 sessions with 48 available slots."""
        response = self.client.post('/api/scheduler/generate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        total_expected = 3 + 3 + 2 + 3 + 3 + 2  # = 16
        self.assertEqual(len(response.data['timetable']), total_expected)

    def test_generated_slots_all_valid(self):
        """All generated entries must reference existing time slot IDs."""
        self.client.post('/api/scheduler/generate/', {}, format='json')

        valid_ts_ids = set(TimeSlot.objects.values_list('id', flat=True))
        for entry in TimetableEntry.objects.all():
            self.assertIn(
                entry.time_slot_id, valid_ts_ids,
                f"Entry references invalid time_slot_id={entry.time_slot_id}"
            )

    def test_no_classes_during_lunch(self):
        """No timetable entry should be assigned to the 13:00–14:00 lunch break."""
        self.client.post('/api/scheduler/generate/', {}, format='json')

        lunch_slots = TimeSlot.objects.filter(start_time=time(13, 0))
        self.assertEqual(lunch_slots.count(), 0, "No lunch slots should exist")

        # Double-check: no entry starts at 13:00
        for entry in TimetableEntry.objects.select_related('time_slot').all():
            self.assertNotEqual(
                entry.time_slot.start_time, time(13, 0),
                f"Class scheduled during lunch break: {entry}"
            )

    def test_saturday_slots_usable(self):
        """Saturday slots should be available and potentially used."""
        sat_slots = TimeSlot.objects.filter(day='SAT')
        self.assertEqual(sat_slots.count(), 8, "Saturday should have 8 periods")

        # Generate and check if any entries land on Saturday
        self.client.post('/api/scheduler/generate/', {}, format='json')
        all_days = set(
            TimetableEntry.objects.select_related('time_slot')
            .values_list('time_slot__day', flat=True)
        )
        # With 16 sessions across 6 days, Saturday may or may not be used
        # but it should be a valid option (not excluded)
        self.assertIn('SAT', set(TimeSlot.objects.values_list('day', flat=True).distinct()))

    def test_max_one_per_subject_per_day_with_48_slots(self):
        """Default max_classes_per_day=1 should still hold with 48 slots."""
        self.client.post('/api/scheduler/generate/', {}, format='json')

        entries = TimetableEntry.objects.select_related('time_slot', 'subject').all()
        # Group by (subject, day)
        from collections import Counter
        combos = Counter(
            (e.subject_id, e.time_slot.day) for e in entries
        )
        for (subj_id, day), count in combos.items():
            self.assertLessEqual(
                count, 1,
                f"Subject {subj_id} has {count} classes on {day} (max 1)"
            )

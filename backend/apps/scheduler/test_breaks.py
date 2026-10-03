"""
Unit tests for break helpers (continuous + discrete breaks, legacy strings, slot filtering)
and the serializer validation. These do not need a database.
"""

from datetime import time

from django.test import SimpleTestCase

from apps.scheduler.breaks import normalize_breaks, slot_overlaps_break, validate_breaks
from apps.scheduler.serializers import InstitutionSettingsSerializer


class TestNormalizeBreaks(SimpleTestCase):
    def test_legacy_string_is_one_hour(self):
        self.assertEqual(
            normalize_breaks(["13:00"]), [{"start": "13:00", "end": "14:00", "label": ""}]
        )

    def test_discrete_breaks_stay_separate(self):
        out = normalize_breaks(["10:00", {"start": "15:00", "end": "16:00", "label": "Tea"}])
        self.assertEqual([(b["start"], b["end"]) for b in out], [("10:00", "11:00"), ("15:00", "16:00")])
        self.assertEqual(out[1]["label"], "Tea")

    def test_continuous_range_and_overlap_merge(self):
        out = normalize_breaks(
            [{"start": "12:00", "end": "14:00"}, {"start": "13:00", "end": "15:00", "label": "Lunch"}]
        )
        self.assertEqual(out, [{"start": "12:00", "end": "15:00", "label": "Lunch"}])

    def test_invalid_entries_ignored(self):
        self.assertEqual(normalize_breaks(["abc", {"start": "15:00", "end": "14:00"}, None]), [])
        self.assertEqual(normalize_breaks(None), [])


class TestSlotOverlap(SimpleTestCase):
    breaks = [{"start": "12:00", "end": "15:00"}, {"start": "10:00", "end": "11:00"}]

    def test_inside_continuous_break(self):
        self.assertTrue(slot_overlaps_break(time(13, 0), time(14, 0), self.breaks))
        self.assertTrue(slot_overlaps_break("14:00:00", "15:00:00", self.breaks))

    def test_between_discrete_breaks_is_allowed(self):
        self.assertFalse(slot_overlaps_break(time(11, 0), time(12, 0), self.breaks))
        self.assertFalse(slot_overlaps_break(time(15, 0), time(16, 0), self.breaks))

    def test_discrete_single_hour(self):
        self.assertTrue(slot_overlaps_break(time(10, 0), time(11, 0), self.breaks))


class TestValidation(SimpleTestCase):
    def test_validate_breaks_rejects_garbage(self):
        with self.assertRaises(ValueError):
            validate_breaks(["not-a-time"])
        with self.assertRaises(ValueError):
            validate_breaks("13:00")

    def test_serializer_normalizes_legacy_and_ranges(self):
        s = InstitutionSettingsSerializer(
            data={"default_breaks": ["13:00", {"start": "15:00", "end": "17:00", "label": "Free"}]},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(
            s.validated_data["default_breaks"],
            [
                {"start": "13:00", "end": "14:00", "label": ""},
                {"start": "15:00", "end": "17:00", "label": "Free"},
            ],
        )

    def test_serializer_rejects_invalid(self):
        s = InstitutionSettingsSerializer(data={"default_breaks": ["nope"]}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("default_breaks", s.errors)

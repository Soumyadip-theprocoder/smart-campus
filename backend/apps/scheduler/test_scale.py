"""
Scale tests for the OR-Tools CP-SAT Timetable Solver.
Verifies performance and correctness for large datasets (e.g., 500+ sessions).
"""

import time
from django.test import TestCase

from apps.scheduler.ortools_adapter import ORToolsSolverAdapter
from apps.scheduler.solver_interface import SolverInput


class ORToolsSolverScaleTests(TestCase):
    """Scale tests for the ORToolsSolverAdapter."""

    def _make_subjects(self, num_subjects):
        """Creates an array of subjects, evenly distributed among 50 faculties."""
        subjects = []
        for i in range(1, num_subjects + 1):
            subjects.append({
                "id": i,
                "code": f"SUBJ{i}",
                "name": f"Subject {i}",
                "faculty_id": (i % 50) + 1,  # 50 unique faculties
                "required_capacity": 30 + (i % 30),  # random capacities between 30 and 59
                "sessions_per_week": 1,
            })
        return subjects

    def _make_rooms(self, num_rooms):
        """Creates an array of rooms with varying capacities and buildings."""
        rooms = []
        for i in range(1, num_rooms + 1):
            rooms.append({
                "id": i,
                "room_number": f"ROOM{i}",
                "capacity": 60 + (i % 40),  # Rooms have at least 60 capacity to fit all subjects safely
                "room_type": "lecture",
                "building": f"Bldg{(i % 5) + 1}",  # 5 buildings
            })
        return rooms

    def _make_slots(self, num_slots_per_day, days):
        """Creates timeslots across the given days."""
        slots = []
        slot_id = 1
        for day in days:
            for i in range(num_slots_per_day):
                slots.append({
                    "id": slot_id,
                    "day": day,
                    "start_time": f"{8 + i:02d}:00",
                    "end_time": f"{9 + i:02d}:00",
                })
                slot_id += 1
        return slots

    def test_scale_500_sessions(self):
        """
        Test the solver's ability to schedule 500 individual sessions
        across 20 rooms and 48 time slots (6 days * 8 slots).
        Total possible placements = 20 * 48 = 960 (sufficient space).
        """
        num_subjects = 500
        num_rooms = 20
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
        slots_per_day = 8

        subjects = self._make_subjects(num_subjects)
        rooms = self._make_rooms(num_rooms)
        slots = self._make_slots(slots_per_day, days)

        # Basic constraints
        solver_input = SolverInput(
            subjects=subjects,
            rooms=rooms,
            time_slots=slots,
            max_classes_per_day=2,
            avoid_back_to_back=True,
            balance_faculty_workload=True,
        )

        adapter = ORToolsSolverAdapter(solver_input)
        
        start_time = time.time()
        result = adapter.solve()
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        self.assertTrue(result.success, f"Failed to solve 500-session scale test: {result.error}")
        self.assertEqual(len(result.timetable), 500, "Should have scheduled exactly 500 sessions")
        
        print(f"\\n[SCALE TEST] 500 sessions scheduled in {elapsed:.2f} seconds.")
        # Ensure it solves reasonably fast (e.g. under 10 seconds for 500 variables)
        self.assertLess(elapsed, 15.0, "Solver took too long for 500 sessions")



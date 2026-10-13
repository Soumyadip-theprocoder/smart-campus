import os
import django
import sys
import time

# Setup Django
sys.path.append(r"d:\Code Workspaces\smart-campus\smart-campus\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scheduler.ortools_adapter import ORToolsSolverAdapter
from apps.scheduler.solver_interface import SolverInput

def test_scale():
    print("Preparing 500-session constraint layout...")
    subjects = []
    for i in range(1, 501):
        subjects.append({
            "id": i,
            "code": f"SUBJ{i}",
            "faculty_id": (i % 50) + 1,
            "required_capacity": 40,
            "sessions_per_week": 1,
        })
        
    rooms = []
    for i in range(1, 25):
        rooms.append({
            "id": i,
            "room_number": f"ROOM{i}",
            "capacity": 60,
            "building": "Bldg1",
        })
        
    slots = []
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]
    sid = 1
    for d in days:
        for i in range(8):
            slots.append({
                "id": sid,
                "day": d,
                "start_time": f"{8 + i:02d}:00",
                "end_time": f"{9 + i:02d}:00",
            })
            sid += 1

    solver_input = SolverInput(
        subjects=subjects,
        rooms=rooms,
        time_slots=slots,
        max_classes_per_day=2,
        avoid_back_to_back=True,
        balance_faculty_workload=True,
    )

    print("Executing CP-SAT solver...")
    start = time.time()
    adapter = ORToolsSolverAdapter(solver_input)
    result = adapter.solve()
    end = time.time()

    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error: {result.error}")
    else:
        print(f"Scheduled classes: {len(result.timetable)}")
    print(f"Time taken: {end - start:.2f} seconds")

if __name__ == "__main__":
    test_scale()

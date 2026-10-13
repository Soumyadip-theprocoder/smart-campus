"""
Solver-Agnostic Interface for Timetable Generation.

Defines the abstract contract that any scheduling backend must implement.
This enables swapping between OR-Tools, custom backtracking, or any future
solver without changing the calling code in tasks.py.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SolverInput:
    """All data needed by the solver, serialized as plain Python structures."""

    subjects: list[dict]
    """Each dict has: id, code, name, faculty_id, required_capacity,
    sessions_per_week, elective_group_id (opt), resource_ids (opt)."""

    rooms: list[dict]
    """Each dict has: id, room_number, capacity, room_type (opt), building (opt)."""

    time_slots: list[dict]
    """Each dict has: id, day, start_time, end_time."""

    resources: list[dict] = field(default_factory=list)
    """Each dict has: id, name, quantity."""

    locked_entries: list[dict] = field(default_factory=list)
    """Each dict has: subject_id, room_id, time_slot_id."""

    excluded_slots: dict[int, list[int]] = field(default_factory=dict)
    """Maps subject_id -> list of forbidden time_slot_ids."""

    preferred_room_types: dict[int, str] = field(default_factory=dict)
    """Maps subject_id -> preferred room_type string."""

    # Configurable constraints
    avoid_back_to_back: bool = False
    max_classes_per_day: int = 1
    balance_faculty_workload: bool = False


@dataclass
class SolverResult:
    """Standardized output from any solver implementation."""

    success: bool
    timetable: list[dict] = field(default_factory=list)
    """Each dict has: subject_id, subject_code, faculty_id,
    room_id, room_number, time_slot_id, day, start_time, end_time."""

    error: str = ""


class TimetableSolverInterface(ABC):
    """Abstract base class for timetable solvers.

    Implementations must accept a SolverInput and produce a SolverResult.
    The optional `previous_assignment` parameter enables rescheduling
    with minimal disruption.
    """

    @abstractmethod
    def __init__(self, solver_input: SolverInput):
        """Initialize the solver with structured input data."""
        ...

    @abstractmethod
    def solve(self, previous_assignment: Optional[dict] = None) -> SolverResult:
        """Generate a timetable.

        Args:
            previous_assignment: Optional dict mapping
                (subject_id, session_index) -> (time_slot_id, room_id).
                When provided, the solver should try to minimize changes
                from this assignment.

        Returns:
            A SolverResult with success status and the timetable entries.
        """
        ...

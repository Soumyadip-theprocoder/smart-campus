"""
Constraint Satisfaction Problem (CSP) Solver for Timetable Generation.

Uses backtracking search with:
- Minimum Remaining Values (MRV) heuristic for variable ordering
- Forward checking for constraint propagation
- Arc consistency for domain pruning

Constraints:
  1. No faculty member teaches two classes at the same time slot
  2. No room hosts two classes at the same time slot
  3. Room capacity >= Subject's required capacity
"""
from typing import Optional


class ScheduleCSP:
    """
    CSP-based timetable scheduler.

    Variables:  Each (subject, session_index) pair to be scheduled
    Domains:    Possible (time_slot_id, room_id) assignments
    Constraints:
      - Faculty conflict: same faculty cannot be in two time slots
      - Room conflict: same room cannot host two sessions at same time
      - Capacity: room capacity must be >= subject's required capacity
    """

    def __init__(self, subjects: list, rooms: list, time_slots: list):
        """
        Args:
            subjects: list of dicts with keys:
                id, code, name, faculty_id, required_capacity, sessions_per_week
            rooms: list of dicts with keys:
                id, room_number, capacity
            time_slots: list of dicts with keys:
                id, day, start_time, end_time
        """
        self.subjects = subjects
        self.rooms = rooms
        self.time_slots = time_slots

        # Build variables: one per session per subject
        self.variables = []
        for subj in subjects:
            for session_idx in range(subj['sessions_per_week']):
                self.variables.append({
                    'subject_id': subj['id'],
                    'subject_code': subj['code'],
                    'faculty_id': subj['faculty_id'],
                    'required_capacity': subj['required_capacity'],
                    'session_index': session_idx,
                })

        # Build domains: all valid (time_slot_id, room_id) pairs
        # pre-filtered by capacity
        self.domains = {}
        for i, var in enumerate(self.variables):
            valid_rooms = [
                r for r in rooms
                if r['capacity'] >= var['required_capacity']
            ]
            self.domains[i] = [
                (ts['id'], room['id'])
                for ts in time_slots
                for room in valid_rooms
            ]

        # Assignment: variable_index -> (time_slot_id, room_id)
        self.assignment = {}

    def is_consistent(self, var_idx: int, value: tuple) -> bool:
        """Check if assigning value to var_idx is consistent with current assignment."""
        ts_id, room_id = value
        var = self.variables[var_idx]

        for assigned_idx, assigned_val in self.assignment.items():
            assigned_ts, assigned_room = assigned_val
            assigned_var = self.variables[assigned_idx]

            # Same time slot?
            if assigned_ts == ts_id:
                # Constraint 1: Faculty conflict
                if assigned_var['faculty_id'] == var['faculty_id']:
                    return False

                # Constraint 2: Room conflict
                if assigned_room == room_id:
                    return False

            # Same subject shouldn't be on the same day twice (soft constraint)
            if assigned_var['subject_id'] == var['subject_id']:
                # Look up day for both time slots
                ts_day = self._get_timeslot_day(ts_id)
                assigned_day = self._get_timeslot_day(assigned_ts)
                if ts_day == assigned_day:
                    return False

        return True

    def _get_timeslot_day(self, ts_id: int) -> str:
        """Get the day of a time slot by its ID."""
        for ts in self.time_slots:
            if ts['id'] == ts_id:
                return ts['day']
        return ''

    def select_unassigned_variable(self) -> Optional[int]:
        """
        Select the next unassigned variable using MRV heuristic
        (variable with fewest remaining legal values).
        """
        unassigned = [
            i for i in range(len(self.variables))
            if i not in self.assignment
        ]
        if not unassigned:
            return None

        return min(
            unassigned,
            key=lambda i: sum(
                1 for v in self.domains[i]
                if self.is_consistent(i, v)
            ),
        )

    def forward_check(self, var_idx: int, value: tuple) -> dict:
        """
        Perform forward checking: prune domains of unassigned variables.
        Returns the pruned values so they can be restored on backtrack.
        """
        pruned = {}
        ts_id, room_id = value
        var = self.variables[var_idx]

        for other_idx in range(len(self.variables)):
            if other_idx in self.assignment or other_idx == var_idx:
                continue

            other_var = self.variables[other_idx]
            new_domain = []
            removed = []

            for other_val in self.domains[other_idx]:
                other_ts, other_room = other_val

                if other_ts == ts_id:
                    # Faculty conflict
                    if other_var['faculty_id'] == var['faculty_id']:
                        removed.append(other_val)
                        continue
                    # Room conflict
                    if other_room == room_id:
                        removed.append(other_val)
                        continue

                new_domain.append(other_val)

            if removed:
                pruned[other_idx] = removed
                self.domains[other_idx] = new_domain

            # If domain is empty, this assignment leads to failure
            if not new_domain:
                # Restore pruned values before returning failure
                for idx, vals in pruned.items():
                    self.domains[idx].extend(vals)
                return None  # Signal failure

        return pruned

    def restore_domains(self, pruned: dict):
        """Restore pruned domain values after backtracking."""
        for idx, vals in pruned.items():
            self.domains[idx].extend(vals)

    def solve(self) -> Optional[dict]:
        """
        Solve the CSP using backtracking with forward checking.
        Returns assignment dict or None if no solution exists.
        """
        return self._backtrack()

    def _backtrack(self) -> Optional[dict]:
        """Recursive backtracking search."""
        # All variables assigned — solution found
        if len(self.assignment) == len(self.variables):
            return dict(self.assignment)

        var_idx = self.select_unassigned_variable()
        if var_idx is None:
            return None

        # Try each value in the domain
        for value in list(self.domains[var_idx]):
            if self.is_consistent(var_idx, value):
                # Assign
                self.assignment[var_idx] = value

                # Forward check
                pruned = self.forward_check(var_idx, value)
                if pruned is not None:
                    result = self._backtrack()
                    if result is not None:
                        return result
                    self.restore_domains(pruned)

                # Backtrack
                del self.assignment[var_idx]

        return None

    def get_timetable(self) -> list:
        """
        Solve and return a human-readable timetable.
        Returns list of dicts with subject, room, and time_slot info.
        """
        solution = self.solve()
        if solution is None:
            return []

        timetable = []
        for var_idx, (ts_id, room_id) in solution.items():
            var = self.variables[var_idx]

            # Find the time slot and room details
            ts_info = next(ts for ts in self.time_slots if ts['id'] == ts_id)
            room_info = next(r for r in self.rooms if r['id'] == room_id)

            timetable.append({
                'subject_id': var['subject_id'],
                'subject_code': var['subject_code'],
                'faculty_id': var['faculty_id'],
                'room_id': room_id,
                'room_number': room_info['room_number'],
                'time_slot_id': ts_id,
                'day': ts_info['day'],
                'start_time': str(ts_info['start_time']),
                'end_time': str(ts_info['end_time']),
            })

        # Sort by day and start time
        day_order = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5}
        timetable.sort(key=lambda x: (day_order.get(x['day'], 99), x['start_time']))

        return timetable

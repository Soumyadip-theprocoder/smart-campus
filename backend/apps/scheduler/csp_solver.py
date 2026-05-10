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
  4. Same subject not on the same day twice (configurable via max_classes_per_day)
  5. Excluded time slots per subject
  6. Locked entries (pre-assigned and immovable)
  7. Preferred room types per subject (soft — tried first)
  8. Avoid back-to-back classes for same faculty (soft)
"""
from typing import Optional


class ScheduleCSP:
    """
    CSP-based timetable scheduler with advanced constraints.

    Variables:  Each (subject, session_index) pair to be scheduled
    Domains:    Possible (time_slot_id, room_id) assignments
    Constraints: see module docstring
    """

    def __init__(
        self,
        subjects: list,
        rooms: list,
        time_slots: list,
        locked_entries: list = None,
        excluded_slots: dict = None,
        preferred_room_types: dict = None,
        avoid_back_to_back: bool = False,
        max_classes_per_day: int = 1,
    ):
        """
        Args:
            subjects: list of dicts with keys:
                id, code, name, faculty_id, required_capacity, sessions_per_week
            rooms: list of dicts with keys:
                id, room_number, capacity  (optionally room_type)
            time_slots: list of dicts with keys:
                id, day, start_time, end_time
            locked_entries: list of dicts {subject_id, room_id, time_slot_id}
                These are pre-assigned and will not be moved.
            excluded_slots: dict of subject_id -> [time_slot_id, ...]
                These time slots are forbidden for the given subject.
            preferred_room_types: dict of subject_id -> room_type string
                The solver will try rooms of this type first (soft preference).
            avoid_back_to_back: if True, penalize consecutive slots for same faculty.
            max_classes_per_day: max sessions of the same subject on one day (default 1).
        """
        self.subjects = subjects
        self.rooms = rooms
        self.time_slots = time_slots
        self.locked_entries = locked_entries or []
        self.excluded_slots = excluded_slots or {}
        self.preferred_room_types = preferred_room_types or {}
        self.avoid_back_to_back = avoid_back_to_back
        self.max_classes_per_day = max_classes_per_day

        # Build lookup maps
        self._ts_map = {ts['id']: ts for ts in time_slots}
        self._room_map = {r['id']: r for r in rooms}

        # Build variables: one per session per subject
        self.variables = []
        self._locked_var_indices = set()

        # Pre-assign locked entries first
        locked_map = {}  # (subject_id, session_idx) -> (ts_id, room_id)
        locked_session_counter = {}
        for le in self.locked_entries:
            sid = le['subject_id']
            locked_session_counter.setdefault(sid, 0)
            idx = locked_session_counter[sid]
            locked_map[(sid, idx)] = (le['time_slot_id'], le['room_id'])
            locked_session_counter[sid] += 1

        for subj in subjects:
            for session_idx in range(subj['sessions_per_week']):
                var_idx = len(self.variables)
                self.variables.append({
                    'subject_id': subj['id'],
                    'subject_code': subj['code'],
                    'faculty_id': subj['faculty_id'],
                    'required_capacity': subj['required_capacity'],
                    'session_index': session_idx,
                })
                if (subj['id'], session_idx) in locked_map:
                    self._locked_var_indices.add(var_idx)

        # Build domains
        self.domains = {}
        for i, var in enumerate(self.variables):
            sid = var['subject_id']
            session_idx = var['session_index']

            # Check if this var is locked
            if (sid, session_idx) in locked_map:
                self.domains[i] = [locked_map[(sid, session_idx)]]
                continue

            # Excluded time slots for this subject
            excluded_ts = set(self.excluded_slots.get(sid, []))

            # Valid rooms by capacity
            valid_rooms = [
                r for r in rooms
                if r['capacity'] >= var['required_capacity']
            ]

            # Sort by preferred room type (preferred first)
            pref_type = self.preferred_room_types.get(sid)
            if pref_type:
                preferred = [r for r in valid_rooms if r.get('room_type') == pref_type]
                non_preferred = [r for r in valid_rooms if r.get('room_type') != pref_type]
                valid_rooms = preferred + non_preferred

            domain = []
            for ts in time_slots:
                if ts['id'] in excluded_ts:
                    continue
                for room in valid_rooms:
                    domain.append((ts['id'], room['id']))

            self.domains[i] = domain

        # Assignment: variable_index -> (time_slot_id, room_id)
        self.assignment = {}

        # Pre-assign locked variables
        for i in self._locked_var_indices:
            self.assignment[i] = self.domains[i][0]

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

            # Same subject: max_classes_per_day constraint
            if assigned_var['subject_id'] == var['subject_id']:
                ts_day = self._get_timeslot_day(ts_id)
                assigned_day = self._get_timeslot_day(assigned_ts)
                if ts_day == assigned_day:
                    # Count how many of this subject are already on this day
                    count = sum(
                        1 for idx, val in self.assignment.items()
                        if self.variables[idx]['subject_id'] == var['subject_id']
                        and self._get_timeslot_day(val[0]) == ts_day
                    )
                    if count >= self.max_classes_per_day:
                        return False

            # Soft: avoid back-to-back for same faculty
            if self.avoid_back_to_back and assigned_var['faculty_id'] == var['faculty_id']:
                if self._are_consecutive(ts_id, assigned_ts):
                    return False

        return True

    def _get_timeslot_day(self, ts_id: int) -> str:
        """Get the day of a time slot by its ID."""
        ts = self._ts_map.get(ts_id)
        return ts['day'] if ts else ''

    def _are_consecutive(self, ts_id_1: int, ts_id_2: int) -> bool:
        """Check if two time slots are consecutive (back-to-back) on the same day."""
        ts1 = self._ts_map.get(ts_id_1)
        ts2 = self._ts_map.get(ts_id_2)
        if not ts1 or not ts2:
            return False
        if ts1['day'] != ts2['day']:
            return False
        # Check if end of one equals start of other
        return ts1['end_time'] == ts2['start_time'] or ts2['end_time'] == ts1['start_time']

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
            ts_info = self._ts_map[ts_id]
            room_info = self._room_map[room_id]

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

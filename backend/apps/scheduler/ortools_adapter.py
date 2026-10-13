"""
Google OR-Tools CP-SAT Adapter for Timetable Generation.

Translates the scheduling problem into a Constraint Programming model
and solves it using Google's CP-SAT solver. Supports all hard and soft
constraints from the legacy backtracking solver, plus native
minimize-changes rescheduling via solver hints and an objective function.
"""

import logging
from typing import Optional

from ortools.sat.python import cp_model

from .solver_interface import SolverInput, SolverResult, TimetableSolverInterface

logger = logging.getLogger(__name__)


class ORToolsSolverAdapter(TimetableSolverInterface):
    """CP-SAT based timetable solver."""

    def __init__(self, solver_input: SolverInput):
        self.input = solver_input

        # Build lookup maps
        self._ts_map = {ts["id"]: ts for ts in solver_input.time_slots}
        self._room_map = {r["id"]: r for r in solver_input.rooms}
        self._resource_map = {r["id"]: r for r in solver_input.resources}

        # Identify days from time slots
        self._ts_by_day: dict[str, list[int]] = {}
        for ts in solver_input.time_slots:
            self._ts_by_day.setdefault(ts["day"], []).append(ts["id"])

        # Build variables list: (subject_dict, session_index)
        self._variables: list[tuple[dict, int]] = []
        locked_map: dict[tuple[int, int], tuple[int, int]] = {}
        locked_session_counter: dict[int, int] = {}
        for le in solver_input.locked_entries:
            sid = le["subject_id"]
            locked_session_counter.setdefault(sid, 0)
            idx = locked_session_counter[sid]
            locked_map[(sid, idx)] = (le["time_slot_id"], le["room_id"])
            locked_session_counter[sid] += 1

        for subj in solver_input.subjects:
            for session_idx in range(subj["sessions_per_week"]):
                self._variables.append((subj, session_idx))

        self._locked_map = locked_map

        # Pre-compute valid rooms per subject (capacity filter)
        self._valid_rooms: dict[int, list[dict]] = {}
        for subj in solver_input.subjects:
            self._valid_rooms[subj["id"]] = [
                r for r in solver_input.rooms
                if r["capacity"] >= subj["required_capacity"]
            ]

        # Pre-compute excluded ts sets
        self._excluded_ts: dict[int, set[int]] = {
            sid: set(ts_list) for sid, ts_list in solver_input.excluded_slots.items()
        }

        # Pre-compute preferred rooms
        self._preferred_rooms: dict[int, set[int]] = {}
        for sid, pref_type in solver_input.preferred_room_types.items():
            self._preferred_rooms[sid] = {
                r["id"] for r in solver_input.rooms if r.get("room_type") == pref_type
            }

        # Pre-compute consecutive slot pairs for building transit
        self._consecutive_pairs: set[tuple[int, int]] = set()
        for day_slots in self._ts_by_day.values():
            sorted_slots = sorted(day_slots, key=lambda tid: str(self._ts_map[tid]["start_time"]))
            for i in range(len(sorted_slots) - 1):
                ts1 = self._ts_map[sorted_slots[i]]
                ts2 = self._ts_map[sorted_slots[i + 1]]
                if str(ts1["end_time"]) == str(ts2["start_time"]):
                    self._consecutive_pairs.add((sorted_slots[i], sorted_slots[i + 1]))
                    self._consecutive_pairs.add((sorted_slots[i + 1], sorted_slots[i]))

    def _are_consecutive(self, ts_id_1: int, ts_id_2: int) -> bool:
        return (ts_id_1, ts_id_2) in self._consecutive_pairs

    def solve(self, previous_assignment: Optional[dict] = None) -> SolverResult:
        model = cp_model.CpModel()

        # ─── Decision Variables ─────────────────────────────────────────
        # x[v][ts_id][room_id] = 1 iff variable v is assigned to (ts, room)
        x: dict[int, dict[int, dict[int, cp_model.IntVar]]] = {}
        all_ts_ids = [ts["id"] for ts in self.input.time_slots]
        all_room_ids = [r["id"] for r in self.input.rooms]

        for v_idx, (subj, sess_idx) in enumerate(self._variables):
            sid = subj["id"]
            excluded = self._excluded_ts.get(sid, set())
            valid_room_ids = [r["id"] for r in self._valid_rooms[sid]]
            locked = self._locked_map.get((sid, sess_idx))

            x[v_idx] = {}
            for ts_id in all_ts_ids:
                if ts_id in excluded and not locked:
                    continue
                if locked and ts_id != locked[0]:
                    continue

                x[v_idx][ts_id] = {}
                for room_id in (valid_room_ids if not locked else [locked[1]]):
                    if locked and room_id != locked[1]:
                        continue
                    var_name = f"x_{v_idx}_{ts_id}_{room_id}"
                    x[v_idx][ts_id][room_id] = model.new_bool_var(var_name)

        # ─── Constraint: Exactly one assignment per variable ────────────
        for v_idx in range(len(self._variables)):
            all_options = []
            for ts_id in x.get(v_idx, {}):
                for room_id in x[v_idx][ts_id]:
                    all_options.append(x[v_idx][ts_id][room_id])
            if not all_options:
                return SolverResult(
                    success=False,
                    error=f"No valid (timeslot, room) options for variable {v_idx} "
                          f"(subject {self._variables[v_idx][0]['code']}, session {self._variables[v_idx][1]})."
                )
            model.add_exactly_one(all_options)

        # ─── Constraint: No faculty conflict (same timeslot) ────────────
        faculty_vars: dict[int, dict[int, list]] = {}  # faculty_id -> ts_id -> [boolvar list]
        for v_idx, (subj, _) in enumerate(self._variables):
            fid = subj["faculty_id"]
            if fid is None:
                continue
            faculty_vars.setdefault(fid, {})
            for ts_id in x.get(v_idx, {}):
                faculty_vars[fid].setdefault(ts_id, [])
                for room_id in x[v_idx][ts_id]:
                    faculty_vars[fid][ts_id].append(x[v_idx][ts_id][room_id])

        for fid, ts_dict in faculty_vars.items():
            for ts_id, var_list in ts_dict.items():
                if len(var_list) > 1:
                    model.add(sum(var_list) <= 1)

        # ─── Constraint: No room conflict (same timeslot) ───────────────
        room_ts_vars: dict[int, dict[int, list]] = {}  # room_id -> ts_id -> [boolvar list]
        for v_idx in range(len(self._variables)):
            for ts_id in x.get(v_idx, {}):
                for room_id in x[v_idx][ts_id]:
                    room_ts_vars.setdefault(room_id, {}).setdefault(ts_id, [])
                    room_ts_vars[room_id][ts_id].append(x[v_idx][ts_id][room_id])

        for room_id, ts_dict in room_ts_vars.items():
            for ts_id, var_list in ts_dict.items():
                if len(var_list) > 1:
                    model.add(sum(var_list) <= 1)

        # ─── Constraint: Elective group conflict ───────────────────────
        elective_vars: dict[int, dict[int, list]] = {}  # group_id -> ts_id -> [boolvar list]
        for v_idx, (subj, _) in enumerate(self._variables):
            eg_id = subj.get("elective_group_id")
            if not eg_id:
                continue
            elective_vars.setdefault(eg_id, {})
            for ts_id in x.get(v_idx, {}):
                elective_vars[eg_id].setdefault(ts_id, [])
                for room_id in x[v_idx][ts_id]:
                    elective_vars[eg_id][ts_id].append(x[v_idx][ts_id][room_id])

        for eg_id, ts_dict in elective_vars.items():
            for ts_id, var_list in ts_dict.items():
                if len(var_list) > 1:
                    model.add(sum(var_list) <= 1)

        # ─── Constraint: Max classes per day per subject ────────────────
        max_cpd = self.input.max_classes_per_day
        subject_session_vars: dict[int, list[int]] = {}  # subject_id -> [v_idx list]
        for v_idx, (subj, _) in enumerate(self._variables):
            subject_session_vars.setdefault(subj["id"], []).append(v_idx)

        for sid, v_indices in subject_session_vars.items():
            for day, day_ts_ids in self._ts_by_day.items():
                day_ts_set = set(day_ts_ids)
                day_vars = []
                for v_idx in v_indices:
                    for ts_id in x.get(v_idx, {}):
                        if ts_id in day_ts_set:
                            for room_id in x[v_idx][ts_id]:
                                day_vars.append(x[v_idx][ts_id][room_id])
                if len(day_vars) > max_cpd:
                    model.add(sum(day_vars) <= max_cpd)

        # ─── Constraint: Balance faculty workload (max 3/day) ───────────
        if self.input.balance_faculty_workload:
            faculty_day_vars: dict[int, dict[str, list]] = {}
            for v_idx, (subj, _) in enumerate(self._variables):
                fid = subj["faculty_id"]
                if fid is None:
                    continue
                faculty_day_vars.setdefault(fid, {})
                for ts_id in x.get(v_idx, {}):
                    day = self._ts_map[ts_id]["day"]
                    faculty_day_vars[fid].setdefault(day, [])
                    for room_id in x[v_idx][ts_id]:
                        faculty_day_vars[fid][day].append(x[v_idx][ts_id][room_id])

            for fid, day_dict in faculty_day_vars.items():
                for day, var_list in day_dict.items():
                    if len(var_list) > 3:
                        model.add(sum(var_list) <= 3)

        # ─── Constraint: Avoid back-to-back for same faculty ────────────
        if self.input.avoid_back_to_back:
            for fid, ts_dict in faculty_vars.items():
                ts_ids_for_fac = sorted(ts_dict.keys(), key=lambda t: (self._ts_map[t]["day"], str(self._ts_map[t]["start_time"])))
                for i in range(len(ts_ids_for_fac)):
                    for j in range(i + 1, len(ts_ids_for_fac)):
                        ts_a, ts_b = ts_ids_for_fac[i], ts_ids_for_fac[j]
                        if self._are_consecutive(ts_a, ts_b):
                            model.add(
                                sum(ts_dict[ts_a]) + sum(ts_dict[ts_b]) <= 1
                            )

        # ─── Constraint: Building transit ───────────────────────────────
        # For same faculty back-to-back, rooms must share a building
        for fid in faculty_vars:
            for v_idx_a, (subj_a, _) in enumerate(self._variables):
                if subj_a["faculty_id"] != fid:
                    continue
                for v_idx_b, (subj_b, _) in enumerate(self._variables):
                    if v_idx_b <= v_idx_a:
                        continue
                    if subj_b["faculty_id"] != fid:
                        continue
                    # For each pair of consecutive timeslots
                    for ts_a in x.get(v_idx_a, {}):
                        for ts_b in x.get(v_idx_b, {}):
                            if not self._are_consecutive(ts_a, ts_b):
                                continue
                            # For each pair of rooms in different buildings
                            for room_a in x[v_idx_a].get(ts_a, {}):
                                for room_b in x[v_idx_b].get(ts_b, {}):
                                    bldg_a = self._room_map[room_a].get("building")
                                    bldg_b = self._room_map[room_b].get("building")
                                    if bldg_a and bldg_b and bldg_a != bldg_b:
                                        model.add(
                                            x[v_idx_a][ts_a][room_a] + x[v_idx_b][ts_b][room_b] <= 1
                                        )

        # ─── Constraint: Resource pool capacity ─────────────────────────
        resource_usage: dict[int, dict[int, list]] = {}  # resource_id -> ts_id -> [boolvar]
        for v_idx, (subj, _) in enumerate(self._variables):
            res_ids = subj.get("resource_ids", [])
            for res_id in res_ids:
                resource_usage.setdefault(res_id, {})
                for ts_id in x.get(v_idx, {}):
                    resource_usage[res_id].setdefault(ts_id, [])
                    for room_id in x[v_idx][ts_id]:
                        resource_usage[res_id][ts_id].append(x[v_idx][ts_id][room_id])

        for res_id, ts_dict in resource_usage.items():
            quantity = self._resource_map.get(res_id, {}).get("quantity", 1)
            for ts_id, var_list in ts_dict.items():
                if len(var_list) > quantity:
                    model.add(sum(var_list) <= quantity)

        # ─── Objective function ─────────────────────────────────────────
        penalties = []
        PENALTY_PREF_ROOM = 1
        PENALTY_CHANGE = 10

        # Soft: prefer rooms of the requested type
        for v_idx, (subj, _) in enumerate(self._variables):
            sid = subj["id"]
            pref_rooms = self._preferred_rooms.get(sid)
            if not pref_rooms:
                continue
            for ts_id in x.get(v_idx, {}):
                for room_id in x[v_idx][ts_id]:
                    if room_id not in pref_rooms:
                        penalties.append(x[v_idx][ts_id][room_id] * PENALTY_PREF_ROOM)

        # Minimize changes from previous assignment (rescheduling)
        if previous_assignment:
            for v_idx, (subj, sess_idx) in enumerate(self._variables):
                key = (subj["id"], sess_idx)
                if key not in previous_assignment:
                    continue
                prev_ts, prev_room = previous_assignment[key]

                # Hint the solver towards original assignment
                if prev_ts in x.get(v_idx, {}) and prev_room in x[v_idx].get(prev_ts, {}):
                    model.add_hint(x[v_idx][prev_ts][prev_room], 1)

                # Penalize any assignment that differs from the original
                for ts_id in x.get(v_idx, {}):
                    for room_id in x[v_idx][ts_id]:
                        if ts_id != prev_ts or room_id != prev_room:
                            penalties.append(x[v_idx][ts_id][room_id] * PENALTY_CHANGE)

        if penalties:
            model.minimize(sum(penalties))

        # ─── Solve ──────────────────────────────────────────────────────
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 120
        solver.parameters.num_workers = 4

        status = solver.solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_name = solver.status_name(status)
            return SolverResult(
                success=False,
                error=f"CP-SAT solver failed with status: {status_name}. "
                      f"The constraints may be unsatisfiable."
            )

        # ─── Extract solution ───────────────────────────────────────────
        timetable = []
        for v_idx, (subj, sess_idx) in enumerate(self._variables):
            for ts_id in x.get(v_idx, {}):
                for room_id in x[v_idx][ts_id]:
                    if solver.value(x[v_idx][ts_id][room_id]) == 1:
                        ts_info = self._ts_map[ts_id]
                        room_info = self._room_map[room_id]
                        timetable.append({
                            "subject_id": subj["id"],
                            "subject_code": subj["code"],
                            "faculty_id": subj["faculty_id"],
                            "room_id": room_id,
                            "room_number": room_info["room_number"],
                            "time_slot_id": ts_id,
                            "day": ts_info["day"],
                            "start_time": str(ts_info["start_time"]),
                            "end_time": str(ts_info["end_time"]),
                        })
                        break  # Found the assigned value for this v_idx+ts_id
                else:
                    continue
                break  # Found the assigned value for this v_idx

        # Sort by day and start time
        day_order = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5}
        timetable.sort(key=lambda e: (day_order.get(e["day"], 99), e["start_time"]))

        logger.info(
            "CP-SAT solved: %d entries, status=%s, objective=%.0f",
            len(timetable), solver.status_name(status),
            solver.objective_value if penalties else 0
        )

        return SolverResult(success=True, timetable=timetable)

"""
Google OR-Tools CP-SAT Adapter for Timetable Generation.

Translates the scheduling problem into a Constraint Programming model
and solves it using Google's CP-SAT solver. Supports all hard and soft
constraints from the legacy backtracking solver, plus native
minimize-changes rescheduling via solver hints and an objective function.

Phase 17 additions:
  - Semester cohort non-overlap (hard)
  - Elective parallel scheduling
  - Common course merging (merge_group_id binds timeslots)
  - 2-hour consecutive lab blocks
  - Academic block affinity (soft/hard)
"""

import logging
from collections import defaultdict
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

        # Canonical interleaved ordering (by hour first, then weekday) for balanced daily distribution
        day_priority = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
        sorted_slots = sorted(
            solver_input.time_slots,
            key=lambda ts: (str(ts["start_time"]), day_priority.get(ts["day"], 99))
        )
        self._sorted_time_slots = sorted_slots

        # Identify days from time slots (preserves canonical weekday ordering)
        self._ts_by_day: dict[str, list[int]] = {}
        for ts in sorted(solver_input.time_slots, key=lambda ts: (day_priority.get(ts["day"], 99), str(ts["start_time"]))):
            self._ts_by_day.setdefault(ts["day"], []).append(ts["id"])

        # Build sorted slots per day (for consecutive lab detection)
        self._sorted_day_slots: dict[str, list[int]] = {}
        for day, slots in self._ts_by_day.items():
            self._sorted_day_slots[day] = sorted(
                slots, key=lambda tid: str(self._ts_map[tid]["start_time"])
            )

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

        # Identify occupied room slots from locked entries of other subjects
        current_sids = {s["id"] for s in solver_input.subjects}
        room_occupied_count: dict[int, int] = defaultdict(int)
        for le in solver_input.locked_entries:
            if le.get("subject_id") not in current_sids and le.get("room_id"):
                room_occupied_count[le["room_id"]] += 1

        total_ts_count = len(solver_input.time_slots)

        # Pre-compute valid rooms per subject (capacity filter + allowed rooms + occupancy balancing)
        self._valid_rooms: dict[int, list[dict]] = {}
        for subj in solver_input.subjects:
            allowed = subj.get("allowed_room_ids")
            rooms_for_subj = []
            for r in solver_input.rooms:
                if r["capacity"] < subj["required_capacity"]:
                    continue
                if allowed and r["id"] not in allowed:
                    continue
                # If room is completely booked across all timeslots, skip it unless explicitly locked
                if not allowed and total_ts_count > 0 and room_occupied_count.get(r["id"], 0) >= total_ts_count:
                    continue
                rooms_for_subj.append(r)

            # Sort by room_type match, occupancy (least occupied first), and smallest suitable capacity
            # Keep top candidates to prevent combinatorial explosion while distributing load evenly
            if len(rooms_for_subj) > 8:
                req_cap = subj["required_capacity"]
                is_lab = subj.get("is_lab")
                rooms_for_subj.sort(key=lambda r: (
                    0 if (r.get("room_type") == "lab") == is_lab else 1,
                    room_occupied_count.get(r["id"], 0),
                    r["capacity"] - req_cap
                ))
                rooms_for_subj = rooms_for_subj[:8]

            self._valid_rooms[subj["id"]] = rooms_for_subj

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
        # Also build ordered consecutive pairs per day for lab blocks
        self._consecutive_pairs_ordered: dict[str, list[tuple[int, int]]] = {}
        for day, sorted_slots in self._sorted_day_slots.items():
            pairs = []
            for i in range(len(sorted_slots) - 1):
                ts1 = self._ts_map[sorted_slots[i]]
                ts2 = self._ts_map[sorted_slots[i + 1]]
                if str(ts1["end_time"]) == str(ts2["start_time"]):
                    self._consecutive_pairs.add((sorted_slots[i], sorted_slots[i + 1]))
                    self._consecutive_pairs.add((sorted_slots[i + 1], sorted_slots[i]))
                    pairs.append((sorted_slots[i], sorted_slots[i + 1]))
            self._consecutive_pairs_ordered[day] = pairs

        # Pre-compute merge groups
        self._merge_groups: dict[str, list[dict]] = {}
        if solver_input.merge_common_courses:
            for subj in solver_input.subjects:
                mg = subj.get("merge_group_id")
                if mg:
                    self._merge_groups.setdefault(mg, []).append(subj)

        # Pre-compute cohort groupings for cohorts present in this solve
        self._cohort_subjects: dict[tuple, list[dict]] = {}
        for subj in solver_input.subjects:
            ck = subj.get("cohort_key")
            if ck:
                key = tuple(ck) if isinstance(ck, (list, tuple)) else ck
                self._cohort_subjects.setdefault(key, []).append(subj)
            else:
                sem = subj.get("semester")
                dept_ids = subj.get("department_ids", [])
                if sem and dept_ids:
                    self._cohort_subjects.setdefault((dept_ids[0], sem), []).append(subj)

    def _are_consecutive(self, ts_id_1: int, ts_id_2: int) -> bool:
        return (ts_id_1, ts_id_2) in self._consecutive_pairs

    def _get_lab_consecutive_pairs(self, subj: dict) -> list[tuple[int, int]]:
        """Return valid consecutive timeslot pairs for a lab subject."""
        allowed_room_ids = subj.get("allowed_room_ids")
        lab_rooms = [
            r for r in self._valid_rooms[subj["id"]]
            if r.get("room_type") == "lab"
        ]
        if allowed_room_ids:
            lab_rooms = [r for r in lab_rooms if r["id"] in allowed_room_ids]

        pairs = []
        for day_pairs in self._consecutive_pairs_ordered.values():
            pairs.extend(day_pairs)
        return pairs

    def solve(self, previous_assignment: Optional[dict] = None) -> SolverResult:
        model = cp_model.CpModel()
        penalties = []

        # ─── Decision Variables ─────────────────────────────────────────
        # x[v][ts_id][room_id] = 1 iff variable v is assigned to (ts, room)
        x: dict[int, dict[int, dict[int, cp_model.IntVar]]] = {}
        all_ts_ids = [ts["id"] for ts in self._sorted_time_slots]

        # Identify lab subjects and their session pairs
        lab_subjects: dict[int, bool] = {}
        for subj in self.input.subjects:
            lab_subjects[subj["id"]] = bool(
                self.input.consecutive_labs and subj.get("is_lab")
            )

        # Identify external locked reservations from prior waves
        current_sids = {s["id"] for s in self.input.subjects}
        occupied_room_slots = set()
        occupied_faculty_slots = set()
        for le in self.input.locked_entries:
            if le.get("subject_id") not in current_sids:
                occupied_room_slots.add((le["room_id"], le["time_slot_id"]))
                fid = le.get("faculty_id")
                if fid:
                    occupied_faculty_slots.add((fid, le["time_slot_id"]))

        for v_idx, (subj, sess_idx) in enumerate(self._variables):
            sid = subj["id"]
            fid = subj.get("faculty_id")
            excluded = self._excluded_ts.get(sid, set())
            valid_room_ids = [r["id"] for r in self._valid_rooms[sid]]
            locked = self._locked_map.get((sid, sess_idx))

            # For lab subjects: restrict rooms to lab type
            if lab_subjects.get(sid):
                lab_room_ids = [
                    r["id"] for r in self._valid_rooms[sid]
                    if r.get("room_type") == "lab"
                ]
                if lab_room_ids:
                    valid_room_ids = lab_room_ids

            x[v_idx] = {}
            for ts_id in all_ts_ids:
                if ts_id in excluded and not locked:
                    continue
                if locked and ts_id != locked[0]:
                    continue
                # If faculty is already occupied by a prior wave at this timeslot
                if not locked and fid and (fid, ts_id) in occupied_faculty_slots:
                    continue

                x[v_idx][ts_id] = {}
                for room_id in (valid_room_ids if not locked else [locked[1]]):
                    if locked and room_id != locked[1]:
                        continue
                    # If room is already reserved by a prior wave at this timeslot
                    if not locked and (room_id, ts_id) in occupied_room_slots:
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

        # Identify merged follower variables (to avoid double-counting in room & faculty conflicts)
        merged_follower_vars: dict[int, int] = {}
        merged_sessions_count = 0
        if self.input.merge_common_courses and self._merge_groups:
            subj_v_indices: dict[int, list[int]] = {}
            for v_idx, (subj, _) in enumerate(self._variables):
                subj_v_indices.setdefault(subj["id"], []).append(v_idx)

            for mg_id, group_subjs in self._merge_groups.items():
                if len(group_subjs) < 2:
                    continue
                merged_sessions_count += 1
                anchor_sid = group_subjs[0]["id"]
                anchor_v_indices = subj_v_indices.get(anchor_sid, [])
                for other_subj in group_subjs[1:]:
                    other_v_indices = subj_v_indices.get(other_subj["id"], [])
                    for sess_idx in range(min(len(anchor_v_indices), len(other_v_indices))):
                        v_anchor = anchor_v_indices[sess_idx]
                        v_other = other_v_indices[sess_idx]
                        merged_follower_vars[v_other] = v_anchor

        # ─── Constraint: No faculty conflict (same timeslot) ────────────
        faculty_vars: dict[int, dict[int, list]] = {}  # faculty_id -> ts_id -> [boolvar list]
        faculty_vars_by_v: dict[int, dict[int, dict[int, list]]] = {}  # fid -> ts_id -> v_idx -> [vars]
        for v_idx, (subj, _) in enumerate(self._variables):
            if v_idx in merged_follower_vars:
                continue
            fid = subj["faculty_id"]
            if fid is None:
                continue
            faculty_vars.setdefault(fid, {})
            faculty_vars_by_v.setdefault(fid, {})
            for ts_id in x.get(v_idx, {}):
                faculty_vars[fid].setdefault(ts_id, [])
                faculty_vars_by_v[fid].setdefault(ts_id, {}).setdefault(v_idx, [])
                for room_id in x[v_idx][ts_id]:
                    var = x[v_idx][ts_id][room_id]
                    faculty_vars[fid][ts_id].append(var)
                    faculty_vars_by_v[fid][ts_id][v_idx].append(var)

        for fid, ts_dict in faculty_vars.items():
            for ts_id, var_list in ts_dict.items():
                if len(var_list) > 1:
                    model.add(sum(var_list) <= 1)

        # ─── Constraint: No room conflict (same timeslot) ───────────────
        room_ts_vars: dict[int, dict[int, list]] = {}  # room_id -> ts_id -> [boolvar list]
        for v_idx in range(len(self._variables)):
            if v_idx in merged_follower_vars:
                continue
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

        # Pre-identify paired lab block variables so avoid_back_to_back does not penalize them
        lab_paired_v_indices = set()
        if self.input.consecutive_labs:
            for sid, v_indices in subject_session_vars.items():
                subj = next((s for s in self.input.subjects if s["id"] == sid), None)
                if not subj or not subj.get("is_lab"):
                    continue
                sessions = subj.get("sessions_per_week", 0)
                num_blocks = sessions // 2
                for block_idx in range(num_blocks):
                    v_a = v_indices[block_idx * 2]
                    v_b = v_indices[block_idx * 2 + 1]
                    lab_paired_v_indices.add(frozenset({v_a, v_b}))

        num_active_days = len(self._ts_by_day)
        for sid, v_indices in subject_session_vars.items():
            subj = next((s for s in self.input.subjects if s["id"] == sid), None)
            is_lab_subj = bool(self.input.consecutive_labs and subj and subj.get("is_lab"))
            eff_max_cpd = max(max_cpd, 2) if is_lab_subj else max_cpd
            if num_active_days > 0:
                eff_max_cpd = max(eff_max_cpd, (len(v_indices) + num_active_days - 1) // num_active_days)
            for day, day_ts_ids in self._ts_by_day.items():
                day_ts_set = set(day_ts_ids)
                day_vars = []
                for v_idx in v_indices:
                    for ts_id in x.get(v_idx, {}):
                        if ts_id in day_ts_set:
                            for room_id in x[v_idx][ts_id]:
                                day_vars.append(x[v_idx][ts_id][room_id])
                if len(day_vars) > eff_max_cpd:
                    model.add(sum(day_vars) <= eff_max_cpd)

        # ─── Constraint: Cohort Daily Load Balancing & Distribution ──────
        # Distribute classes for each cohort (department + semester) evenly
        # across all active days of the week rather than clustering on single days.
        num_active_days = len(self._ts_by_day)
        if self._cohort_subjects and num_active_days > 1:
            PENALTY_DAY_IMBALANCE = 15
            for cohort_key, cohort_subjs in self._cohort_subjects.items():
                ck_str = (
                    f"{cohort_key[0]}_{cohort_key[1]}"
                    if isinstance(cohort_key, (list, tuple)) and len(cohort_key) >= 2
                    else str(cohort_key)
                )
                cohort_sid_set = {s["id"] for s in cohort_subjs}
                cohort_v_indices = [
                    v_idx for v_idx, (s, _) in enumerate(self._variables)
                    if s["id"] in cohort_sid_set
                ]
                total_cohort_sessions = len(cohort_v_indices)
                if total_cohort_sessions == 0:
                    continue

                # Target sessions per day
                target_per_day = max(1, round(total_cohort_sessions / num_active_days))
                min_expected_per_day = max(1, total_cohort_sessions // num_active_days - 1) if total_cohort_sessions >= num_active_days else 0
                max_target_per_day = max(2, (total_cohort_sessions + num_active_days - 1) // num_active_days + 1)

                for day, day_ts_ids in self._ts_by_day.items():
                    day_ts_set = set(day_ts_ids)
                    day_vars = []
                    for v_idx in cohort_v_indices:
                        for ts_id in x.get(v_idx, {}):
                            if ts_id in day_ts_set:
                                for room_id in x[v_idx][ts_id]:
                                    day_vars.append(x[v_idx][ts_id][room_id])

                    if not day_vars:
                        continue

                    # Soft penalty: penalize days falling below minimum expected sessions
                    if min_expected_per_day > 0 and len(day_vars) >= min_expected_per_day:
                        under_var = model.new_int_var(0, min_expected_per_day, f"coh_{ck_str}_{day}_under")
                        model.add(under_var >= min_expected_per_day - sum(day_vars))
                        penalties.append(under_var * PENALTY_DAY_IMBALANCE)

                    # Soft penalty: penalize days exceeding maximum target daily sessions
                    if len(day_vars) > max_target_per_day:
                        over_var = model.new_int_var(0, len(day_vars), f"coh_{ck_str}_{day}_over")
                        model.add(over_var >= sum(day_vars) - max_target_per_day)
                        penalties.append(over_var * PENALTY_DAY_IMBALANCE)

        # ─── Soft Constraint: Cohort Schedule Contiguity (Minimizing Idle Gaps) ──────
        # Encourages classes for the same student cohort to be continuous / back-to-back
        # on each day, penalizing idle gaps (dead hours) between a student's first and last class.
        PENALTY_COHORT_GAP = 15
        if self._cohort_subjects:
            for cohort_key, cohort_subjs in self._cohort_subjects.items():
                ck_str = (
                    f"{cohort_key[0]}_{cohort_key[1]}"
                    if isinstance(cohort_key, (list, tuple)) and len(cohort_key) >= 2
                    else str(cohort_key)
                )
                cohort_sid_set = {s["id"] for s in cohort_subjs}
                cohort_v_indices = [
                    v_idx for v_idx, (s, _) in enumerate(self._variables)
                    if s["id"] in cohort_sid_set
                ]
                if len(cohort_v_indices) < 2:
                    continue

                for day, day_ts_ids in self._sorted_day_slots.items():
                    if len(day_ts_ids) < 3:
                        continue

                    # For each slot on this day, build indicator variable for whether cohort has a class
                    slot_active_vars = []
                    for ts_id in day_ts_ids:
                        ts_vars = []
                        for v_idx in cohort_v_indices:
                            if ts_id in x.get(v_idx, {}):
                                for room_id in x[v_idx][ts_id]:
                                    ts_vars.append(x[v_idx][ts_id][room_id])
                        if ts_vars:
                            is_active = model.new_bool_var(f"act_{ck_str}_{day}_{ts_id}")
                            model.add(sum(ts_vars) >= is_active)
                            model.add(sum(ts_vars) <= len(ts_vars) * is_active)
                            slot_active_vars.append((ts_id, is_active))
                        else:
                            slot_active_vars.append((ts_id, None))

                    num_day_slots = len(slot_active_vars)
                    # Prefix prefix_active[i] = True if any slot <= i is active
                    prefix_active = []
                    for i in range(num_day_slots):
                        p_var = model.new_bool_var(f"pre_{ck_str}_{day}_{i}")
                        sub_vars = [v for _, v in slot_active_vars[: i + 1] if v is not None]
                        if sub_vars:
                            model.add(sum(sub_vars) >= p_var)
                            model.add(sum(sub_vars) <= len(sub_vars) * p_var)
                        else:
                            model.add(p_var == 0)
                        prefix_active.append(p_var)

                    # Suffix suffix_active[i] = True if any slot >= i is active
                    suffix_active = []
                    for i in range(num_day_slots):
                        s_var = model.new_bool_var(f"suf_{ck_str}_{day}_{i}")
                        sub_vars = [v for _, v in slot_active_vars[i:] if v is not None]
                        if sub_vars:
                            model.add(sum(sub_vars) >= s_var)
                            model.add(sum(sub_vars) <= len(sub_vars) * s_var)
                        else:
                            model.add(s_var == 0)
                        suffix_active.append(s_var)

                    # An idle gap occurs at slot j (0 < j < num_day_slots - 1) if:
                    # prefix_active[j-1] == 1 AND suffix_active[j+1] == 1 AND slot_active[j] == 0
                    for j in range(1, num_day_slots - 1):
                        act_j = slot_active_vars[j][1]
                        pre_j = prefix_active[j - 1]
                        suf_j = suffix_active[j + 1]

                        gap_var = model.new_bool_var(f"gap_{ck_str}_{day}_{j}")
                        if act_j is not None:
                            model.add(gap_var >= pre_j + suf_j - act_j - 1)
                        else:
                            model.add(gap_var >= pre_j + suf_j - 1)
                        penalties.append(gap_var * PENALTY_COHORT_GAP)

        # ─── Soft Constraint: Balance faculty workload (prefer <= 3/day) ─────────
        if self.input.balance_faculty_workload:
            PENALTY_FACULTY_OVERLOAD = 15
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
                        overload_var = model.new_int_var(
                            0, len(var_list), f"fac_{fid}_{day}_overload"
                        )
                        model.add(overload_var >= sum(var_list) - 3)
                        penalties.append(overload_var * PENALTY_FACULTY_OVERLOAD)

        # ─── Constraint: Avoid back-to-back for same faculty ────────────
        if self.input.avoid_back_to_back:
            PENALTY_BACK_TO_BACK = 25
            for fid, ts_dict in faculty_vars_by_v.items():
                ts_ids_for_fac = sorted(ts_dict.keys(), key=lambda t: (self._ts_map[t]["day"], str(self._ts_map[t]["start_time"])))
                for i in range(len(ts_ids_for_fac)):
                    for j in range(i + 1, len(ts_ids_for_fac)):
                        ts_a, ts_b = ts_ids_for_fac[i], ts_ids_for_fac[j]
                        if self._are_consecutive(ts_a, ts_b):
                            lab_pair_found = False
                            if lab_paired_v_indices:
                                for v_a in ts_dict[ts_a]:
                                    for v_b in ts_dict[ts_b]:
                                        if frozenset({v_a, v_b}) in lab_paired_v_indices:
                                            lab_pair_found = True
                                            break
                                    if lab_pair_found:
                                        break

                            if not lab_pair_found:
                                vars_a = faculty_vars[fid][ts_a]
                                vars_b = faculty_vars[fid][ts_b]
                                b2b_var = model.new_bool_var(f"b2b_{fid}_{ts_a}_{ts_b}")
                                model.add(sum(vars_a) + sum(vars_b) <= 1 + b2b_var)
                                penalties.append(b2b_var * PENALTY_BACK_TO_BACK)
                            else:
                                for v_a, vars_a in ts_dict[ts_a].items():
                                    for v_b, vars_b in ts_dict[ts_b].items():
                                        if frozenset({v_a, v_b}) in lab_paired_v_indices:
                                            continue
                                        b2b_var = model.new_bool_var(f"b2b_{fid}_{v_a}_{v_b}_{ts_a}_{ts_b}")
                                        model.add(sum(vars_a) + sum(vars_b) <= 1 + b2b_var)
                                        penalties.append(b2b_var * PENALTY_BACK_TO_BACK)


        # ─── Constraint: Building transit ───────────────────────────────
        # For same faculty back-to-back, rooms must share a building.
        # If avoid_back_to_back is active, consecutive slots are already forbidden.
        if not self.input.avoid_back_to_back:
            faculty_bldg_vars: dict[int, dict[int, dict[str, list]]] = {}
            for v_idx in range(len(self._variables)):
                fid = self._variables[v_idx][0]["faculty_id"]
                if fid is None:
                    continue
                for ts_id in x.get(v_idx, {}):
                    for room_id in x[v_idx][ts_id]:
                        bldg = self._room_map[room_id].get("building")
                        if bldg:
                            faculty_bldg_vars.setdefault(fid, {}).setdefault(ts_id, {}).setdefault(bldg, []).append(
                                x[v_idx][ts_id][room_id]
                            )

            for fid, ts_dict in faculty_bldg_vars.items():
                for ts_a, ts_b in self._consecutive_pairs:
                    if ts_a >= ts_b or ts_a not in ts_dict or ts_b not in ts_dict:
                        continue
                    for bldg_a, vars_a in ts_dict[ts_a].items():
                        for bldg_b, vars_b in ts_dict[ts_b].items():
                            if bldg_a != bldg_b:
                                model.add(sum(vars_a) + sum(vars_b) <= 1)

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

        # ═══════════════════════════════════════════════════════════════
        # Phase 17: Multi-Department Constraints
        # ═══════════════════════════════════════════════════════════════

        # ─── Constraint: Semester Cohort Non-Overlap ────────────────────
        # For each (dept_id, semester) cohort, no two mandatory core subjects
        # may be assigned to the same timeslot.
        if self._cohort_subjects:
            total_ts_available = len(self._ts_map)
            PENALTY_COHORT_CLASH = 50

            for cohort_key, cohort_subjs in self._cohort_subjects.items():
                mandatory_subjs = [
                    s for s in cohort_subjs if not s.get("elective_group_id")
                ]
                cohort_sessions = sum(s.get("sessions_per_week", 3) for s in mandatory_subjs)

                # Group variables by subject id
                cohort_subj_vars = defaultdict(list)
                for subj in mandatory_subjs:
                    for v_idx, (s, _) in enumerate(self._variables):
                        if s["id"] == subj["id"]:
                            cohort_subj_vars[subj["id"]].append(v_idx)

                # If bloated cohort (> timeslot capacity), protect core courses,
                # and soft-penalize secondary specialization tracks.
                max_core_count = max(1, min(4, (total_ts_available - 6) // 4))
                is_bloated = cohort_sessions > max(16, total_ts_available - 6) or len(mandatory_subjs) > max_core_count
                if is_bloated:
                    sorted_subjs = sorted(
                        mandatory_subjs,
                        key=lambda s: (s.get("required_capacity", 0), s.get("id", 0)),
                        reverse=True,
                    )
                    core_subj_ids = set(s["id"] for s in sorted_subjs[:max_core_count])
                else:
                    core_subj_ids = set(s["id"] for s in mandatory_subjs)

                cohort_core_ts_vars = {}
                cohort_sec_ts_vars = {}

                for s_id, v_list in cohort_subj_vars.items():
                    target_map = cohort_core_ts_vars if s_id in core_subj_ids else cohort_sec_ts_vars
                    for v_idx in v_list:
                        for ts_id in x.get(v_idx, {}):
                            target_map.setdefault(ts_id, [])
                            for room_id in x[v_idx][ts_id]:
                                target_map[ts_id].append(x[v_idx][ts_id][room_id])

                ck_str = (
                    f"{cohort_key[0]}_{cohort_key[1]}"
                    if isinstance(cohort_key, (list, tuple)) and len(cohort_key) >= 2
                    else str(cohort_key)
                )

                # Core courses: heavy penalty (or hard non-overlap if plenty of slots)
                core_sessions = sum(s.get("sessions_per_week", 3) for s in mandatory_subjs if s["id"] in core_subj_ids)
                strict_core = core_sessions <= (total_ts_available - 8)

                for ts_id, var_list in cohort_core_ts_vars.items():
                    if len(var_list) > 1:
                        if strict_core:
                            model.add(sum(var_list) <= 1)
                        else:
                            clash_var = model.new_int_var(0, len(var_list), f"coh_{ck_str}_{ts_id}_core_clash")
                            model.add(clash_var >= sum(var_list) - 1)
                            penalties.append(clash_var * PENALTY_COHORT_CLASH * 5)

                # Soft penalty and hard cap for clashes involving secondary specialization courses
                max_simultaneous = max(2, (len(mandatory_subjs) + 4) // 5)
                for ts_id, sec_list in cohort_sec_ts_vars.items():
                    core_list = cohort_core_ts_vars.get(ts_id, [])
                    all_list = core_list + sec_list
                    if len(all_list) > 1:
                        clash_var = model.new_int_var(0, len(all_list), f"coh_{ck_str}_{ts_id}_clash")
                        model.add(clash_var >= sum(all_list) - 1)
                        penalties.append(clash_var * PENALTY_COHORT_CLASH)
                        if len(all_list) > max_simultaneous:
                            model.add(sum(all_list) <= max_simultaneous)

        # ─── Constraint: Consecutive Lab Blocks ─────────────────────────
        # Lab subjects must occupy 2 consecutive timeslots on the same day
        # in a lab-type room.
        lab_blocks_count = 0
        if self.input.consecutive_labs:
            for sid, v_indices in subject_session_vars.items():
                subj = next((s for s in self.input.subjects if s["id"] == sid), None)
                if not subj or not subj.get("is_lab"):
                    continue

                # Lab subjects should have sessions_per_week as multiples of 2
                sessions = subj["sessions_per_week"]
                if sessions < 2:
                    continue

                # Group v_indices into pairs for 2-hour blocks
                num_blocks = sessions // 2
                lab_blocks_count += num_blocks

                for block_idx in range(num_blocks):
                    v_a = v_indices[block_idx * 2]
                    v_b = v_indices[block_idx * 2 + 1]

                    valid_ts1 = set()
                    valid_ts2 = set()
                    for day, day_pairs in self._consecutive_pairs_ordered.items():
                        for ts1, ts2 in day_pairs:
                            valid_ts1.add(ts1)
                            valid_ts2.add(ts2)
                            common_rooms = set(x.get(v_a, {}).get(ts1, {}).keys()) & \
                                           set(x.get(v_b, {}).get(ts2, {}).keys())
                            for room_id in common_rooms:
                                room_info = self._room_map.get(room_id, {})
                                if room_info.get("room_type") != "lab":
                                    continue
                                model.add_implication(
                                    x[v_a][ts1][room_id], x[v_b][ts2][room_id]
                                )

                    # Prune v_a from timeslots that cannot start a 2-hour block
                    for ts_id in x.get(v_a, {}):
                        if ts_id not in valid_ts1:
                            for room_id in x[v_a][ts_id]:
                                model.add(x[v_a][ts_id][room_id] == 0)

                    # Prune v_b from timeslots that cannot end a 2-hour block
                    for ts_id in x.get(v_b, {}):
                        if ts_id not in valid_ts2:
                            for room_id in x[v_b][ts_id]:
                                model.add(x[v_b][ts_id][room_id] == 0)

        # ─── Constraint: Common Course Merging ──────────────────────────
        # Subjects with the same merge_group_id must be scheduled at the
        # exact same timeslot and room (seminar / central hall).
        if merged_follower_vars:
            for v_other, v_anchor in merged_follower_vars.items():
                for ts_id in x.get(v_anchor, {}):
                    for room_id in x[v_anchor][ts_id]:
                        if ts_id in x.get(v_other, {}) and room_id in x[v_other][ts_id]:
                            model.add(x[v_other][ts_id][room_id] == x[v_anchor][ts_id][room_id])
                        else:
                            model.add(x[v_anchor][ts_id][room_id] == 0)

        # ─── Objective function ─────────────────────────────────────────
        PENALTY_PREF_ROOM = 1
        PENALTY_CHANGE = 10
        PENALTY_SPILLOVER = 25

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

        # ─── Soft/Hard: Academic Block Affinity ─────────────────────────
        # Subjects prefer rooms in their designated academic blocks.
        for v_idx, (subj, _) in enumerate(self._variables):
            allowed_blocks = subj.get("allowed_blocks") or ({subj["block_name"]} if subj.get("block_name") else set())
            if not allowed_blocks:
                continue
            for ts_id in x.get(v_idx, {}):
                for room_id in x[v_idx][ts_id]:
                    room_bldg = self._room_map[room_id].get("building", "")
                    room_block = self._room_map[room_id].get("block_name", "")
                    # Central rooms (seminar / lecture halls) are common campus resources accessible across blocks
                    if "Central" in room_bldg or "Main Block" in room_bldg:
                        continue
                    if room_block and not any(ab in room_block or room_block in ab for ab in allowed_blocks):
                        if self.input.allow_spillover:
                            penalties.append(
                                x[v_idx][ts_id][room_id] * PENALTY_SPILLOVER
                            )
                        else:
                            model.add(x[v_idx][ts_id][room_id] == 0)

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
        solver.parameters.max_time_in_seconds = getattr(self.input, "max_time_in_seconds", 60)
        solver.parameters.relative_gap_limit = 0.20
        solver.parameters.num_workers = 8

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
                        entry = {
                            "subject_id": subj["id"],
                            "subject_code": subj["code"],
                            "faculty_id": subj["faculty_id"],
                            "room_id": room_id,
                            "room_number": room_info["room_number"],
                            "time_slot_id": ts_id,
                            "day": ts_info["day"],
                            "start_time": str(ts_info["start_time"]),
                            "end_time": str(ts_info["end_time"]),
                        }
                        mg = subj.get("merge_group_id")
                        if mg:
                            entry["merge_group_id"] = mg
                        timetable.append(entry)
                        break  # Found the assigned value for this v_idx+ts_id
                else:
                    continue
                break  # Found the assigned value for this v_idx

        # Sort by day and start time
        day_order = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5}
        timetable.sort(key=lambda e: (day_order.get(e["day"], 99), e["start_time"]))

        # Count distinct cohorts
        cohort_keys = set()
        for subj in self.input.subjects:
            ck = subj.get("cohort_key")
            if ck:
                cohort_keys.add(tuple(ck) if isinstance(ck, (list, tuple)) else ck)

        logger.info(
            "CP-SAT solved: %d entries, status=%s, objective=%.0f, "
            "cohorts=%d, merged=%d, lab_blocks=%d",
            len(timetable), solver.status_name(status),
            solver.objective_value if penalties else 0,
            len(cohort_keys), merged_sessions_count, lab_blocks_count,
        )

        return SolverResult(
            success=True,
            timetable=timetable,
            cohort_stats=len(cohort_keys),
            merged_sessions_count=merged_sessions_count,
            lab_blocks_count=lab_blocks_count,
        )

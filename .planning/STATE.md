# Phase State

**Current Phase:** Phase 17 (Multi-Department Routine Scheduler - OR-Tools CP-SAT Upgrade)
**Status:** Completed (Verified 100%)

### Recent Activity
- Implemented and verified the enterprise Multi-Department Routine Scheduler across all 178 academic departments and 9 Academic School Blocks (Blocks A to I).
- Formulated and passed 100% of CP-SAT constraints:
  - **Semester Cohort Non-Overlap**: guarantees no two mandatory subjects for any `(department, semester)` cohort overlap at the same timeslot.
  - **2-Hour Consecutive Lab Blocks**: atomic coupling of adjacent timeslots on the same day in dedicated `room_type='lab'` facilities with relaxed per-day thresholds.
  - **Common Course Merging**: concurrent scheduling of shared curriculum across departments into seminar and central lecture halls (`MG-*`) without faculty/room double-counting.
  - **Academic Block Affinity & Spillover Penalty**: routing classes to departmental home blocks with soft fallback to adjacent blocks.
  - **Wave Orchestrator**: block-by-block sequential generation with locked reservations.
- Hardened backend APIs and serializers:
  - Updated `TimetableView` filtering by `block`, `department`, and `semester`.
  - Updated `GenerateTimetableView` validating `scope_type`, `block_name`, `department_id`, and `semester`.
  - Enriched `TimetableEntrySerializer` with `department_names`, `semester`, and `block_name`.
- Upgraded Frontend UI (`TimetablePage.jsx`):
  - Generator Scope Selector (Single Department, Academic School Block, Whole Campus).
  - Smart Routine toggles for Common Course Merging, 2-Hour Lab Blocks, and Dynamic Block Spillover.
  - School Block grid filter and `🧪 2h Lab` & `⚡ Merged` badges.
- Verified test suite:
  - 38/38 scheduler unit tests passing in 1.97s.
  - 500-session scale test passing in 33.7s.
  - Frontend production build (`npm run build`) passing in 5.11s with 0 errors.

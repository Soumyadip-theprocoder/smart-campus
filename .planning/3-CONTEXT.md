# Phase 3 Context: Enhanced Features (Mobile & UI)

## Overview
Phase 3 focuses on improving the user experience for mobile devices and dramatically enhancing the intelligence of the Timetable CSP solver. Note that the "Scalable Vector Search" milestone originally slotted for Phase 3 was completed early during Phase 1.

## Decisions Made

### 1. Mobile Support & UI Fallbacks
- **Decision:** Ensure all React dashboards are fully responsive using modern CSS media queries. Implement a QR code generator and scanner as a fallback for the Attendance app when Face Recognition fails.
- **Rationale:** Ensures that the Smart Campus platform is usable on phones and tablets. The QR code fallback guarantees that attendance can still be reliably tracked even if lighting conditions are poor or camera hardware is unavailable.
- **Implementation Note:** Use standard CSS flexbox/grid media queries for responsiveness. Integrate a robust QR code library (e.g. `qrcode.react` for generation and `html5-qrcode` or similar for scanning).

### 2. Advanced Scheduling Constraints
- **Decision:** Implement **full advanced constraints** in the CSP solver, including student elective preference optimization and complex multi-campus routing.
- **Rationale:** The system needs to scale to realistic, complex university scenarios where students choose electives and must travel between geographically separated buildings across a large campus.
- **Implementation Note:** The backend solver (`backend/apps/scheduler/csp_solver.py`) will require significant refactoring to support building transit times, hard/soft constraint scoring for elective preferences, and potentially clustering algorithms. Since the solver is already asynchronous (Django Q2), the increased compute time will not block the API.

## Exclusions
- **Vector Indexing (pgvector):** Already completed.

# Onboarding Summary

## What Was Learned
The codebase is a robust, decoupled **Smart Campus Management System** leveraging a **Vite + React** frontend and a **Django + DRF** backend.

Key functional pillars include:
1. **AI Face Recognition**: Powered by dlib CNN and OpenCV.
2. **CSP Timetable Solver**: An algorithmic approach to conflict-free class scheduling.
3. **Role-based Dashboards**: Distinct experiences for Admins, Faculty, and Students.
4. **SMTP Automation**: Automated attendance shortage alerts and digital notices.

**Major Technical Observations**:
- The architecture is solid but has potential scaling bottlenecks in the synchronous face-matching logic and the CSP solver.
- The default database is SQLite, which should be migrated to PostgreSQL before significant production usage.
- Testing infrastructure needs to be formalized.

## Next Commands
The codebase map is complete, and the project is initialized in GSD.

Suggested next actions:
- Start planning new features or fixes using `/gsd-plan-phase`.
- Address the concerns highlighted in `.planning/codebase/CONCERNS.md`.

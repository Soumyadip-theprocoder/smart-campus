# Phase 4 Context: Production Hardening & Post-Review Fixes

## 1. Security & Authentication Decisions
- **Face Recognition Engine API (MarkAttendanceView):** We will use a **Static Shared API Key**. We will add an environment variable `FACE_ENGINE_API_KEY` to the Django settings, and the Python face recognition script will send this key in the `Authorization: Api-Key <key>` header. This avoids the overhead of managing expiring JWT tokens for a non-human service.
- **Registration (RegisterView):** The `RegisterView` API endpoint will be **disabled completely** for public access. All user creation (students, faculty, admins) must happen through the Django Admin interface by authorized administrators.
- **SECRET_KEY Configuration:** If the `SECRET_KEY` environment variable is missing in production, the application will **raise an `ImproperlyConfigured` exception** and crash on startup. We will remove the insecure fallback.

## 2. Outstanding Gray Areas from Project Review
- **Permission Guards:** `IsAdminUser` must be applied to `FacultyDetailView` (especially delete operations), `StudentListView`, `FacultyListView`, `SendAttendanceAlertsView`, and `DeleteNoticeView`.
- **FacultyDashboard Filtering:** Will need to be updated to rely on `faculty_id` rather than a fragile string comparison of `faculty_name`.
- **Rate Limiting:** A throttle limit of `5/minute` will be added to the login endpoint.
- **Code Splitting:** Dynamic imports (`React.lazy`) should be implemented in the frontend router to split chunks and prevent the 736KB bundle warning.
- **Django Q2 Config:** Add `'retry': 700` to `Q_CLUSTER` in `settings.py` to fix the retry/timeout mismatch warning.

This context locks in the implementation details for the production hardening phase. Downstream planning agents must strictly follow these architectural decisions.

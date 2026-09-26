# API Reference

The backend exposes a comprehensive RESTful API built on the Django REST Framework (DRF), secured via SimpleJWT.

## Base URL
`http://localhost:8000/api`

## Authentication (`/api/auth/`)
All endpoints (except login/register) require an `Authorization: Bearer <token>` header.

- `POST /api/auth/login/`: Authenticates a user and returns `{ access, refresh, role }`.
- `POST /api/auth/register/`: Creates a new user profile.
- `GET /api/auth/me/`: Retrieves the currently authenticated user's profile and metadata.
- `POST /api/auth/token/refresh/`: Issues a new access token using a valid refresh token.

## Analytics & Reporting (`/api/analytics/`)
- `GET /api/analytics/overview/`: Returns aggregated KPI stats (total students, active classes, campus attendance percentage).
- `GET /api/analytics/department-trends/`: Returns historical attendance arrays broken down by department for chart rendering.

## Scheduler (`/api/scheduler/`)
- `GET /api/scheduler/subjects/`: Lists all subjects.
- `GET /api/scheduler/rooms/`: Lists all rooms.
- `GET /api/scheduler/timetable/`: Retrieves the active generated timetable.
- `POST /api/scheduler/generate/`: Triggers the async CSP solver to generate a new timetable. Returns `{ task_id: "uuid" }`.
- `GET /api/scheduler/task-status/<task_id>/`: Polling endpoint to check the progress of the async timetable generation.

## Attendance (`/api/attendance/`)
- `GET /api/attendance/`: Lists paginated attendance records.
- `POST /api/attendance/mark/`: Manually overrides or submits an attendance record.
- `GET /api/attendance/report/<student_id>/`: Returns detailed attendance breakdowns per subject for a specific student.
- `GET /api/attendance/export/admin/csv/`: Streams a downloadable CSV export of all attendance records.
- `GET /api/attendance/export/student/pdf/<student_id>/`: Streams a dynamically generated PDF report card.

## Communication (`/api/communication/`)
- `GET /api/communication/notices/`: Lists active digital notices, ordered by priority.
- `POST /api/communication/notices/create/`: Creates a new priority notice (Admin only).
- `POST /api/communication/alerts/attendance/`: Triggers the Django Q2 worker to run the predictive analytics engine and dispatch SMTP emails to students falling below the 75% attendance threshold.

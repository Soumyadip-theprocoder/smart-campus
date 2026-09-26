# Codebase Structure

## Root Directory
- `backend/`: Django REST Framework API, Q2 worker tasks, and ML Engine.
- `frontend/`: React Vite SPA.
- `.planning/`: GSD workflow state and architecture documentation.
- `docs/`: Markdown files describing schemas, deployment, and APIs.

## Backend (`backend/`)
- `config/`: Main Django settings, URL router, and WSGI entry point.
- `apps/`: Modular Django apps holding models, serializers, and views.
  - `accounts/`: Auth, `User`, `StudentProfile`, `FacultyProfile`.
  - `attendance/`: Face ID verification logic, attendance logging.
  - `scheduler/`: Timetable generation logic (CSP solver).
  - `communication/`: Notices and email alerting system.
  - `analytics/`: ML predictive algorithms for attendance trajectory mapping.
- `face_recognition_engine/`: OpenCV + dlib scripts for extracting face vectors.

## Frontend (`frontend/src/`)
- `api/`: Centralized Axios instance configuration with JWT interceptors.
- `context/`: `AuthContext` (JWT session management) and `ThemeContext` (Dark Mode).
- `components/`: Generic UI elements.
  - `DataTable.jsx`: Responsive data grid.
  - `StatCard.jsx`: Reusable KPI card.
  - `ErrorBoundary.jsx` & `LocalErrorBoundary.jsx`: Fault-tolerance wrappers.
- `features/`: Route-specific views.
  - `auth/`: Login pages.
  - `dashboard/`: `AdminDashboard`, `StudentDashboard`, `FacultyDashboard`.
  - `attendance/`: manual marking and history views.
  - `scheduler/`: `TimetablePage`, subject/room management.
- `index.css`: Design system tokens (glassmorphism, variables, layout grids).

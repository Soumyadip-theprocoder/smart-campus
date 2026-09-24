# Phase 4 Plan: Production Hardening & Post-Review Fixes

## Overview
This phase focuses on hardening the production environment and implementing the security and architectural fixes identified during the project review (Phase 4).

## Context Reference
All decisions implemented here are defined in `4-CONTEXT.md`.

## Task Breakdown

### 1. Security & Authentication Updates
- [ ] **Task 1.1: Static Shared API Key for Face Recognition**
  - Update `backend/config/settings.py` to define `FACE_ENGINE_API_KEY = os.environ.get('FACE_ENGINE_API_KEY', None)`.
  - Create a custom DRF permission class `HasFaceEngineAPIKey` in `backend/apps/attendance/permissions.py` (create file if it doesn't exist).
  - Update `backend/apps/attendance/views.py` (`MarkAttendanceView`) to use `permission_classes = [HasFaceEngineAPIKey]`.
- [ ] **Task 1.2: Disable Open Registration**
  - Update `backend/apps/accounts/views.py` (`RegisterView`) to either remove the endpoint or set `permission_classes = [permissions.IsAdminUser]`. (As per context, we disable it completely for public access. Changing to `IsAdminUser` is easiest).
- [ ] **Task 1.3: Enforce SECRET_KEY**
  - Update `backend/config/settings.py` to raise `django.core.exceptions.ImproperlyConfigured` if `SECRET_KEY` is not found in the environment, rather than falling back to an insecure default.

### 2. Permission Guards
- [ ] **Task 2.1: Lock Down Faculty/Student Views**
  - Update `backend/apps/accounts/views.py`: Change `permission_classes` to `[permissions.IsAdminUser]` for `StudentListView`, `FacultyListView`, and `FacultyDetailView`.
- [ ] **Task 2.2: Lock Down Communication Views**
  - Update `backend/apps/communication/views.py`: Add `permissions.IsAdminUser` to `SendAttendanceAlertsView` and `DeleteNoticeView`.

### 3. Application Fixes & Improvements
- [ ] **Task 3.1: FacultyDashboard Filtering**
  - Update `frontend/src/features/dashboard/FacultyDashboard.jsx` to filter timetables using `faculty_id` (e.g., `item.subject.faculty.user.id === user.id` or similar depending on the timetable payload) instead of matching `faculty_name`.
- [ ] **Task 3.2: Login Rate Limiting**
  - Update `backend/config/settings.py` to add DRF throttling defaults (`REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'login': '5/minute'}`).
  - Update `backend/apps/accounts/views.py` (`LoginView` or token endpoint) to use `throttle_classes = [AnonRateThrottle]` and `throttle_scope = 'login'`.
- [ ] **Task 3.3: Django Q2 Configuration**
  - Update `backend/config/settings.py` to add `'retry': 700` inside `Q_CLUSTER`.

### 4. Frontend Optimization
- [ ] **Task 4.1: Code Splitting (React.lazy)**
  - Update `frontend/src/App.jsx` (or wherever routes are defined) to replace static imports of feature pages (e.g., `AdminDashboard`, `FacultyDashboard`, `StudentDashboard`, `TimetablePage`, `AttendancePage`) with `React.lazy()` dynamic imports.
  - Wrap the routes in a `<Suspense>` boundary with a loading fallback.

### 5. Project Polish & UI/UX Refinements (Aiming for 5-star Frontend UX)
- [ ] **Task 5.1: UI/UX & Animations**
  - Refine existing React components for consistent styling.
  - Enhance micro-animations (e.g., hover effects, page transitions).
  - Fix any visual glitches across the dashboard and timetable views.
- [ ] **Task 5.2: Error Handling & Notifications**
  - Implement a global React Error Boundary component to prevent full app crashes.
  - Add user-friendly toast notifications for success/error states across the app.
  - Enhance form validation for user inputs (e.g., login, profile updates).

### 6. Code Quality, Architecture & Refactoring (Aiming for 5-star Code & Architecture)
- [ ] **Task 6.1: Technical Debt & Refactoring**
  - Remove unused code, console logs, and dead variables across both frontend and backend.
  - Fix the `import random` inside the loop in `csp_solver.py`.
  - Ensure strict linting passes without warnings.

### 7. Deployment & Production Readiness (Aiming for 5-star Deployment)
- [ ] **Task 7.1: Production Readiness Check**
  - Finalize and document Docker configurations (if used).
  - Ensure all environment variables are properly documented and handled.
  - Finalize the Render deployment scripts (including HTTPS redirect enforcement via `SECURE_SSL_REDIRECT = True`).
  - Fix hardcoded passwords in production seed scripts (use environment variables).

### 8. Testing & Quality Assurance (Aiming for 5-star Testing)
- [ ] **Task 8.1: Expand Test Coverage**
  - Write unit tests for the newly added security permission guards (`HasFaceEngineAPIKey`, `IsAdminUser`).
  - Ensure the CSP solver has comprehensive unit tests covering edge cases.
  - Add integration tests for the authentication and login throttling flow.

### 9. Verification
- [ ] **Task 9.1: Security Verification**
  - Verify that `MarkAttendanceView` rejects requests without the `Api-Key` header.
  - Verify that standard users cannot access `StudentListView` or `FacultyDetailView`.
- [ ] **Task 9.2: Optimization Verification**
  - Run `npm run build` locally in the frontend and confirm the bundle chunks are significantly smaller (warning about >500KB chunks should be mitigated).
- [ ] **Task 9.3: Polish Verification**
  - Trigger a UI error manually to verify the Error Boundary catches it gracefully.
  - Verify toast notifications appear for form submissions.

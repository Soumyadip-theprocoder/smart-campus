# Phase 5 Plan: PDF Feature Parity

## Overview
This phase implements the final missing features required by the project proposal PDF: Web-based Face Data Registration using a webcam, and Data Visualization & Exporting for both Administrators and Students.

## Context Reference
All decisions implemented here are defined in `5-CONTEXT.md`.

## Task Breakdown

### 1. Face Data Registration (Backend)
- [ ] **Task 1.1: Registration API Endpoint**
  - Create a new endpoint `POST /api/accounts/student/face-register/` in `backend/apps/accounts/views.py`.
  - The view should expect a multipart form data containing an image file.
  - The endpoint should be secured for authenticated users (or specific roles).
- [ ] **Task 1.2: Synchronous Encoding Extraction**
  - Update `backend/apps/accounts/serializers.py` or the view to import the Python face recognition logic.
  - Extract the 128-d encoding from the uploaded image synchronously during the request.
  - If no face or multiple faces are detected, return a `400 Bad Request` with an appropriate error message.
- [ ] **Task 1.3: Image & Encoding Storage**
  - Save the uploaded image to the `face_image` field of the user's `Student` profile.
  - Save the extracted 128-d vector to the `face_encoding` field.
  - Return a success response.

### 2. Face Data Registration (Frontend)
- [ ] **Task 2.1: Webcam Capture Component**
  - Install a webcam library if necessary (e.g., `react-webcam`) or use the native HTML5 `getUserMedia` API.
  - Create `frontend/src/features/accounts/FaceRegistrationPage.jsx` (or a modal component).
  - Add a live video feed with a "Capture" button.
- [ ] **Task 2.2: Upload Integration**
  - Implement a function to convert the captured image (usually a base64 Data URL or Canvas blob) into a `File` object.
  - Send a `FormData` POST request to `/api/accounts/student/face-register/`.
  - Display success toasts or error messages based on the backend response.

### 3. Data Visualization & Reporting (Backend Exports)
- [ ] **Task 3.1: Admin CSV Export API**
  - Create an endpoint `GET /api/attendance/export/admin/csv/` in `backend/apps/attendance/views.py`.
  - Use Python's `csv` module to generate a report containing attendance statistics and records.
  - Set the HTTP response `Content-Type` to `text/csv` and `Content-Disposition` to attachment.
- [ ] **Task 3.2: Student PDF Export API**
  - Create an endpoint `GET /api/attendance/export/student/pdf/` for individual student reports.
  - Use a library (e.g., `reportlab` or HTML-to-PDF generation like `weasyprint` / `xhtml2pdf`) to generate a printable PDF.
  - Return the PDF with appropriate headers.

### 4. Data Visualization & Reporting (Frontend)
- [ ] **Task 4.1: Visual Analytics Dashboard**
  - Enhance the existing `AdminDashboard` and `StudentDashboard` with visual charts.
  - Implement chart components (using a library like `recharts` or `chart.js`) to display attendance trends over time, or class distributions.
- [ ] **Task 4.2: Export Buttons**
  - Add a "Download CSV Report" button to the Admin Dashboard that triggers the CSV export API.
  - Add a "Download PDF Report" button to the Student Dashboard that triggers the PDF export API.

### 5. Verification
- [ ] **Task 5.1: Webcam Integration Test**
  - Test the webcam component on a real device (or simulated camera) to ensure capturing works.
  - Verify that a valid face uploads successfully, while an empty room triggers a backend validation error.
- [ ] **Task 5.2: Export Format Verification**
  - Download the Admin CSV and verify it opens correctly in a spreadsheet application.
  - Download the Student PDF and verify the formatting is clean and professional.
# Phase 5.1: Codebase & Documentation Polish

## Objective
Comprehensive cleanup of the backend codebase, removal of deprecated files and old code, and polishing of project documentation to ensure a pristine state for the upcoming v2.0 milestone.

## Context
The project has successfully shipped v1.0 (MVP) and v1.1 (Production Hardening & Features). Before beginning heavy new feature work for v2.0 (Predictive Analytics), technical debt must be paid down. This phase focuses on linting the backend, removing unused legacy code (especially any remnants from before the UI implementations), and making sure all documentation reads cleanly for the newest project state.

## Tasks

### 1. Codebase Linting & Formatting
- **File:** `backend/` directory
- **Action:** Run `black`, `isort`, and `flake8` across the backend apps (`accounts`, `attendance`, `scheduler`, `config`).
- **Goal:** Fix any styling inconsistencies, remove unused imports (`F401`), and resolve undefined variables or too-broad exceptions.

### 2. Dead Code Removal
- **Action:** Identify and remove any unused legacy files, such as outdated manual database seed scripts, leftover mock views, or unused dependencies in `requirements.txt`.
- **Validation:** Ensure the app still runs and tests pass after removal.

### 3. Documentation Polish
- **File:** `README.md`
- **Action:** Rewrite the `README.md` to reflect the v2.0 architecture and newly shipped features (Webcam face registration, PDF exports, automated timetable). Ensure the badges, tech stack, and deployment instructions are crystal clear and free of typos.
- **File:** `TESTING.md`
- **Action:** Polish testing documentation to remove outdated references to old manual workflows, replacing them with the current web-based UAT flows.

### 4. Planning Artifact Verification
- **File:** `.planning/LEARNINGS.md`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`
- **Action:** Ensure all active planning artifacts correctly frame the project in its current post-v1.1 state. Archive any stray v1.0 docs that clutter the active directory.

## Verification
- Code passes `flake8` with 0 warnings/errors for critical rules (E9, F63, F7, F82).
- Django tests still pass successfully: `python manage.py test`.
- All documentation files render correctly in Markdown.
# Phase 5.2: Frontend UI Rewrite & Polish

## Objective
Execute a comprehensive frontend rewrite to significantly elevate the user experience, applying a premium glassmorphism aesthetic, smooth micro-interactions, responsive chart integrations, and cohesive placement of the new v1.1 features (webcam and exports).

## Context
While the core features (PDF/CSV generation, AI facial recognition, and CSP scheduling) are functionally complete, the frontend UI lacks the high-end polish expected of a modern web application. The `UI-SPEC.md` outlines a glassmorphism theme, robust responsive scaling, and refined layouts for the dashboards. This phase will implement that specification completely.

## Tasks

### 1. Global Theming & CSS Variables
- **File:** `frontend/src/index.css` (or equivalent global styles)
- **Action:** Define deep navy/purple dark mode variables, glassmorphism utility classes (blur, translucent backgrounds, subtle glowing borders), and smooth transition utilities for hover states.

### 2. Admin Dashboard Rewrite
- **File:** `frontend/src/features/dashboard/AdminDashboard.jsx`
- **Action:** 
  - Restyle all StatCards to use the new glassmorphism theme with hover scaling.
  - Implement a `ResponsiveContainer` wrapping a `LineChart` (via `recharts`) below the StatCards to visualize the Weekly Attendance trend, using gradient fills (e.g., `emerald` to `blue`).
  - Style the "Export CSV" button as a sleek secondary glass button in the top-right header area, featuring a `<HiOutlineDownload />` icon.
  - Ensure the recent notices and quick actions fit seamlessly into the new layout grid.

### 3. Student Dashboard Rewrite
- **File:** `frontend/src/features/dashboard/StudentDashboard.jsx`
- **Action:**
  - Redesign the layout to clearly separate the attendance summary, today's schedule, and recent notices.
  - Integrate a responsive `PieChart` or `DoughnutChart` (via `recharts`) to visualize subject-wise attendance breakdown.
  - Place the "Download PDF Report" button prominently (e.g., next to the analytics chart) as a secondary glass button.
  - If the student's `face_encoding` is null, prominently display the "Register Face Data" primary accent button to trigger the webcam flow.

### 4. Face Registration Flow Refinement
- **File:** `frontend/src/features/accounts/FaceRegistrationModal.jsx` (or similar)
- **Action:** 
  - Ensure the modal or page uses a dark overlay with a centered, rounded-corner video feed box containing a subtle glowing border.
  - Implement clear state transitions: "Loading (checking permissions)", "Ready", "Uploading (spinner)", and "Success/Error (toast/overlay)".
  - Verify mobile-first scaling so the video feed doesn't overflow or break the aspect ratio on small screens.

### 5. Responsive Behavior & Cross-Device Optimization
- **Action:** Audit the entire application on various viewport sizes (mobile, tablet, desktop). Ensure generous padding (`1rem` to `1.5rem`), easily tappable modal close buttons, and legible typography on all devices. Charts must shrink gracefully.

## Verification
- Visual inspection confirms the deep navy/purple glassmorphism theme is consistently applied.
- Hover states and micro-animations (e.g., button scaling, modal fade-ins) are smooth.
- `recharts` components render correctly and resize dynamically without breaking layouts.
- Face registration modal transitions gracefully through all defined states.
- Mobile viewport testing confirms no horizontal scrolling or overlapping elements.

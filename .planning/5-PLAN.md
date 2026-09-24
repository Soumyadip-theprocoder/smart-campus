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

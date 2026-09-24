# Phase 5: PDF Feature Parity - User Acceptance Testing (UAT)

## Overview
This document tracks the UAT progress for Phase 5 (Webcam Registration, Dashboard Charts, and CSV/PDF Data Exports).

## Test Cases

### 1. Face Data Registration
- [x] **Test 1.1**: Log in as a student without a face encoding. The Student Dashboard should display a "Register Face Data" button.
- [x] **Test 1.2**: Click the "Register Face Data" button. A modal with a live webcam feed should appear.
- [x] **Test 1.3**: Click "Capture". The modal should process the image and show a success message, then close automatically.
- [x] **Test 1.4**: Refresh the Student Dashboard. The "Register Face Data" button should no longer be visible.

### 2. Export & Reporting
- [x] **Test 2.1**: On the Student Dashboard, click the "Download PDF" button. A PDF file named `attendance_<enrollment_number>.pdf` should be downloaded.
- [x] **Test 2.2**: Open the downloaded PDF. It should display a cleanly formatted report of the student's attendance summary.
- [x] **Test 2.3**: Log out, then log in as an Admin user.
- [x] **Test 2.4**: On the Admin Dashboard, click the "Export CSV" button. A CSV file named `attendance_report.csv` should be downloaded, containing global attendance records.

### 3. Visual Analytics (Dashboards)
- [x] **Test 3.1**: On the Admin Dashboard, verify the "Weekly Attendance" chart renders as a responsive line chart with hovering tooltips.
- [x] **Test 3.2**: On the Student Dashboard, verify the "Attendance by Subject" chart renders as a responsive pie/doughnut chart with hovering tooltips.

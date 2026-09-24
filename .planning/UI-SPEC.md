# UI Specification: Phase 5 (PDF Feature Parity)

## 1. Aesthetic Guidelines
- **Theme:** Glassmorphism with deep navy/purple dark mode, matching existing `AdminDashboard` and `StudentDashboard`.
- **Micro-interactions:** Interactive hover states on all charts and buttons. Fade-in animations for the webcam modal.
- **Charts:** Use a modern, customizable chart library (e.g., `recharts` or `chart.js`) styled to match the dark theme (transparent backgrounds, vibrant accent colors for data points).

## 2. Component Specifications

### 2.1. FaceRegistrationModal (or Page)
- **Trigger:** A prominent "Register Face Data" button on the Student Dashboard if `face_encoding` is null.
- **Layout:**
  - A modal overlay or dedicated route.
  - A live video feed box in the center with rounded corners and a subtle glowing border.
  - A "Capture" button (primary accent color, e.g., blue or emerald).
- **States:**
  - **Loading:** Checking camera permissions...
  - **Ready:** Live feed visible.
  - **Uploading:** Spinner over the captured frame after clicking "Capture".
  - **Success:** Green checkmark overlay and automatic modal dismissal.
  - **Error:** Red toast notification if the backend rejects the image (e.g., no face detected).

### 2.2. Visual Analytics Dashboard
- **Admin Dashboard:**
  - **Component:** Line chart or Bar chart showing system-wide attendance trends over the last 7 days.
  - **Placement:** Below the main StatCards.
  - **Styling:** Gradient fill under the line chart, matching the existing `emerald`/`blue` gradients.
- **Student Dashboard:**
  - **Component:** A Doughnut/Pie chart breaking down attendance by subject.
  - **Placement:** Beside or above the "Recent Attendance" list.

### 2.3. Export Buttons
- **Admin CSV Export:**
  - Placed near the top-right of the Admin Dashboard or Attendance page.
  - Icon: `<HiOutlineDownload />`. Label: "Export CSV".
  - Style: Secondary glass button.
- **Student PDF Export:**
  - Placed near the top-right of the Student Dashboard or next to the Analytics chart.
  - Icon: `<HiOutlineDocumentDownload />`. Label: "Download PDF Report".
  - Style: Secondary glass button.

## 3. Responsive Behavior & Cross-Device Optimization
- **Mobile-First Flexibility:** All UI components, including the new FaceRegistrationModal, must be fully responsive across mobile (portrait/landscape), tablet, and desktop devices.
- **Charts Scaling:** Must use responsive containers (`ResponsiveContainer` in Recharts) to shrink on mobile devices without overlapping text or breaking the aspect ratio.
- **Webcam Feed:** The video feed must scale down gracefully, maintaining a centered aspect ratio on mobile devices and avoiding overflow.
- **UI Cleanliness:** Maintain generous padding (`1rem` to `1.5rem`), avoid overwhelming the screen with too many buttons on mobile, and ensure high contrast and clear typography. Ensure modal close buttons are easily tappable on small touch screens.

# Project Roadmap

## Archived Milestones
- [v1.0 MVP Delivery](milestones/v1.0-ROADMAP.md) - Implemented full asynchronous backend with HNSW/GIN indexing, robust mobile UI QR check-ins, and complex multi-campus CSP constraint scheduling.
- [v1.1 Production Hardening & Features](milestones/v1.1-ROADMAP.md) - Added security fixes, error boundaries, lazy-loading, PDF/CSV exports, visual analytics, and webcam face registration.

## Active Milestone (v2.0: Predictive Analytics)

### Phase 5.4: Google Colab Face Recognition Engine
- **Status:** Planning
- **Goal:** Offload computationally expensive face recognition tasks (dlib/face_recognition) to a Google Colab notebook API.
- **Scope:** Create a Google Colab notebook that runs a FastAPI server exposed via ngrok or localtunnel. Refactor the Django backend to send image encoding requests to this external Colab API instead of running it locally, bypassing Render's memory limits.

### Phase 5.5: Cloud-Native Face ID Check-in
- **Status:** Complete
- **Goal:** Refactor the attendance Face ID scanner to work over the web rather than relying on a local server webcam.
- **Scope:** Update the React frontend (`AttendancePage.jsx`) to capture webcam frames in the browser and POST them to the Django backend. Refactor the backend `TriggerFaceRecognitionView` to accept an image, use the Colab API for encoding, and match it against the pgvector database to mark attendance.

### Phase 5.6: Code Review Fixes for Face ID
- **Status:** Complete
- **Goal:** Implement the security and business logic fixes identified during the Phase 5.5 code review.
- **Scope:** Verify faculty authorization and student enrollment in `TriggerFaceRecognitionView`. Add camera permission error handling to the React frontend.

### Phase 6: Core Analytics & Predictive Modeling
- **Status:** Complete
- **Goal:** Develop backend aggregation endpoints and the predictive shortage algorithm.
- **Scope:** Django ORM aggregations for department/subject stats, and a linear trajectory model to flag students at risk of < 75% attendance.

### Phase 7: Analytics Dashboard UI
- **Status:** Complete
- **Goal:** Build the dedicated frontend interface for data visualization.
- **Scope:** New `/admin/analytics` route, extensive `recharts` integration (bar charts, area charts), and UI indicators for "At Risk" students on the Faculty dashboard.

### Phase 8: Proactive Warning System
- **Status:** Complete
- **Goal:** Automate the dispatch of warning emails.
- **Scope:** Django Q2 scheduled background tasks to run the predictive model weekly and trigger SMTP emails to flagged students.

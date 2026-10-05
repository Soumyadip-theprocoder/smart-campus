# Milestone Roadmap

### Phase 10: UI Rework & Real-World Hardening
- **Status:** Completed
- **Goal:** Rework the UI and harden existing features to ensure they are fully operational for real-world use.
- **Scope:** Fix fragile data filtering, improve error boundaries, ensure responsive design works across all devices, and make existing dashboards (Admin, Student, Faculty) robust.

### Phase 11: Core Stabilization & UX Polish
- **Status:** Completed
- **Goal:** Ensure core workflows (attendance, timetable, analytics) are reliable and user-friendly.
- **Scope:** Enhance error messaging for timetable generation, stabilize async task polling, fix any broken links/buttons, and implement a consistent design system (including Dark Mode).

### Phase 12: Timetable & Attendance Enhancements
- **Status:** Completed
- **Goal:** Add manual overrides for timetable and batch uploads for attendance.
- **Scope:** Drag-and-drop timetable management, specific class locking, and batch image uploads for fallback attendance.

### Phase 12.1: Dynamic & Feature-Rich Timetable
- **Status:** Completed
- **Goal:** Expand timetable flexibility, dynamism, and user experience.
- **Scope:** Dynamic institution hours, persistent subject colors, export to PDF, personalized filtering, and ad-hoc event scheduling.

### Phase 12.2: Operations & Sandbox Environment
- **Status:** Completed
- **Goal:** Provide safe drafting environments and real-time operational workflows.
- **Scope:** Sandbox versioning (Draft/Publish), Scenario comparisons & Rollback, Faculty Absence Reporting, Substitute Request Broadcasting, and Push Alerts.

### Phase 12.3: AI Scheduling & Advanced Swaps
- **Status:** Completed
- **Goal:** Introduce AI-assisted conflict resolution and fairness balancing.
- **Scope:** AI Smart Swaps, Safe Drop Zones, Natural Language commands, Swap Approval workflows, Faculty Fairness Balancer, and Office Hour auto-injection.

### Phase 12.4: Extended Modules & Sync
- **Status:** Completed
- **Goal:** Deliver specialized scheduling modes and external integrations.
- **Scope:** Academic Calendar Sync (Blackout dates), Exam & Invigilation Mode, and 1-Click Calendar Sync (iCal).

### Phase 12.5: Multi-Department Architecture
- **Status:** Completed
- **Goal:** Partition the timetable UI and AI generation by Department for massive scale.
- **Scope:** Department-specific hours/breaks, scoped AI generation, department selector UI, and Cross-Department Shared Electives.

### Phase 12.6: Resource Logistics & Accreditation Analytics
- **Status:** Completed
- **Goal:** Track physical inventory constraints and automate compliance reporting.
- **Scope:** Physical Equipment tracking (AI constraints), Student Accessibility Routing, and automated Accreditation Reporting (contact hours, lab ratios).

### Phase 12.7: Predictive Analytics & TA Logistics
- **Status:** Planned
- **Goal:** Predict future capacity needs and manage complex student-teacher roles.
- **Scope:** AI "What-If" Forecasting Simulations and Automated Teaching Assistant (TA) Rostering.

### Phase 12.8: Timetable Break Overhaul & Theme-Stable PDF Export
- **Status:** Implemented (pending manual UAT)
- **Goal:** Make timetable breaks dynamic and editable, and make PDF export theme-independent.
- **Scope:** Fix un-deselectable 1 PM break (remove gap heuristic), data-driven break rows, multi-break editor (discrete + continuous ranges) with persistence, backend honouring of breaks, and consistent light-palette PDF export.

### Phase 12.9: Flexible Department & Grouping System
- **Status:** Planned
- **Goal:** Add robust support for grouping students and teachers to facilitate inter-disciplinary classes and accurate department mapping.
- **Scope:** Create a flexible `AcademicGroup` model, migrate `Student` and `Faculty` `department` text fields to ForeignKeys referencing the `scheduler.Department` model, and provide UI to manage these associations.

### Phase 13: Advanced Analytics & Communication (Deferred)
- **Status:** Planned
- **Goal:** Provide granular filtering and expand notification methods.
- **Scope:** Date Pickers for custom ranges, SMS support, Rich Text notice creation.

### Phase 13.1: ML Predictive Analytics Service
- **Status:** Planned
- **Goal:** Implement the core ML model (Random Forest/DNN) to predict absenteeism risk based on historical attendance patterns.
- **Scope:** Data preprocessing, ML classification integration (scikit-learn/PyTorch), and backend GET endpoints.

### Phase 13.2: Asynchronous Alerting Engine
- **Status:** Planned
- **Goal:** Autonomously dispatch SMTP alerts to at-risk students without freezing the API.
- **Scope:** Django Q2 background tasks, AlertLog cooldown mechanism, and POST endpoints to trigger the job.

### Phase 13.3: UI Decision Support Dashboards
- **Status:** Planned
- **Goal:** Provide web-based interfaces for admins and students to consume the ML predictions.
- **Scope:** Admin Dashboard (view at-risk list, trigger alerts) and Student Dashboard (view personal risk warnings).

### Phase 14.1: EDM Engine - Grade Forecasting (Regression)
- **Status:** Done
- **Goal:** Predict final CGPA based on historical marks and attendance.
- **Scope:** Extend `master_dataset.csv`, evaluate SVR/RandomForest/LinearRegression, and serialize the best forecaster.

### Phase 14.2: EDM Engine - Student Profiling (Clustering)
- **Status:** Done
- **Goal:** Group students into behavioral clusters for targeted advising.
- **Scope:** Evaluate K-Means, DBScan, BIRCH, Gaussian Mixture, and Mean Shift. Validate using F-measure and Silhouette scores.

### Phase 14.3: Backend Integration & APIs
- **Status:** Done
- **Goal:** Expose the ML predictions to the Django frontend securely.
- **Scope:** Create GET endpoints `/api/attendance/forecast/<student_id>/` and `/api/analytics/student-clusters/`.

### Phase 14.4: UI Decision Support Dashboards
- **Status:** Done
- **Goal:** Render actionable visualizations of the new models.
- **Scope:** Add a CGPA Forecast gauge to the Student Dashboard and a Recharts scatter plot to the Admin Dashboard.

<details>
<summary>Archived Milestones</summary>

- **[v2.0 - Predictive Analytics & Remote AI capabilities](milestones/v2.0-ROADMAP.md)** - Completed 2026-09-25
- **[v1.0 - Core Foundation](milestones/v1.0-ROADMAP.md)** - Completed 2026-09-21
</details>

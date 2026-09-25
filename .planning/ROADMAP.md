# Project Roadmap

## Archived Milestones
- [v1.0 MVP Delivery](milestones/v1.0-ROADMAP.md) - Implemented full asynchronous backend with HNSW/GIN indexing, robust mobile UI QR check-ins, and complex multi-campus CSP constraint scheduling.
- [v1.1 Production Hardening & Features](milestones/v1.1-ROADMAP.md) - Added security fixes, error boundaries, lazy-loading, PDF/CSV exports, visual analytics, and webcam face registration.

## Active Milestone (v2.0: Predictive Analytics)

### Phase 5.1: Codebase & Documentation Polish
- **Status:** Complete
- **Goal:** Comprehensive cleanup of the backend codebase, removal of deprecated files, and polishing of project documentation to ensure a pristine state for the v2.0 milestone.
- **Scope:** Run linters/formatters, remove dead code/unused imports, verify `README.md` and architecture docs are up-to-date.

### Phase 5.2: UI Rewrite & Polish
- **Status:** Complete
- **Goal:** Comprehensive frontend rewrite to ensure maximum visual polish, responsiveness, and user-friendly interaction across all dashboards according to the `UI-SPEC.md`.
- **Scope:** Enhance `AdminDashboard` and `StudentDashboard` with glassmorphism, responsive `recharts` layouts, hover states, proper loading indicators, and graceful fallback behaviors. Ensure the webcam modal and PDF/CSV buttons are intuitively placed and aesthetically pleasing.

### Phase 6: Core Analytics & Predictive Modeling
- **Status:** Planned
- **Goal:** Develop backend aggregation endpoints and the predictive shortage algorithm.
- **Scope:** Django ORM aggregations for department/subject stats, and a linear trajectory model to flag students at risk of < 75% attendance.

### Phase 7: Analytics Dashboard UI
- **Status:** Planned
- **Goal:** Build the dedicated frontend interface for data visualization.
- **Scope:** New `/admin/analytics` route, extensive `recharts` integration (bar charts, area charts), and UI indicators for "At Risk" students on the Faculty dashboard.

### Phase 8: Proactive Warning System
- **Status:** Planned
- **Goal:** Automate the dispatch of warning emails.
- **Scope:** Django Q2 scheduled background tasks to run the predictive model weekly and trigger SMTP emails to flagged students.

# Project Roadmap

## Archived Milestones
- [v1.0 MVP Delivery](milestones/v1.0-ROADMAP.md) - Implemented full asynchronous backend with HNSW/GIN indexing, robust mobile UI QR check-ins, and complex multi-campus CSP constraint scheduling.
- [v1.1 Production Hardening & Features](milestones/v1.1-ROADMAP.md) - Added security fixes, error boundaries, lazy-loading, PDF/CSV exports, visual analytics, and webcam face registration.

## Active Milestone (v2.0: Predictive Analytics)



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

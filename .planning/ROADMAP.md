# Project Roadmap

## Archived Milestones
- [v1.0 MVP Delivery](milestones/v1.0-ROADMAP.md) - Implemented full asynchronous backend with HNSW/GIN indexing, robust mobile UI QR check-ins, and complex multi-campus CSP constraint scheduling.
## Active Milestone (v1.1)

### Phase 4: Production Hardening & Post-Review Fixes
- **Status:** Planned
- **Goal:** Address all security vulnerabilities, optimize frontend bundles, and implement project polish.
- **Scope:** API key auth for Face Engine, disable open registration, code splitting (React.lazy), error boundaries, and fixing Django Q2 config.

### Phase 5: PDF Feature Parity (Face Data Registration & Data Visualization)
- **Status:** Planned
- **Goal:** Implement the missing features from the project proposal PDF.
- **Scope:**
  - **Face Data Registration:** Web-based UI to capture student facial images via webcam during initial setup, extracting encodings on the backend and storing them in the DB.
  - **Data Visualization & Reporting:** Visual analytics dashboard (attendance stats, class schedules) with the ability to download or export reports for administrative purposes.

# Milestone Roadmap

### Phase 10: Overall UI/UX Polish (Dark Mode & Mobile)
- **Status:** Planned
- **Goal:** Implement system-wide Dark Mode and improve mobile responsiveness.
- **Scope:** Create a theme context for Dark/Light mode. Refactor complex data tables in Admin and Faculty dashboards to stack nicely on mobile screens. Add ARIA labels for accessibility.

### Phase 11: Timetable Enhancements (Drag-and-Drop)
- **Status:** Planned
- **Goal:** Allow manual overrides of the generated timetable.
- **Scope:** Introduce `react-beautiful-dnd` or similar to `ManageTimetablePage`. Update the backend to accept manual updates to timetable entries and allow "locking" of specific blocks before the solver runs.

### Phase 12: Communication & Rich Text
- **Status:** Planned
- **Goal:** Enhance how notices and alerts are sent out.
- **Scope:** Integrate `react-quill` for the Notice creation form. Hook up a mock SMS provider (or Twilio sandbox) in the Django backend. Design and implement HTML email templates for attendance warnings.

### Phase 13: Advanced Analytics & Dashboards
- **Status:** Planned
- **Goal:** Provide granular filtering for the Admin Dashboard.
- **Scope:** Add Date Pickers for custom ranges. Implement filtering by Department/Semester on the frontend and wire these up as query parameters to the analytics backend endpoints.

### Phase 14: Attendance History & Batch Upload
- **Status:** Planned
- **Goal:** Expand attendance capabilities.
- **Scope:** Create a new route for students to view day-by-day attendance history. Add a fallback to upload multiple images at once for batch attendance processing in case of webcam failure.

<details>
<summary>Archived Milestones</summary>

- **[v2.0 - Predictive Analytics & Remote AI capabilities](milestones/v2.0-ROADMAP.md)** - Completed 2026-09-25
- **[v1.0 - Core Foundation](milestones/v1.0-ROADMAP.md)** - Completed 2026-09-21
</details>

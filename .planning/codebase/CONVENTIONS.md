# Codebase Conventions

## Frontend Conventions

### CSS & Styling
- **Avoid Inline Styles:** All structural layout rules must be placed in `index.css`. Inline styles should only be used for dynamically calculated values (e.g., chart heights, absolute positioning logic).
- **Responsive Tables:** Do not write separate Mobile UI components for tables. Use `<table className="data-table">` and attach `data-label` to every `<td>`. `index.css` handles the automatic transformation into mobile cards.
- **Glassmorphism:** Use `.glass-card` for container elements. Do not manually declare background blurs on generic divs.

### React State Management
- **Async Polling / Subscriptions:** Any component that executes an async `setTimeout` or `setInterval` polling loop (like checking timetable task status) **must** utilize a `useRef(true)` cleanup guard to prevent unmounted component state updates.
- **Error Boundaries:** Use `<LocalErrorBoundary>` around any complex third-party visual component (e.g., Recharts) to prevent dashboard-wide crashes.

## Backend Conventions

### Models & Serializers
- **Profiles:** Never attach arbitrary student/faculty fields directly to the `User` model. Always use the 1-to-1 `StudentProfile` and `FacultyProfile` models.
- **Vectors:** Face encodings must be stored using `pgvector` VectorFields, not binary blobs, to allow for HNSW indexing in production.

### Performance
- **Heavy Workloads:** Do not execute computationally intensive tasks (like CSP Solvers or Machine Learning) synchronously within DRF views. Dispatch them to `django-q2` using `.async_task()`.

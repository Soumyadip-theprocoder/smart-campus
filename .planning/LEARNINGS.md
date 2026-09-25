# Project Learnings & Discoveries

## 1. Key Architectural Decisions
- **Face Recognition Database:** We adopted `pgvector` with HNSW indexing in PostgreSQL for storing and querying 128-dimensional face encoding vectors. This significantly improves search speed over traditional scalar distance calculations.
- **Timetable Scheduling Algorithm:** We utilized a Constraint Satisfaction Problem (CSP) solver implementing the Minimum Remaining Values (MRV) heuristic and forward checking, efficiently handling complex multi-campus building transits and elective overlaps.
- **Asynchronous Task Processing:** We integrated `django-q2` for background processing. The CSP timetable generation is CPU-intensive, so offloading it prevents HTTP timeouts.
- **Face Engine Authentication:** We decided to use a **Static Shared API Key** rather than JWTs for the automated Python face recognition script. This eliminates the operational overhead of managing short-lived token expirations for non-human services.
- **Webcam Registration Flow:** We decided to process initial webcam face encodings **synchronously** during the API request rather than via background workers, as processing a single image is fast enough for the request lifecycle.

## 2. Lessons Learned (Gotchas & Fixes)
- **Render Background Workers:** Deploying `django-q2` on a Render "Web Service" requires a custom `start.sh` script to boot both `gunicorn` and the `qcluster` worker simultaneously, since Render only executes one `startCommand`.
- **SPA Routing on Render Static Sites:** A React SPA deployed to Render Static will throw 404 errors on browser refresh unless a rewrite rule (`/*` -> `/index.html`) is explicitly added in the Render dashboard.
- **Fragile Data Filtering:** Filtering timetables by a concatenated `faculty_name` string in React is extremely fragile and error-prone. Relational lookups must always rely on unique primary keys (`faculty_id`).
- **Security Defaults:** Setting permissive defaults (`AllowAny` or `IsAuthenticated` without role checks) for endpoints like `RegisterView` or `StudentListView` easily leads to exposed PII and privilege escalation. Explicit `IsAdminUser` checks must be enforced.
- **Bundle Optimization:** Un-split React applications grow very quickly (e.g., >700KB). Implementing `React.lazy()` with `<Suspense>` is a necessary early step for feature-heavy dashboards.

## 3. Recurring Patterns Discovered
- **Task Polling Pattern:** When the backend triggers an asynchronous task, the frontend should immediately receive a `task_id`. The React components (e.g., `TimetablePage`) then use a `setInterval` polling loop against a `/status/` endpoint to display loading states until the task completes.
- **Role-Based Protected Routes:** The `<ProtectedRoute allowedRoles={['admin', 'faculty']}>` wrapper pattern in React Router provides an incredibly clean and scalable way to restrict frontend access.

## 4. Surprises Encountered
- **Buried PDF Requirements:** Essential features (Webcam registration UI and Data Exporting) were present in the initial academic PDF proposal but were easily overlooked when decomposing the technical MVP, requiring a retroactive "Phase 5" to achieve feature parity.
- **Silent Misconfigurations:** The initial `SECRET_KEY` implementation had an insecure default fallback. In production, this can silently compromise the entire application without throwing an error. We learned to enforce `ImproperlyConfigured` exceptions for critical missing environment variables.
- **Python Imports in Loops:** An `import random` statement was initially found inside a CSP domain-building loop during Phase 4 code review. This was fixed by moving the import to module level (`csp_solver.py` line 19). While Python caches imports, the discovery highlighted the need for stricter code reviews regarding loop optimization.

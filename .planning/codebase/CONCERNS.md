# Codebase Concerns & Technical Debt

## Security
- **Open Endpoints:** `RegisterView` and `MarkAttendanceView` currently lack proper restriction in the active codebase (addressed in Phase 4).
- **Missing API Keys:** Face engine relies on permissive open routes rather than static API keys.
- **Hardcoded Secrets:** `seed_data.py` contains hardcoded passwords (`admin123`). This should be driven by environment variables.
- **Rate Limiting:** Login endpoints lack throttling, leaving them vulnerable to brute-force attacks.

## Performance & Optimization
- **Frontend Bundle Size:** The React Vite build outputs a massive >736KB bundle chunk, indicating a need for `React.lazy` code splitting at the router level.
- **Loop Imports:** `import random` is executed inside a heavy domain-building loop in `csp_solver.py`, which is poor practice.
- **String Matching Queries:** Filtering timetables on the frontend using concatenated names (`first_name` + `last_name`) is extremely fragile. It must be refactored to use robust primary keys (`faculty_id`).

## Deployment
- **HTTPS Enforcement:** Missing `SECURE_SSL_REDIRECT` in Django settings for production.
- **Django Q2 Config:** Missing `retry` configuration in `Q_CLUSTER` leads to startup warnings.

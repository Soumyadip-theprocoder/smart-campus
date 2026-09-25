# Testing Documentation

This document explains the testing strategy and setup for the Smart Campus Management System. The project has a robust testing suite for the backend application written using the Django `TestCase` framework and Django REST Framework `APIClient`.

## Overview

The backend has 48+ comprehensive test cases categorized by app to ensure model integrity, API availability, role-based access control, and edge-case resilience.

- **`accounts/tests.py`** — Auth, JWT, Registration, Profile
- **`attendance/tests.py`** — Face Recognition Engine fallback, marking logic, threshold analysis
- **`scheduler/tests.py`** — Constraint Satisfaction Problem (CSP) solver unit tests
- **`communication/tests.py`** — Notice boards, alert triggering logic

## Running Tests

### Local Execution (Standard)

By default, testing the `accounts`, `attendance`, and `communication` apps requires PostgreSQL with the `pgvector` extension running (because `accounts.models.Student` uses `VectorField` and `HnswIndex`).

To run the entire test suite:
```bash
cd backend
python manage.py test
```

To run a specific app's tests:
```bash
# Test only the CSP scheduler (No DB dependencies)
python manage.py test apps.scheduler

# Test the auth logic
python manage.py test apps.accounts
```

To run a specific test class or method:
```bash
python manage.py test apps.accounts.tests.RobustnessAccountsTests
python manage.py test apps.accounts.tests.RobustnessAccountsTests.test_register_invalid_role
```

### Continuous Integration (CI) / Render 

If running on a deployment pipeline like Render, make sure the `DATABASE_URL` environment variable points to a PostgreSQL instance with pgvector initialized before running:

```yaml
# Example render.yaml build command modification:
buildCommand: "pip install -r requirements.txt && python manage.py test && ./build.sh"
```

## Testing Philosophy

### 1. Robustness and Boundary Checks
Each app includes a `Robustness*Tests` suite that specifically attempts to break the application with malformed data.
- **Example:** Submitting 300-character long strings to the registration endpoint.
- **Example:** Student accounts attempting to create admin notices (testing `401 Unauthorized`/`403 Forbidden`).
- **Example:** Providing invalid enum choices to the `MarkAttendanceView` (like `method='magic'`).

### 2. Idempotency 
Tests are designed so that running an action multiple times yields consistent results. 
- **Example:** Marking attendance for the same student, on the same subject, on the same day twice returns a `200 OK` rather than duplicating rows or throwing a `500 Server Error`.

### 3. Algorithm Resilience (`scheduler/tests.py`)
The CSP Timetable Solver is heavily tested for constraint violations. The solver uses Backtracking + MRV (Minimum Remaining Values) heuristic + Forward Checking.
- Tests verify it doesn't double-book a room at the same time.
- Tests verify a professor isn't assigned to two different classes simultaneously.
- **Edge cases covered:** Zero rooms available, zero slots, unsatisfiable constraints (it returns an empty schedule instead of raising exceptions).

### 4. UI & Export Workflows (v1.1+)
- **PDF/CSV Generation:** The backend uses `reportlab` to generate PDF binary streams directly into the HTTP response. Testing involves asserting the `Content-Type: application/pdf` header is present.
- **Webcam Registration:** Because `face_recognition` is disabled in Render production environments to save RAM, testing the webcam registration flow requires a local development setup with C++ tools installed (`cmake`, `dlib`). Production gracefully degrades by returning `501 Not Implemented`.

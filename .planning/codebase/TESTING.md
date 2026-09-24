# Testing Overview

## Current Status
Testing is currently minimal (rated 1-star in the initial Project Review). Test infrastructure exists, but coverage is sparse.

## Existing Tests
- `backend/test_login.py`: Verifies JWT authentication flows.
- `backend/test_generate.py`: Basic test scaffold for the timetable generator.

## Testing Needs (Phase 4 & Phase 5)
- **Security Tests:** Unit tests needed to verify permission guards (`HasFaceEngineAPIKey`, `IsAdminUser`) properly block unauthorized access to endpoints like `MarkAttendanceView` and `RegisterView`.
- **Algorithm Tests:** Comprehensive unit tests are needed for the `csp_solver.py` edge cases.
- **Component Tests:** Frontend error boundary components and toast notifications need regression verification.

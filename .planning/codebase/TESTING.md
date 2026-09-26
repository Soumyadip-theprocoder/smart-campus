# Testing Philosophy & Guidelines

## Frontend Testing
- **Visual Validation:** The primary methodology for frontend validation is User Acceptance Testing (UAT) paired with artifact generation via `generate_image` or DOM snapshots. 
- **Error Boundary Testing:** We explicitly verify that `LocalErrorBoundary` components catch crashes by injecting deliberate runtime errors into chart components during test phases.
- **Responsiveness Check:** Mobile behavior (`<768px`) is validated by verifying that CSS media queries correctly trigger the card-based layout for data tables.

## Backend Testing
- **Algorithm Verification:** The Timetable Generator (CSP Solver) is tested against constraint satisfaction constraints to ensure zero overlapping classes.
- **Background Tasks:** Q2 tasks must be verified by inspecting worker logs and database state mutation after the task completes.
- **Mock Interfaces:** Hardware-dependent workflows (like webcam capture) gracefully fallback to mock data injection APIs if hardware access is unavailable in the environment.

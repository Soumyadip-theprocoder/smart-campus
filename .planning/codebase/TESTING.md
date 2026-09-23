# Testing

## Overview
Currently, the codebase does not appear to have an extensive automated testing suite defined (no prominent `tests/` directories or specific test requirements like `pytest` explicitly listed).

## Recommendations
- **Backend**: Implement Django's built-in `TestCase` or integrate `pytest-django` to test API endpoints, CSP solver correctness, and JWT authentication.
- **Frontend**: Integrate `Vitest` and `React Testing Library` to test component rendering and context state.
- **Computer Vision**: Unit test the face encoding and matching logic with static mock images to ensure accuracy without requiring a live webcam.

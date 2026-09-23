# Codebase Structure

## Root Workspace
- `frontend/`: React SPA source code.
- `backend/`: Django API source code and computer vision scripts.

## Backend (`backend/`)
- `manage.py`: Django CLI entry point.
- `requirements.txt`: Python dependencies.
- `seed_data.py`: Script to populate the database with demo users.
- `config/`: Django project settings, root `urls.py`, and WSGI/ASGI configurations.
- `apps/`: Django modular applications.
  - `accounts/`: User authentication, roles, and profile models.
  - `attendance/`: Attendance tracking, reports, and API views.
  - `scheduler/`: CSP solver and timetable management.
  - `communication/`: Notices, alerts, and SMTP integrations.
- `face_recognition_engine/`: Dedicated computer vision scripts.
  - `encode_faces.py`: Script to process images and store encodings in DB.
  - `recognize_faces.py`: Script to run webcam recognition and hit the API.
  - `training_images/`: Directory containing student photos organized by ID.

## Frontend (`frontend/`)
- `src/`
  - `api/`: Axios configuration and API client abstractions.
  - `assets/`: Static files (images, icons).
  - `components/`: Reusable UI components (buttons, modals, layout).
  - `context/`: React Context providers (AuthContext).
  - `features/`: Page-level components organized by domain (e.g., dashboard, attendance).
  - `App.jsx`, `main.jsx`: React entry points and routing definitions.
  - `index.css`: Global styles.
- `package.json`: NPM dependencies and Vite scripts.
- `vite.config.js`: Vite build configuration.

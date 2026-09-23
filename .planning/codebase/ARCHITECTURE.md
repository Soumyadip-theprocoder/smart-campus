# Architecture

## High-Level System Architecture
The Smart Campus Management System uses a decoupled **Client-Server Architecture**.

### 1. Presentation Layer (Vite React Frontend)
- A Single Page Application (SPA) running on port `5173`.
- Communicates with the backend exclusively via REST APIs using Axios.
- Maintains authentication state via JWT tokens (likely stored in context/local storage).
- Separates features logically (`features/`, `components/`, `context/`).

### 2. Application Layer (Django API)
- Serves RESTful endpoints on port `8000`.
- **Authentication**: JWT token issuance and validation.
- **Apps**:
  - `accounts`: Manages users (Admin, Student, Faculty) and roles.
  - `attendance`: API endpoints for marking and querying attendance.
  - `scheduler`: API and constraint logic for timetable generation.
  - `communication`: Notice board and SMTP alert dispatch.

### 3. Background Services & Algorithms
- **Face Recognition Engine**: A dedicated Python subsystem (`backend/face_recognition_engine/`) running alongside Django. It handles training (encoding) and real-time live recognition (webcam capture), submitting results to the API.
- **CSP Solver (`csp_solver.py`)**: A Backtracking Constraint Satisfaction Problem algorithm with MRV heuristic used by the `scheduler` app to generate conflict-free timetables.

### 4. Data Layer
- **Relational DB**: Stores structured data (Users, Students, Subjects, Rooms, Timetable entries, Notices).
- **Blob/JSON Storage**: `face_encoding` data is stored as JSON arrays in the `students` table.

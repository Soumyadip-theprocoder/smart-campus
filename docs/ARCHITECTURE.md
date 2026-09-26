# Smart Campus Architecture

## High-Level System Design

The Smart Campus Management System is a modern, modular web application utilizing a decoupled architecture:
- **Frontend:** React (Vite)
- **Backend:** Django & Django REST Framework (DRF)
- **Database:** PostgreSQL (with `pgvector` for Face ID matching) or SQLite (fallback for local dev)
- **Background Tasks:** Django Q2 (for async tasks like timetable generation and predictive modeling)

```mermaid
graph TD
    UI[React Frontend (Vite)] -->|REST API (JWT)| API[Django Backend API]
    API --> DB[(PostgreSQL + pgvector)]
    API --> Q2[Django Q2 Task Queue]
    Q2 --> Worker[Background Workers]
    Worker --> DB
    
    UI -->|Face Capture| Camera[Webcam API]
    Camera -->|Base64 Image| API
    API -->|Face Encoding| ML[Face Recognition Engine]
    ML -->|Vector| DB
```

## Core Modules

### 1. Authentication & Identity (`apps/accounts`)
- Implements custom `User` model, extending Django's `AbstractUser`.
- Segregated profiles: `StudentProfile` and `FacultyProfile`.
- Uses `djangorestframework-simplejwt` for secure, stateless token-based authentication.

### 2. Face ID & Attendance (`apps/attendance`)
- Replaces traditional roll calls with biometric verification.
- Uses `dlib` CNN and `face_recognition` to extract 128-dimensional encodings.
- Vectors are stored in PostgreSQL using `pgvector`.
- Distance matching (L2 distance) is optimized using **HNSW (Hierarchical Navigable Small World) Indexes**.

### 3. Asynchronous Timetable Scheduler (`apps/scheduler`)
- A Constraint Satisfaction Problem (CSP) solver built with Backtracking and Forward Checking.
- Due to computational intensity (O(n!)), the solver is offloaded to a **Django Q2** background worker.
- The frontend asynchronously polls the backend via `/api/scheduler/task-status/{task_id}/` for real-time progress updates.

### 4. Predictive Analytics (`apps/analytics`)
- Aggregates attendance data to predict student absenteeism using linear trajectory modeling.
- Identifies "At-Risk" students (falling below 75% attendance).
- Automated weekly jobs in Django Q2 scan for at-risk students and trigger SMTP email alerts.

### 5. Frontend Ecosystem
- **State Management:** React Context API (`AuthContext`, `ThemeContext`).
- **Performance:** `React.lazy` and `Suspense` are used for route-level code splitting, significantly reducing the initial bundle size (especially for heavy libraries like `recharts`).
- **Resilience:** Implements nested `LocalErrorBoundary` components to catch runtime crashes in isolated components (like charts) without bringing down the entire dashboard.
- **Styling:** Vanilla CSS with robust Glassmorphism tokens (`index.css`), natively responsive grid systems (`.grid-2`, `.grid-4`), and dynamic Dark Mode support.

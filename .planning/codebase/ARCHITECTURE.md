# Architecture & System Design

The Smart Campus system follows a classic decoupled client-server architecture with heavy asynchronous background processing for intensive workloads.

## High-Level Architecture
1. **Frontend (Client):** A Single Page Application (SPA) built with React and Vite. It communicates with the backend exclusively via REST JSON APIs secured by JWT access tokens.
2. **Backend (API Server):** A monolithic Django + DRF application. It handles request validation, database transactions, and dispatching ML tasks.
3. **Background Worker Cluster:** A `django-q2` cluster running parallel to the API server.
4. **Data Persistence:** PostgreSQL is utilized as the persistent data store.

## Core Workflows

### 1. Facial Recognition Authentication Flow
1. User requests to log in via Face ID on the frontend.
2. `react-webcam` captures a base64 frame.
3. The frame is sent via `POST` to the backend.
4. The `face_recognition_engine` uses `dlib` to locate the face and extract a 128-d vector.
5. The backend queries PostgreSQL `pgvector` HNSW index for the nearest matching profile.
6. If the L2 distance is within the confidence threshold, a JWT is issued.

### 2. Timetable Generation (Asynchronous CSP)
1. Admin triggers timetable generation.
2. API responds immediately with a `task_id`.
3. `django-q2` worker picks up the task and runs the Backtracking solver against the Subjects and Rooms tables.
4. The Frontend polls `/api/scheduler/task-status/{task_id}/` recursively utilizing a protected `useRef` mounted state guard to prevent memory leaks if the user navigates away mid-poll.
5. Upon completion, the frontend renders the weekly grid.

### 3. Responsive UI Layer
- All global structural styles are housed in `index.css`.
- `.data-table` dynamically reflows into a card-based layout on viewports `<768px` by mapping `data-label` attributes to CSS pseudo-elements (`::before`), guaranteeing complete mobile responsiveness without relying on JS breakpoints.
- Dark and Light mode is managed globally by `ThemeContext`.

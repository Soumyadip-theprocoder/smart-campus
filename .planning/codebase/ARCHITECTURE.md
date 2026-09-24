# Architecture

## Core Architectural Patterns
The application follows a decoupled Client-Server architecture. 

### 1. Feature-Sliced Frontend
The React application is organized by features rather than file types (e.g., separating by `attendance`, `dashboard`, `scheduler`). This encapsulation makes it easier to scale domains.
- **Role-Based Access:** React Router is wrapped with a `<ProtectedRoute>` component that inspects the JWT payload to ensure users only access their designated UI (Admin, Faculty, Student).
- **Polling Pattern:** For async backend operations (like Timetable generation), the UI uses `setInterval` to poll a `/status/` endpoint until completion.

### 2. App-Based Backend
Django is structured into highly cohesive apps:
- `accounts`: Handles Custom User models, JWT auth, and Student/Faculty profiles.
- `attendance`: Handles face engine APIs, QR fallback, and attendance records.
- `scheduler`: Handles rooms, subjects, timetable generation, and the core CSP algorithm.
- `communication`: Handles notices and email alerts.

### 3. Background Processing
The `scheduler` domain is too heavy for standard HTTP request lifecycles. 
- A `django-q2` worker queue (`qcluster`) runs continuously in the background alongside the `gunicorn` web server.
- The web server offloads timetable generation to the queue and returns a `task_id`.

### 4. Vector Database Recognition
Instead of looping through all face embeddings in Python memory, the architecture delegates distance calculations to the PostgreSQL database engine using `pgvector` with HNSW indices, allowing extremely fast nearest-neighbor lookups.

# Deployment & Worker Guide

## Architecture Topology
The application relies on 3 main long-running processes in production:
1. **Frontend Server:** Serves the Vite React bundle (or NGINX serving static files).
2. **Backend API Server:** Gunicorn/Uvicorn running the Django ASGI/WSGI application.
3. **Django Q2 Cluster:** A fleet of asynchronous background workers that process CPU-heavy tasks.

## Background Workers (Django Q2)
Due to Render's strict timeout limits (30-60 seconds for HTTP requests), the Smart Campus system aggressively offloads heavy workloads to `django-q2`.

### Offloaded Tasks
- `generate_timetable_task`: Runs the Backtracking CSP Solver to schedule hundreds of classes without blocking the API.
- `predict_attendance_shortages`: A periodic CRON job that analyzes DB matrices and flags students.
- `dispatch_smtp_alerts`: Bulks sends alert emails asynchronously to prevent blocking.

### Running Workers Locally
To process background tasks during development, you must run the Q cluster in a separate terminal:
```bash
cd backend
python manage.py qcluster
```

## Running the Complete Stack

**Terminal 1 (Backend API):**
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 (Background Workers):**
```bash
cd backend
python manage.py qcluster
```

**Terminal 3 (Frontend):**
```bash
cd frontend
npm run dev
```

## Production Deployment (Render)
1. **Web Service (Backend):** Configure a Python Web Service. Start command: `gunicorn config.wsgi:application`.
2. **Background Worker:** Configure a Background Worker service. Start command: `python manage.py qcluster`. (Requires a connected Redis instance).
3. **Static Site (Frontend):** Configure a Static Site. Build command: `npm run build`. Publish directory: `dist`.

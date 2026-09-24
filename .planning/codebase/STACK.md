# Tech Stack

## Frontend
- **Framework:** React 18
- **Build Tool:** Vite 5
- **Routing:** React Router v7
- **Styling:** Vanilla CSS (Glassmorphism design aesthetic)
- **HTTP Client:** Axios (with interceptors for JWT)
- **Icons:** React Icons
- **QR Code:** `html5-qrcode` (scanning), `qrcode.react` (generation)

## Backend
- **Framework:** Django 4.2
- **API Framework:** Django Rest Framework (DRF)
- **Authentication:** `djangorestframework-simplejwt`
- **Background Tasks:** `django-q2` (for CSP scheduler and async operations)
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Vector Search:** `pgvector` (HNSW indexing for face embeddings)

## AI / Engines
- **Face Engine:** OpenCV & `face_recognition` (Python)
- **Algorithm:** Constraint Satisfaction Problem (CSP) Solver with Minimum Remaining Values (MRV) and Forward Checking.

## Infrastructure
- **Deployment Platform:** Render (Web Service for backend, Static Site for frontend)
- **Concurrency:** `start.sh` orchestrates Gunicorn and `qcluster` concurrently.

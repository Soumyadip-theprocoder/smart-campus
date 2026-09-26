# Tech Stack

## Frontend Ecosystem
- **Core Framework:** React 18 (Client-side rendered).
- **Build Tooling:** Vite (ESBuild based).
- **Routing:** React Router v7 (`BrowserRouter` with `lazy()` + `Suspense`).
- **Styling:** Vanilla CSS 3 with custom CSS variable design system (`index.css`), natively responsive via Flexbox and Grid.
- **Charts:** Recharts (AreaChart, PieChart).
- **Device APIs:** `react-webcam` (for face capture), `html5-qrcode` (for QR code attendance).
- **Notifications:** `react-hot-toast` for global toast alerts.
- **Icons:** `react-icons` (Heroicons `HiOutline*`).

## Backend Ecosystem
- **Core Framework:** Django 4.2.
- **API Layer:** Django REST Framework (DRF).
- **Authentication:** `djangorestframework-simplejwt` for secure JSON Web Tokens.
- **Asynchronous Tasks:** `django-q2` for background queue processing (Timetable Generation, Email Alerts).
- **Machine Learning / Computer Vision:** `dlib`, `face_recognition`, and `OpenCV` (`cv2`) for local deep metric learning and 128-d face encodings.
- **Database:** PostgreSQL (Production) / SQLite3 (Local fallback).
- **Vector Search:** `pgvector` extension for PostgreSQL to perform HNSW exact nearest-neighbor search for face matching.
- **Mailing:** Django built-in SMTP backend (`django.core.mail`).

## Monorepo Tooling
- **Package Manager:** `npm` (Frontend), `pip` + `venv` (Backend).
- **Linting:** ESLint (Frontend).

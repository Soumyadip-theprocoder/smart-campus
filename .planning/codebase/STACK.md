# STACK

## Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM (v7)
- **Styling/UI**: Custom CSS/Tailwind (implied), React Icons, Recharts (for charts), React Webcam (for face capture), HTML5-QRCode (for QR scanning), React Hot Toast (for notifications)
- **Drag & Drop**: @dnd-kit/core

## Backend
- **Framework**: Django 4.2+, Django REST Framework
- **Authentication**: djangorestframework-simplejwt (JWT)
- **Database ORM**: Django ORM with dj-database-url

## Database
- **Primary Database**: PostgreSQL (configured via Docker)
- **Vector Extension**: pgvector (for face embeddings)

## Services & Tasks
- **Background Tasks**: django-q2
- **Image Processing**: OpenCV, Pillow (face-recognition/dlib disabled for production/Render due to memory limits)
- **Calendar Sync**: icalendar (for .ics feed generation)

## Deployment
- **Containerization**: Docker & Docker Compose
- **Production Server**: Gunicorn, Whitenoise (for static files)
- **Platform**: Render (render.yaml is present)

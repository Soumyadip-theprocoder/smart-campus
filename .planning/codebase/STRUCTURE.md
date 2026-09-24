# Directory Structure

```text
smart-campus/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # User auth, JWT, Profiles
│   │   ├── attendance/        # Face/QR attendance, API
│   │   ├── communication/     # Notices, emails
│   │   └── scheduler/         # CSP Algorithm, Rooms, Subjects
│   ├── config/                # Django settings, WSGI/ASGI
│   ├── face_recognition_engine/ # OpenCV encoding/matching scripts
│   ├── manage.py
│   ├── render.yaml            # Render IaC config
│   ├── requirements.txt
│   ├── seed_data.py           # DB populator
│   └── start.sh               # Dual-boot script for Web + Worker
└── frontend/
    ├── package.json
    ├── public/
    └── src/
        ├── App.jsx            # Main Router
        ├── components/        # Reusable UI (Navbar, Sidebar, StatCard)
        ├── context/           # Global AuthContext
        ├── features/          # Domain logic
        │   ├── attendance/    # QR Scanner/Generator, Attendance Views
        │   ├── auth/          # LoginPage
        │   ├── communication/ # Notice boards
        │   ├── dashboard/     # Role-specific dashboard views
        │   └── scheduler/     # Timetable management, subjects, rooms
        └── main.jsx
```

# Third-Party Integrations

## Core Dependencies
1. **django-q2:** Used extensively for managing the asynchronous task queue. Essential for running the heavy `generate_timetable` Backtracking CSP solver and the `predict_attendance_shortages` predictive algorithm in the background without blocking the main DRF thread.
2. **djangorestframework-simplejwt:** Issues JSON Web Tokens (JWT) for stateless authentication.
3. **pgvector:** PostgreSQL extension used to store 128-dimensional face encodings. Allows for extremely fast exact nearest-neighbor search during face-recognition logins.
4. **dlib / face_recognition:** Core ML libraries providing the pre-trained Convolutional Neural Networks (CNNs) used to detect bounding boxes and extract feature vectors from webcam snapshots.
5. **Recharts:** Used in the frontend Admin and Student dashboards to render predictive analytics and attendance pies. Loaded asynchronously via `React.lazy()` to reduce initial bundle size.

## External Services
1. **SMTP Provider (e.g. Gmail / SendGrid):** Integrated via Django's `core.mail` module. The Q2 worker dispatches automated shortage warning emails to students through this service.

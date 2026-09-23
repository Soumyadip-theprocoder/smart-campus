# Integrations & Dependencies

## External Systems
- **SMTP Provider**: Used for automated email alerts (Attendance shortages, new notices). Configurable via environment variables (Gmail, Outlook, SendGrid).

## Core Libraries
- **`face_recognition`**: Heavily relies on dlib's CNN model for 128-d face encoding and matching.
- **OpenCV (`cv2`)**: Used for real-time webcam frame processing in the attendance engine.
- **`dj-database-url`**: Parses connection URLs for PostgreSQL integration.
- **`whitenoise`**: Serves static files in production.

## Infrastructure
- **Render**: The live application is deployed on Render (`render.yaml` exists in the backend).
- **PostgreSQL**: Production relational database, handled via Django ORM.

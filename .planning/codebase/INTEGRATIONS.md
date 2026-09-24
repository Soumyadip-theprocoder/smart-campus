# Integrations

## 1. Face Recognition Engine
- **Type:** Local Python Script / Library
- **Integration Point:** `backend/face_recognition_engine/`
- **Mechanism:** The backend invokes `encode_faces.py` and `recognize_faces.py` functions natively. 
- **Future Integration (Phase 5):** The engine will be invoked synchronously during a `POST` request from the web UI to process webcam images.
- **Authentication:** Static Shared API Key (`FACE_ENGINE_API_KEY`) used when automated scripts push data to the API.

## 2. PostgreSQL `pgvector`
- **Type:** Database Extension
- **Integration Point:** `Student.face_encoding` model field.
- **Mechanism:** Uses HNSW (Hierarchical Navigable Small World) index to compute vector distances for face matching.

## 3. Email / SMTP Service
- **Type:** External Mail Server
- **Integration Point:** `backend/apps/communication/views.py` (e.g., `SendAttendanceAlertsView`).
- **Mechanism:** Standard Django `send_mail` functionality to trigger mass alerts.

## 4. Render Platform
- **Type:** PaaS Deployment
- **Integration Point:** `backend/render.yaml` and `backend/start.sh`.
- **Mechanism:** IaC (Infrastructure as Code) file dictates the build and start commands for the backend and background workers.

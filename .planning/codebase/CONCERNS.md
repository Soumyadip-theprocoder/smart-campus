# Concerns

## Technical Debt & Scalability
- **Face Recognition Performance**: `face_recognition` library uses dlib. If the server scales to thousands of students, 128-d vector matching in a single Python process could become a bottleneck. Caching or specialized vector DBs (e.g., pgvector, Milvus) might be needed.
- **Webcam Integration**: The `recognize_faces.py` script requires physical hardware access. Deploying this on a cloud server means the client needs to stream video or send images to the backend. Currently, it seems designed to run locally or on an edge device (e.g., a Raspberry Pi in a classroom).
- **CSP Solver Blocking**: Constraint Satisfaction generation is NP-hard. For a large campus, the `POST /api/scheduler/generate/` endpoint might time out if it runs synchronously. It should likely be moved to a background task runner (like Celery or Django Q).
- **SQLite vs PostgreSQL**: README mentions PostgreSQL, but SQLite is the default. Migrating to PostgreSQL is critical for production deployment (Render) to prevent data loss.

## Security
- **Email Credentials**: Relies on `.env` for SMTP credentials. Ensure these are never committed and appropriately managed in cloud environments.
- **Face Data Privacy**: Encoded facial vectors are biometric data. Proper encryption and access control (GDPR/compliance) should be considered.

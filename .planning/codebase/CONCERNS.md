# CONCERNS

## Technical Debt & Risks
1. **Memory Limits for Face Recognition**: The `face-recognition` (dlib) dependency requires significant RAM (8GB+ to compile). It is currently disabled for Render production due to these constraints. An OpenCV headless alternative is used, which may have lower accuracy.
2. **Environment Configuration**: Secrets and `.env` files must be carefully managed. The `backend/.env.example` should be the only commited file.
3. **Database Migrations**: When deploying to production with `pgvector`, the extension must be successfully created on the target database, which requires superuser privileges or a managed service that supports it natively.
4. **Recent Database Connectivity**: Phase 12.6 reported a "Database server was unreachable" issue, meaning some migrations might be pending and local testing could be blocked if the DB container isn't spun up successfully.

# CONCERNS

## Technical Debt & Risks
1. **Memory Limits for Face Recognition**: The `face-recognition` (dlib) dependency requires significant RAM (8GB+ to compile). It is currently commented out or noted as disabled for Render production due to these constraints. An OpenCV headless alternative is used, which may have lower accuracy.
2. **Environment Configuration**: Secrets and `.env` files must be carefully managed. The `backend/.env.example` should be the only commited file, no real `.env` should be in git.
3. **Database Migrations**: When deploying to production with `pgvector`, the extension must be successfully created on the target database, which requires superuser privileges or a managed service that supports it natively.

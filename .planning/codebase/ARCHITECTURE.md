# ARCHITECTURE

## High-Level Architecture
- **Client-Server Model**: A React frontend (SPA) communicates with a Django REST Framework backend API.
- **Database**: PostgreSQL with `pgvector` for storing face embeddings and generic relational data.

## Deployment Model
- **Containerized**: `docker-compose.yml` provides the database. The Django application and Vite frontend run as separate services.
- **Production via Render**: The `render.yaml` definitions outline the deployment topology.

## Component Interactions
1. **Frontend**: Vite-built React app handles UI, state, camera access (for faces/QRs), and visualizations.
2. **Backend**: Django acts as the API gateway and business logic processor, utilizing JWT for stateless authentication.
3. **Database**: Stores structured data and facial embeddings.
4. **Background Tasks**: `django-q2` handles asynchronous work (e.g. email sending, heavy image processing).

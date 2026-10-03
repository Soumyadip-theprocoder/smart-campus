# ARCHITECTURE

## High-Level Architecture
- **Client-Server Model**: A React frontend (SPA) communicates with a Django REST Framework backend API.
- **Database**: PostgreSQL with `pgvector` for storing face embeddings and generic relational data.

## Deployment Model
- **Containerized Local**: `docker-compose.yml` provides the database. The Django application and Vite frontend run as separate services.
- **Production via Render**: The `render.yaml` definitions outline the deployment topology for backend and database.

## Component Interactions
1. **Frontend**: Vite-built React app handles UI, state, camera access (for faces/QRs), scheduling interfaces (drag-and-drop), and analytics visualizations.
2. **Backend**: Django acts as the API gateway and business logic processor, utilizing JWT for stateless authentication. Handles scheduling algorithms, PDF generation, and iCal feeds.
3. **Database**: Stores structured data (users, classes, timetables, groupings) and facial embeddings.
4. **Background Tasks**: `django-q2` handles asynchronous work (e.g. email sending, heavy image processing).

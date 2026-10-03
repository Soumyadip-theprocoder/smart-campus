# STRUCTURE

```text
/
├── .planning/                  # GSD planning state and codebase maps
├── backend/                    # Django application
│   ├── apps/                   # Django applications (domain logic)
│   ├── config/                 # Django settings and core configuration
│   ├── face_recognition_engine/# Image processing logic
│   ├── manage.py               # Django CLI
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Vite/React frontend application
│   ├── public/                 # Static assets
│   ├── src/                    # React components, contexts, and hooks
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite configuration
│   └── test_frontend.py        # Python-based frontend testing script
├── docs/                       # Project documentation
├── docker-compose.yml          # Container configuration for DB
└── render.yaml                 # Deployment configuration
```

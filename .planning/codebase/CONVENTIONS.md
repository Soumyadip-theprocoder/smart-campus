# Conventions

## Backend (Django/Python)
- **Architecture Standard**: Django MVT (Model-View-Template) is adapted to Model-View-Controller, where Views are DRF API Views returning JSON.
- **Apps**: Feature isolation into dedicated Django apps (`accounts`, `attendance`, `scheduler`, `communication`).
- **PEP 8**: Standard Python formatting applies.
- **REST Principles**: Endpoints follow resource-based routing (`/api/attendance/`, `/api/auth/`).
- **Secret Management**: Environment variables are managed via `.env` files using `python-decouple`/`django-environ`.

## Frontend (React/JS)
- **Component Style**: Functional components with React Hooks (useState, useEffect, useContext).
- **Module System**: ES Modules (`type: "module"` in package.json).
- **Styling**: Vanilla CSS mapping to class names.
- **File Structure**: Feature-driven folder structure (`src/features/`) combined with shared resources (`src/components/`, `src/api/`).
- **Routing**: Client-side routing with `react-router-dom`.

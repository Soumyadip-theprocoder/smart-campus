# Code Conventions

## Backend (Django / DRF)
- **Class-Based Views:** DRF Generic Views and ViewSets are highly preferred over function-based views to minimize boilerplate.
- **Permissions First:** Every view MUST declare `permission_classes`. Defaults should assume `IsAdminUser` for data-mutating operations unless explicitly public or restricted to a specific role.
- **Fat Models, Skinny Views:** Business logic (like checking schedule overlaps) belongs in model methods or specific service files (like `csp_solver.py`), not inside the View methods.
- **Environment Variables:** `os.environ.get()` with strict exception handling for missing critical keys (e.g. `SECRET_KEY`, `FACE_ENGINE_API_KEY`).

## Frontend (React)
- **Functional Components:** Only React functional components with Hooks. No class components.
- **CSS Architecture:** Vanilla CSS modules or global CSS (as long as Tailwind is avoided per project constraints). Aim for modern aesthetics: glassmorphism, gradients, and micro-animations.
- **Routing:** All routes must be declared in `App.jsx` and wrapped with `<ProtectedRoute>` depending on the allowed user role.
- **Code Splitting:** Route-level components should be imported dynamically via `React.lazy()` to keep the main bundle size small.

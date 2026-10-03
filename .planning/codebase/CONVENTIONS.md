# CONVENTIONS

## Language & Formatting
- **Backend**: Python 3 (Django). Formatting uses standard PEP 8, likely enforced via tools. Viewsets and REST framework routers are preferred for APIs.
- **Frontend**: JavaScript/JSX (ES6+). Functional components and React Hooks are standard.

## Architecture & Patterns
- **Frontend State**: Context API or specific hooks for state management (based on app size).
- **Backend Architecture**: Django standard `apps/` structure for domain separation.
- **API Design**: RESTful architecture returning JSON, utilizing Django REST Framework serializers.

## Naming
- Python/Django uses `snake_case` for variables/functions, `PascalCase` for classes.
- React/JS uses `camelCase` for variables, `PascalCase` for components.

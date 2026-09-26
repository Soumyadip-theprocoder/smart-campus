# Frontend Architecture & Component Library

The Smart Campus frontend is built with React + Vite, focusing on performance, modularity, and modern UI/UX principles.

## Structure

```
frontend/src/
├── api/          # Axios configuration and interceptors
├── components/   # Shared UI components (StatCard, DataTable, ErrorBoundary)
├── context/      # Global state providers
├── features/     # Route-level feature modules
│   ├── auth/
│   ├── dashboard/
│   ├── scheduler/
│   ├── attendance/
│   └── communication/
├── App.jsx       # Routing and Lazy Loading configuration
└── index.css     # Global styles and design system tokens
```

## Design System (`index.css`)

The application avoids heavy CSS frameworks, relying on a custom CSS-variable-based design system:
- **Glassmorphism:** The `.glass-card` class provides a sleek, frosted glass effect used universally across dashboards.
- **Themes:** Supports Light and Dark modes. Toggled via `.light-theme` applied to the `<body>`, driven by `ThemeContext`.
- **Layout Grids:** `.grid-2`, `.grid-3`, and `.grid-4` natively reflow to a single column (`1fr`) on viewports under `768px`.

## Key Components

### `DataTable`
A highly reusable, responsive data grid. On desktop screens, it behaves like a standard table. On mobile screens (width < `768px`), it automatically stacks into visually distinct cards, mapping `data-label` attributes to pseudo-elements for clean readability.

### `LocalErrorBoundary`
Protects the app from cascading failures. Used aggressively to wrap heavy third-party components (like Recharts `<AreaChart>`). If a chart fails to render or throws an exception, the boundary catches it and displays a localized fallback UI, keeping the parent dashboard fully interactive.

### `StatCard`
Displays high-level KPIs with animated entry delays (`animate-fade-in-up`) and gradient icon containers. Supports onClick navigation routing.

## Performance Optimizations
- **Code Splitting:** All major routes in `App.jsx` are dynamically imported using `React.lazy()` and wrapped in `<Suspense>`.
- **Bundle Shrinking:** Heavy dependencies (like `recharts` and `html2pdf.js`) are segmented into separate chunks via Vite's chunking algorithm, accelerating the initial Time-To-Interactive (TTI).
- **Asynchronous Polling:** Long-running backend operations (timetable generation) don't lock the UI. The frontend utilizes a non-blocking `setTimeout` polling loop to check `/api/scheduler/task-status/`.

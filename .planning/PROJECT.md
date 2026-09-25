# Smart Campus Management System

## Vision
A full-stack, AI-driven campus management platform that modernizes educational administration. It reduces manual overhead by providing automated attendance via facial recognition, constraint-based algorithmic class scheduling, centralized real-time dashboards, and automated SMTP email alerts.

## Core Pillars
1. **AI-Automated Attendance**: Eliminates manual roll calls using OpenCV and dlib CNN face recognition.
2. **Smart Scheduling**: Automates conflict-free timetable generation using a Backtracking Constraint Satisfaction Problem (CSP) solver.
3. **Centralized Communication**: Digital notice board and automated email dispatch for shortages and alerts.
4. **Role-Based Access**: Distinct dashboards and capabilities for Admins, Faculty, and Students.

## Current State
**v3.0 (Scale & Mobile Native)**
- Expand the platform for native mobile devices (iOS/Android) via React Native.
- Setup microservices for timetable scheduling to scale across multiple university branches.

<details>
<summary>Archived Versions</summary>

**v2.0 (Predictive Analytics & Alerts - Shipped)**
The analytics dashboards and remote AI integrations are fully complete. Deployed with multi-stage Dockerfiles and `render.yaml`. The system supports background workers (`django-q2`) for calculating students at risk of < 75% attendance and dispatching warning emails automatically. Remote AI face recognition runs in Google Colab while the main backend runs smoothly on constrained environments.

**v1.1 (Production Hardening & Features - Shipped)**
The platform is fully feature-complete, secure, and performant. Added critical security fixes, lazy-loaded components, and error boundaries for stability. Replaced manual DB face insertions with a web-based `react-webcam` registration flow. Upgraded the raw HTML dashboards with rich visual analytics (`recharts`) and automated PDF/CSV export generation (`reportlab`).

**v1.0 (MVP Delivery)**
The MVP is complete. The system features a robust PostgreSQL backend with `pgvector` HNSW indexes for face embeddings and asynchronous celery-like processing via Django Q2. The timetable solver successfully handles complex constraints including multi-campus transit times and student elective groupings. The Vite+React frontend is fully mobile-responsive and supports AI Face ID scans alongside fallback QR code scanning.
</details>


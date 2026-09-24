# Smart Campus Management System

## Vision
A full-stack, AI-driven campus management platform that modernizes educational administration. It reduces manual overhead by providing automated attendance via facial recognition, constraint-based algorithmic class scheduling, centralized real-time dashboards, and automated SMTP email alerts.

## Core Pillars
1. **AI-Automated Attendance**: Eliminates manual roll calls using OpenCV and dlib CNN face recognition.
2. **Smart Scheduling**: Automates conflict-free timetable generation using a Backtracking Constraint Satisfaction Problem (CSP) solver.
3. **Centralized Communication**: Digital notice board and automated email dispatch for shortages and alerts.
4. **Role-Based Access**: Distinct dashboards and capabilities for Admins, Faculty, and Students.

## Current State
**v1.1 (Production Hardening & Features - Shipped)**
The platform is fully feature-complete, secure, and performant. Added critical security fixes, lazy-loaded components, and error boundaries for stability. Replaced manual DB face insertions with a web-based `react-webcam` registration flow. Upgraded the raw HTML dashboards with rich visual analytics (`recharts`) and automated PDF/CSV export generation (`reportlab`).

<details>
<summary>Archived Versions</summary>

**v1.0 (MVP Delivery)**
The MVP is complete. The system features a robust PostgreSQL backend with `pgvector` HNSW indexes for face embeddings and asynchronous celery-like processing via Django Q2. The timetable solver successfully handles complex constraints including multi-campus transit times and student elective groupings. The Vite+React frontend is fully mobile-responsive and supports AI Face ID scans alongside fallback QR code scanning.
</details>

## Next Milestone Goals
**v2.0 (Predictive Analytics & Alerts)**
- Build an advanced analytics dashboard for deep organizational insight.
- Implement a predictive shortage algorithm to catch students before they fall under the 75% threshold.
- Setup background cron jobs to dispatch automated warning emails.

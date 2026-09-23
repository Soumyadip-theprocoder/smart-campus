# Phase 1 Context & Decisions

This document captures the implementation decisions for Phase 1 (Onboarding & Stabilization) to guide downstream planning and execution.

## 1. Face Recognition Performance
**Decision**: Use **PostgreSQL + pgvector**.
**Rationale**: It's highly scalable and allows native vector similarity search directly within the database, eliminating the need to process large NumPy arrays in application memory.
**Note**: Implementing `pgvector` will mandate running PostgreSQL locally for development, which conflicts with the decision to keep SQLite for local dev. This will need to be reconciled during implementation (e.g., using Docker for a local Postgres instance).

## 2. Database Migration
**Decision**: Keep **SQLite for local dev**, only use PostgreSQL on Render.
**Rationale**: Keeps the local development environment lightweight and easy to spin up without external dependencies.
**Implementation Guidance**: Ensure ORM queries remain database-agnostic. *If `pgvector` is implemented for face recognition, this decision must be revisited or a fallback mechanism for SQLite must be created.*

## 3. Async Task Workers (CSP Solver)
**Decision**: Use **Django Q**.
**Rationale**: Django Q uses the existing database (SQLite locally, Postgres in production) as a message broker. It is much simpler to set up than Celery since it doesn't require a separate Redis instance.
**Implementation Guidance**: Move the synchronous `POST /api/scheduler/generate/` endpoint to enqueue a Django Q task and return a task ID for the frontend to poll.

## 4. Testing Infrastructure
**Decision**: **Defer** setting up test frameworks (pytest, vitest).
**Rationale**: Focus on stabilization and core features first. Testing infrastructure will be handled in a dedicated Quality phase later in the roadmap.

# Phase 2 Context: Database Indexing & Performance

## Overview
Phase 2 focuses on Database Indexing and Performance Optimizations. Note that the asynchronous processing component (Django Q2) and the pgvector integration were already completed during Phase 1 stabilization. This phase will solely focus on optimizing database query performance through strategic indexing.

## Decisions Made

### 1. Vector Indexing (Face Recognition)
- **Decision:** Implement an HNSW (Hierarchical Navigable Small World) index on the `Student.face_encoding` field.
- **Rationale:** HNSW provides the fastest query time for approximate nearest neighbor search and is natively supported by pgvector in Django 4.2+. It does not require a "warm-up" period with existing data like IVFFlat does, making it perfect for a dynamic student database.
- **Implementation Note:** Use `pgvector.django.HnswIndex` in the `Student` model's `Meta.indexes`. Use `m` and `ef_construction` parameters appropriate for 128 dimensions (e.g. `m=16`, `ef_construction=64`).

### 2. Attendance Indexing
- **Decision:** Add individual database indexes to the `date` and `subject` fields, and create a composite index for `['student', 'subject']` on the `Attendance` model.
- **Rationale:** While `unique_together` on `['student', 'subject', 'date']` already creates a composite index, querying *only* by `date` (e.g., daily reports) or *only* by `subject` (e.g., class reports) cannot efficiently use the leftmost prefix of the existing index. The additional indexes will speed up dashboard analytics.

### 3. JSON Indexing (Faculty Availability)
- **Decision:** Add a GIN (Generalized Inverted Index) to the `Faculty.availability` JSONField.
- **Rationale:** Allows for fast querying of specific available time slots directly at the database level, rather than pulling all rows into Python memory to filter.
- **Implementation Note:** Use `django.contrib.postgres.indexes.GinIndex`.

## Exclusions
- **Asynchronous Processing:** Already implemented via `django-q2` in Phase 1.
- **Initial pgvector setup:** Already implemented (extension created, field migrated to VectorField) in Phase 1.

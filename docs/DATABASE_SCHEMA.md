# Database Schema

The system uses PostgreSQL as the primary database, utilizing specialized extensions like `pgvector` for ML integration. SQLite is supported as a local development fallback (without vector features).

## Core Models

### Accounts (`apps/accounts/models.py`)
- **`User` (AbstractUser)**
  - `email` (PK/Unique)
  - `role` (Choices: admin, student, faculty)
- **`StudentProfile`**
  - `user` (OneToOne)
  - `enrollment_number` (Unique)
  - `department`, `semester`
  - `face_encoding` (VectorField / JSONField fallback)
- **`FacultyProfile`**
  - `user` (OneToOne)
  - `employee_id` (Unique)
  - `department`, `designation`

### Scheduler (`apps/scheduler/models.py`)
- **`Subject`**
  - `code` (Unique), `name`, `credits`, `required_capacity`
  - `faculty` (ForeignKey)
- **`Room`**
  - `room_number` (Unique), `building`, `capacity`, `room_type`
- **`TimeSlot`**
  - `day` (SUN-SAT), `start_time`, `end_time`
- **`Timetable`**
  - Connects `Subject`, `Room`, `TimeSlot`

### Attendance (`apps/attendance/models.py`)
- **`Attendance`**
  - `student` (ForeignKey)
  - `subject` (ForeignKey)
  - `date`, `status` (Present/Absent/Late)
  - `method` (AI, Manual, Override)
  - *Indexes:* B-Tree composite index on `(student, subject, date)`.

### Communication (`apps/communication/models.py`)
- **`Notice`**
  - `title`, `content`, `priority`
  - `posted_by` (ForeignKey)
  - `created_at`

## Database Optimizations
- **HNSW Indexing:** The `face_encoding` field uses `pgvector`'s HNSW index to calculate L2 distance near-instantaneously during facial recognition login, scaling efficiently to 10k+ vectors.
- **JSONB & GIN:** Configuration and unstructured analytics data leverage PostgreSQL `JSONB` with `GIN` indexes for fast arbitrary key querying.

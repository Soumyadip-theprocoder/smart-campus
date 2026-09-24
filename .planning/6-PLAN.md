# Phase 6 Plan: Core Analytics & Predictive Modeling

## Overview
Develop the backend aggregation endpoints and the predictive shortage algorithm. This phase builds the core intelligence required to drive the upcoming Analytics Dashboard (Phase 7) and Automated Warning System (Phase 8).

## 1. Analytics Service (`backend/apps/attendance/analytics.py`)
- **Task**: Create a new module to handle heavy data aggregation.
- **Action**: Implement functions using Django ORM (`Count`, `Avg`, `TruncDate`) to calculate:
  - System-wide daily attendance trends over the last 30 days.
  - Department-wise overall attendance percentages.
  - Subject-wise overall attendance percentages.

## 2. Predictive Shortage Algorithm (`backend/apps/attendance/predictive.py`)
- **Task**: Implement a linear trajectory model to flag "At Risk" students.
- **Action**: 
  - Calculate a student's `current_attendance_rate`.
  - Calculate their `recent_trend` (e.g., attendance rate over the last 14 days).
  - Project their final semester attendance. If the projected final attendance falls below the mandatory **75%** threshold, flag the student.
  - Return a list of flagged student profiles with their predicted percentages and risk severity (e.g., "High", "Critical").

## 3. API Endpoints (`backend/apps/attendance/views.py`)
- **Task**: Expose the analytics and predictive data to the frontend via secure REST endpoints.
- **Action**: Create the following views (protected by `IsAdminUser` or `IsFaculty` permissions):
  - `AnalyticsGlobalView` (`GET /api/attendance/analytics/global/`)
  - `AnalyticsDepartmentView` (`GET /api/attendance/analytics/department/`)
  - `PredictiveAtRiskView` (`GET /api/attendance/analytics/at-risk/`)

## 4. Routing Configuration (`backend/apps/attendance/urls.py`)
- **Task**: Wire up the new analytics views.
- **Action**: Map the URLs to the newly created views.

## Verification
- Verify that standard Students get a `403 Forbidden` when attempting to access the analytics endpoints.
- Verify that `AnalyticsGlobalView` correctly aggregates mock data into a timeseries format suitable for Recharts.
- Verify that `PredictiveAtRiskView` correctly identifies a student with a deliberately poor recent attendance record.

# Requirements: Smart Campus v2.0 (Predictive Analytics)

## Overview
The goal of this milestone is to introduce deep data analytics and predictive modeling to the Smart Campus system. By analyzing historical attendance data, the system will identify students at risk of falling below the mandatory 75% attendance threshold and proactively alert them and the faculty.

## Features & Scope

### 1. Advanced Analytics Dashboard (Admin)
- **Feature**: A dedicated `/admin/analytics` page.
- **Details**:
  - Global attendance trends over the semester.
  - Department-wise and Subject-wise attendance comparisons.
  - Visualizations powered by `recharts`.

### 2. Predictive Shortage Modeling
- **Feature**: Backend cron job or algorithmic service.
- **Details**:
  - Predicts end-of-semester attendance percentage based on current trajectory (e.g., using moving average or simple linear regression).
  - Flags students whose predicted attendance falls below the 75% threshold.

### 3. Proactive Warning System
- **Feature**: Automated Email Alerts.
- **Details**:
  - Automatically dispatch warning emails to "At Risk" students.
  - Faculty dashboard should highlight students in their classes who are at risk of a shortage.

## Non-Functional Requirements
- **Performance**: Analytics queries must be optimized (using aggregations/materialized views if necessary) to prevent slow load times on large datasets.
- **Security**: Analytics endpoints must be strictly restricted to Admins and authorized Faculty.

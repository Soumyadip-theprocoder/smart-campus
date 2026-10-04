# Smart Campus Management System

## 1. Problem Statement
In the current academic ecosystem, administrative processes are heavily reliant on manual intervention. The traditional method of taking attendance via roll calls consumes valuable lecture time and is prone to ”proxy” attendances. Furthermore, the manual creation of class timetables often results in scheduling conflicts, whereas communication via physical noticeboards leads to information gaps between the administration and students.

## 2. Gap Analysis
Existing campus management systems primarily rely on manual attendance marking, static timetable creation, and traditional notice board communication, which are often time-consuming, error-prone, and inefficient. Many currently available solutions either focus only on attendance management or only on scheduling, lacking an integrated smart automation approach. Traditional attendance systems are vulnerable to proxy attendance and require significant faculty effort, while manual timetable generation frequently leads to scheduling conflicts and poor resource utilization. Furthermore, communication gaps between administration, faculty, and students arise due to delayed notice dissemination. 

Although some advanced systems implement biometric or RFID-based attendance, they often involve additional hardware costs and limited scalability. The proposed Smart Campus Management System addresses these gaps by integrating AI-based facial recognition for automated attendance, intelligent timetable scheduling using constraint-based algorithms, centralized database management, and real-time digital communication through dashboards and email notifications, thereby providing a unified, efficient, and scalable campus automation solution.

## 3. Literature Research & Academic Foundation
To ensure the system relies on state-of-the-art academic principles, an extensive literature survey was conducted across the three primary AI domains of the project using the arXiv and OpenAlex scholarly databases. The research roots the project in highly cited operational research, biometric security, and educational data mining.

### 3.1. Timetabling via Constraint Satisfaction Problems (CSP)
Educational timetabling is traditionally framed as an NP-complete Constraint Optimization Problem (COP). Our approach to offload scheduling to a CSP solver is heavily validated by decades of operations research:
- **Foundational Optimization:** Highly cited frameworks for non-linear optimization, such as [*"CasADi: a software framework for nonlinear optimization and optimal control"*](https://openalex.org/W2842089854) (Andersson et al., ~3900+ citations), underscore the necessity of robust mathematical models (like Backtracking and Forward Checking) for resolving complex resource allocations.
- **Educational Application:** Foundational research such as [*"Constructing university timetable using constraint satisfaction programming approach"*](https://openalex.org/W2102858635) and [*"A Constraint Driven Solution Model for Discrete Domains"*](https://arxiv.org/abs/2002.03102v1) confirms that CSP algorithms remain the most robust way to generate non-conflicting schedules while balancing soft preferences like faculty availability. More recently, [*"Optimizing University Course Timetabling Using Constraint Satisfaction Models"*](https://openalex.org/W4412783666) (2023) demonstrates continued reliance on these models. 

### 3.2. Real-time Face Recognition for Attendance
The integration of biometrics in academic environments aligns with the broader paradigm shift towards "Smart Campuses" and IoT-driven automation:
- **The Smart Campus Paradigm:** Highly impactful surveys such as [*"A Metaverse: Taxonomy, Components, Applications, and Open Challenges"*](https://openalex.org/W4206484811) (~1800+ citations) and [*"AI-big data analytics for building automation and management systems"*](https://openalex.org/W4306292106) (~500+ citations) categorize automated attendance as a foundational pillar of modern smart infrastructure.
- **Architectural Best Practices:** Recent papers such as [*"Smart Campus: Smart Attendance Management System using Face Recognition"*](https://openalex.org/W4395080192) (2024) and [*"IAAS: IoT-Based Automatic Attendance System... in Smart Campus"*](https://openalex.org/W3113809445) demonstrate massive industry movement towards biometric automation. Furthermore, [*"AttenFace: A Real Time Attendance System using Face Recognition"*](https://arxiv.org/abs/2211.07582v1) highlights the necessity of decoupling the face recognition processing from the backend database server to ensure scalability. The literature supports our decision to use periodic snapshots and Deep Convolutional Neural Networks (CNN/ResNet) over lightweight models like LBPH to maintain high accuracy against variations in lighting.

### 3.3. Predictive Analytics for Absenteeism
The operational impacts of absenteeism are significant, and predicting it requires careful data modeling to handle imbalances:
- **Impact & Crisis Mitigation:** The necessity of tracking student attendance to prevent dropout is highlighted by highly-cited works like [*"Risk Factors for School Absenteeism and Dropout: A Meta-Analytic Review"*](https://openalex.org/W2960437645) (~600+ citations). Furthermore, as seen in [*"School closure and management practices during coronavirus outbreaks... a rapid systematic review"*](https://openalex.org/W3015107971) (~2300+ citations), digital attendance and predictive tracing are critical for crisis resilience.
- **Algorithmic Approaches:** To combat absenteeism proactively, [*"A Novel Approach to Tackle and Predict Absenteeism of Students Using Deep Learning and Data Analytics"*](https://openalex.org/W4308650875) and [*"Integration of a machine learning model into a decision support tool..."*](https://arxiv.org/abs/2202.03577v1) advocate for integrating predictive analytics directly into administrative dashboards, dispatching automated alerts without requiring administrative ML expertise. Current literature also warns of "severe class imbalance" in attendance datasets, supporting our use of linear trajectory models and thresholds (e.g., 75% warnings) for initial MVP deployment over naive classification models.
- **Broader Educational AI:** As noted in [*"Application and theory gaps during the rise of Artificial Intelligence in Education"*](https://openalex.org/W3084223432) (~900+ citations), applying AI directly to student metrics must bridge the gap between theoretical ML models and practical, deployable software—a gap this project directly addresses.

## 4. Model Workflow & Architecture
The Smart Campus Management System operates through an integrated workflow consisting of user interaction, AI-based attendance processing, timetable scheduling, database management, and automated communication modules. 

1. **User Authentication and Login:** Students, faculty, and administrators log into a secure React/Vite dashboard using JWT-based credentials.
2. **Face Data Registration:** During setup, student facial images are captured via webcam. The system extracts facial features using a 29-layer ResNet Deep Convolutional Neural Network (CNN) to output a 128-dimensional encoding.
3. **Real-Time Face Detection and Attendance:** 
   - *Phase 1 (Detection):* HOG (Histogram of Oriented Gradients) is used to rapidly localize human faces in a video frame regardless of lighting.
   - *Phase 2 (Recognition):* The localized face is passed through the CNN to generate a 128-dimensional vector. This vector is compared against the database using Euclidean distance (L2 distance matching) to confidently identify the student and mark attendance automatically.
4. **Attendance Data Storage and Monitoring:** Records are stored in a centralized PostgreSQL database (utilizing the `pgvector` extension for instant encoding comparisons). 
5. **Automatic Timetable Scheduling:** An asynchronous Django Q2 background worker processes faculty availability, room capacities, and subject credits using a Constraint Satisfaction Problem solver to automatically generate conflict-free schedules.
6. **Notice and Communication Management:** Administrators publish digital notices and the system dispatches automated SMTP email alerts regarding attendance shortages.
7. **Data Visualization:** The dashboard provides real-time visual analytics of attendance statistics and schedules.

## 5. Technology Stack & Meta Data
The project architecture utilizes a robust, modern stack deployed via Docker, optimized for performance and AI capabilities:
- **Frontend Framework:** React 18 built with Vite, utilizing React Router DOM for routing.
- **Frontend Libraries:** `@dnd-kit/core` (Drag & Drop Timetables), `html2canvas` / `jspdf` (Export capabilities), `recharts` (Analytics visualizations), `react-webcam` (Face capture).
- **Backend Framework:** Django 4.2+ REST Framework secured via SimpleJWT authentication.
- **Background Tasks:** `django-q2` for asynchronous AI timetable scheduling and bulk SMTP alert dispatching.
- **Machine Learning Integration:** OpenCV and Pillow for frame capturing; 128-dimensional encodings generated via dlib/ResNet.
- **Database Engine:** PostgreSQL utilizing the specialized `pgvector` extension (HNSW indexes) for near-instantaneous L2 Euclidean distance face matching.

## 6. Database Schema
The core database models are partitioned into highly specialized domains via Django ORM:

### 6.1. Accounts (`apps/accounts/models.py`)
- **`User` (AbstractUser):** Core auth model. Primary key is `email`. Roles include *admin, student, faculty*.
- **`StudentProfile` / `FacultyProfile`:** Extends `User` using `OneToOneField`. Tracks `enrollment_number`, `employee_id`, and includes `ManyToMany` relations to `AcademicGroup` (for interdisciplinary classes) and a `ForeignKey` to `scheduler.Department`. The `StudentProfile` stores the `face_encoding` via `VectorField`.

### 6.2. Scheduler (`apps/scheduler/models.py`)
- **`Subject` & `Room`:** Contains `credits`, `required_capacity`, and hardware constraints.
- **`Timetable`:** Connects `Subject`, `Room`, and `TimeSlot` (`day`, `start_time`, `end_time`). Generated automatically by the backend CSP solver.

### 6.3. Attendance (`apps/attendance/models.py`)
- **`Attendance`:** Records `date`, `status` (Present/Absent/Late), and `method` (AI, Manual). Highly optimized via B-Tree composite indexes on `(student, subject, date)`.

## 7. API Reference & Endpoints
The backend exposes a comprehensive RESTful API built on the Django REST Framework (DRF):

### 7.1. Authentication (`/api/auth/`)
- `POST /login/`: Authenticates a user and returns `{ access, refresh, role }`.
- `GET /me/`: Retrieves the currently authenticated user's profile and metadata.
- `GET /groups/`: Lists and manages `AcademicGroup`s for interdisciplinary class tracking.

### 7.2. Scheduler (`/api/scheduler/`)
- `POST /generate/`: Triggers the async CSP solver to generate a new timetable. Returns a `{ task_id }`.
- `GET /task-status/<task_id>/`: Non-blocking polling endpoint to check the progress of async timetable generation.
- `GET /swaps/`: Manages timetable swap requests (AI conflict resolution).
- `GET /analytics/forecast/`: Predicts capacity needs based on simulated growth.
- `GET /ical/<user_id>/`: Retrieves the user's timetable as a downloadable `.ics` feed.

### 7.3. Analytics & Attendance (`/api/analytics/`, `/api/attendance/`)
- `GET /analytics/overview/`: Returns aggregated KPI stats (total students, active classes, campus attendance percentage).
- `GET /attendance/report/<student_id>/`: Returns detailed attendance breakdowns per subject for a specific student.
- `POST /communication/alerts/attendance/`: Triggers the Django Q2 worker to run predictive analytics and dispatch SMTP emails to students falling below the 75% threshold.

## 8. Target Audience & Role-Based Access
The system is built on a strict Multi-Tenant Role-Based Access Control (RBAC) architecture, catering to three distinct user groups:
1. **Administrators:** Have global oversight. They can trigger the AI timetable generation, manage master datasets (Subjects, Rooms, Users), publish digital notices, and view campus-wide analytics and accreditation reports.
2. **Faculty:** Can view their personalized timetables, download them via iCal, monitor student attendance in their specific classes, request schedule swaps via the AI conflict resolver, and access their specific performance metrics.
3. **Students:** Can view their personalized schedules, monitor their real-time attendance thresholds, receive automated shortfall warnings, and download PDF report cards.

## 9. Core System Modules & Capabilities
The system is divided into four highly scalable modules:
### 9.1. AI-Automated Attendance Module
- Replaces manual roll calls with an automated facial recognition pipeline.
- Uses OpenCV for capturing frames via `react-webcam` and Deep Convolutional Neural Networks (ResNet) to generate 128-dimensional facial encodings. 
- Fast verification is achieved by storing these encodings as vectors in PostgreSQL and querying them using HNSW indexing (`pgvector`), capable of matching faces in milliseconds.

### 9.2. Smart Timetable Scheduler Module
- Solves the NP-complete scheduling problem using a custom Constraint Satisfaction Problem (CSP) solver built into a asynchronous Django Q2 worker.
- Incorporates complex hard constraints (e.g., room capacity, faculty overlaps, physical inventory availability) and soft constraints (e.g., preferred faculty hours, student accessibility routing).
- Features dynamic institution hours, drag-and-drop overrides, and an "AI Smart Swap" engine for conflict resolution.

### 9.3. Analytics & Accreditation Module
- Generates real-time visual dashboards (using Recharts) for attendance trends, department performance, and classroom utilization.
- Automatically compiles Accreditation Analytics to track faculty contact hours and lab ratios for regulatory compliance.

### 9.4. Centralized Communication Module
- Provides a digital noticeboard for instant administrative broadcasts.
- Runs predictive cron jobs via `django-q2` to automatically dispatch SMTP email warnings to students whose attendance falls below the critical 75% threshold.

## 10. System Constraints & Architectural Decisions
- **Face Recognition Compute Constraint:** Traditional face recognition libraries like `dlib` consume significant RAM (often >1GB during inference), which exceeds the memory limits of free/hobby-tier production hosting (like Render). Consequently, heavy AI inference is decoupled; MVP production instances rely on fallback logic or remote inference APIs, while `pgvector` handles the distance calculation cleanly in the database layer.
- **Asynchronous Decoupling:** Timetable generation is mathematically intense and can take minutes for large campuses. This is strictly decoupled from the web thread using `django-q2` message queues to prevent API timeouts, providing a non-blocking UX via polling endpoints.
- **Database Standardization:** Instead of managing separate vector databases (like Pinecone) and relational databases (like MySQL), PostgreSQL with the `pgvector` extension was chosen to maintain ACID compliance across student metadata and biometric data simultaneously.

## 11. Current Progress & Implementation Status
The project is advancing rapidly and has reached **v2.1** maturity:
- **Core Platform:** Built the React frontend and Django REST Framework backend with full containerized (Docker) database integration.
- **Advanced Timetabling :** Implemented dynamic institution hours, drag-and-drop scheduling overrides, AI Smart Swaps, Academic Calendar sync (iCal), and Multi-Department isolation for massive scale.
- **Resource Logistics :** Successfully tracked physical inventory constraints, student accessibility routing, and automated Accreditation analytics.
- **PDF Export & Overhaul :** Completed the dynamic timetable break editor and finalized theme-stable PDF exports.


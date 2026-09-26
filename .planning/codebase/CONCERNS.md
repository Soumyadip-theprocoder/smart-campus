# Open Technical Concerns & Tech Debt

## Active Concerns

### 1. Database Indexing Scale
- The HNSW index for `pgvector` relies heavily on exact nearest-neighbor search. As the student face vector database grows into the tens of thousands, tuning the `m` and `ef_construction` parameters in PostgreSQL will become necessary to maintain `<100ms` facial recognition latency.

### 2. Timetable Generation Complexity
- The current Backtracking CSP solver runs in $O(N!)$ time. While Forward Checking trims the search space, dense scheduling scenarios (many subjects, limited rooms) may still cause the solver to time out.
- **Future Action:** Refactor the solver to implement a Metaheuristic approach (e.g., Genetic Algorithms or Simulated Annealing) to guarantee a "good enough" schedule within a fixed time bound rather than failing on perfect optimization.

### 3. Frontend Bundle Size
- `recharts` is heavy. While we have mitigated initial load times using `React.lazy()` chunking, the user still pays the network cost when navigating to the dashboard for the first time.
- **Future Action:** Explore migrating to lighter charting libraries or pre-fetching chunks via Service Workers.

### 4. Facial Recognition Security (Spoofing)
- The current `dlib` bounding box algorithm verifies facial features but lacks Liveness Detection. 
- **Future Action:** Integrate an anti-spoofing mechanism (e.g., blink detection or 3D depth analysis via mobile sensors) to prevent students from holding up photos to bypass attendance.

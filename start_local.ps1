# start_local.ps1
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Starting Smart Campus Local Environment  " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# 1. Start Database (only the db service)
Write-Host "[1/5] Starting PostgreSQL database container..." -ForegroundColor Cyan
docker-compose up -d db

# Wait for DB to be ready
Write-Host "Waiting for database to initialize..."
Start-Sleep -Seconds 3

# 2. Start Backend Web Server
Write-Host "[2/5] Starting Django Backend Web Server..." -ForegroundColor Cyan
$backendWebCmd = "cd backend; " +
                 "if (Test-Path 'venv\Scripts\activate.ps1') { .\venv\Scripts\activate.ps1 }; " +
                 "pip install -r requirements.txt; " +
                 "python manage.py migrate; " +
                 "python manage.py runserver"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendWebCmd -WindowStyle Normal

# 3. Start Backend Background Worker
Write-Host "[3/5] Starting Django QCluster Background Worker..." -ForegroundColor Cyan
$backendWorkerCmd = "cd backend; " +
                    "if (Test-Path 'venv\Scripts\activate.ps1') { .\venv\Scripts\activate.ps1 }; " +
                    "python manage.py qcluster"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendWorkerCmd -WindowStyle Normal

# 4. Start Frontend Development Server
Write-Host "[4/5] Starting React Frontend..." -ForegroundColor Cyan
$frontendCmd = "cd frontend; npm install; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

# 5. Start Face Recognition Engine
Write-Host "[5/5] Starting Face Recognition Engine..." -ForegroundColor Cyan
$faceEngineCmd = "cd backend\face_recognition_engine; " +
                 "if (Test-Path '..\venv\Scripts\activate.ps1') { ..\venv\Scripts\activate.ps1 }; " +
                 "python recognize_faces.py --subject-id 1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $faceEngineCmd -WindowStyle Normal

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "All services are launching in separate windows!" -ForegroundColor Green
Write-Host "Backend API:      http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend UI:      http://localhost:5173" -ForegroundColor Yellow
Write-Host "Face Recognition: Camera window active (press 'q' to quit)" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Green

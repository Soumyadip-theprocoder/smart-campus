# start_local.ps1
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Starting Smart Campus Local Environment  " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = (Get-Location).Path
}

# 1. Start Database (only the db service)
Write-Host "[1/4] Starting PostgreSQL database container..." -ForegroundColor Cyan
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    docker compose up -d db
} else {
    docker-compose up -d db
}

# Wait for DB to be ready
Write-Host "Waiting for database to initialize..."
Start-Sleep -Seconds 2

# 2. Start Backend Web Server
Write-Host "[2/4] Starting Django Backend Web Server..." -ForegroundColor Cyan
Start-Process cmd.exe -ArgumentList "/c", "`"$rootDir\scripts\run_backend.bat`""

# 3. Start Backend Background Worker
Write-Host "[3/4] Starting Django QCluster Background Worker..." -ForegroundColor Cyan
Start-Process cmd.exe -ArgumentList "/c", "`"$rootDir\scripts\run_worker.bat`""

# 4. Start Frontend Development Server
Write-Host "[4/4] Starting React Frontend..." -ForegroundColor Cyan
Start-Process cmd.exe -ArgumentList "/c", "`"$rootDir\scripts\run_frontend.bat`""

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "All services are launching in separate windows!" -ForegroundColor Green
Write-Host "Backend API:      http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend UI:      http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Optional: Run Face Recognition camera engine via:" -ForegroundColor Cyan
Write-Host "  scripts\run_face_recognition.bat" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Green

# CLARA Backend Services Startup Script
# Starts Training and Dataset backends in separate windows

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "CLARA Backend Services - Startup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Step 1: Environment Setup (UDS3 Integration)
# ============================================================================

Write-Host "Step 1: Configuring environment..." -ForegroundColor Yellow
Write-Host ""

# Get script directory
$ClaraRoot = $PSScriptRoot
$UDS3Root = Join-Path (Split-Path $ClaraRoot -Parent) "uds3"

# Set environment variables
$env:PYTHONPATH = "$UDS3Root;$ClaraRoot;$env:PYTHONPATH"
$env:UDS3_ROOT = $UDS3Root
$env:CLARA_ROOT = $ClaraRoot
$env:CLARA_ENVIRONMENT = "development"

if (Test-Path $UDS3Root) {
    Write-Host "[OK] UDS3 directory found: $UDS3Root" -ForegroundColor Green
} else {
    Write-Host "[!!] UDS3 directory NOT found: $UDS3Root" -ForegroundColor Yellow
    Write-Host "     Dataset search will be limited" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Step 2: Check if already running
# ============================================================================

Write-Host "Step 2: Checking existing services..." -ForegroundColor Yellow
Write-Host ""

# Check if already running
$trainingRunning = $false
$datasetRunning = $false

try {
    $response = Invoke-RestMethod -Uri "http://localhost:45680/health" -Method Get -TimeoutSec 2
    Write-Host "[!!] Training Backend already running on port 45680" -ForegroundColor Yellow
    $trainingRunning = $true
} catch {
    # Not running, will start
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:45681/health" -Method Get -TimeoutSec 2
    Write-Host "[!!] Dataset Backend already running on port 45681" -ForegroundColor Yellow
    $datasetRunning = $true
} catch {
    # Not running, will start
}

# Start Training Backend
if (-not $trainingRunning) {
    Write-Host "[>>] Starting Training Backend (Port 45680)..." -ForegroundColor Green
    
    # Pass environment variables to new process
    $env:PYTHONPATH = "$UDS3Root;$ClaraRoot;$env:PYTHONPATH"
    $env:UDS3_ROOT = $UDS3Root
    $env:CLARA_ENVIRONMENT = "development"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", `
        "`$env:PYTHONPATH='$UDS3Root;$ClaraRoot'; `$env:UDS3_ROOT='$UDS3Root'; python -m backend.training.app" `
        -WindowStyle Normal
    
    Start-Sleep -Seconds 2
} else {
    Write-Host "[OK] Training Backend already running" -ForegroundColor Green
}

# Start Dataset Backend
if (-not $datasetRunning) {
    Write-Host "[>>] Starting Dataset Backend (Port 45681)..." -ForegroundColor Green
    
    # Pass environment variables to new process
    $env:PYTHONPATH = "$UDS3Root;$ClaraRoot;$env:PYTHONPATH"
    $env:UDS3_ROOT = $UDS3Root
    $env:CLARA_ENVIRONMENT = "development"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", `
        "`$env:PYTHONPATH='$UDS3Root;$ClaraRoot'; `$env:UDS3_ROOT='$UDS3Root'; python -m backend.datasets.app" `
        -WindowStyle Normal
    
    Start-Sleep -Seconds 2
} else {
    Write-Host "[OK] Dataset Backend already running" -ForegroundColor Green
}

# Wait for services to be ready
Write-Host ""
Write-Host "[..] Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Verify health
Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Cyan

try {
    $training = Invoke-RestMethod -Uri "http://localhost:45680/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Training Backend: HEALTHY" -ForegroundColor Green
    Write-Host "     Port: $($training.port)" -ForegroundColor Gray
    Write-Host "     Active Jobs: $($training.active_jobs)" -ForegroundColor Gray
} catch {
    Write-Host "[!!] Training Backend: FAILED TO START" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $dataset = Invoke-RestMethod -Uri "http://localhost:45681/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Dataset Backend: HEALTHY" -ForegroundColor Green
    Write-Host "     Port: $($dataset.port)" -ForegroundColor Gray
    Write-Host "     Datasets: $($dataset.datasets_count)" -ForegroundColor Gray
    Write-Host "     UDS3: $($dataset.uds3_available)" -ForegroundColor Gray
} catch {
    Write-Host "[!!] Dataset Backend: FAILED TO START" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Backend Services Started!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Training API: http://localhost:45680" -ForegroundColor White
Write-Host "Dataset API:  http://localhost:45681" -ForegroundColor White
Write-Host ""
Write-Host "To stop services: Press CTRL+C in each backend window" -ForegroundColor Yellow
Write-Host "To launch frontends: .\launch_frontend.ps1" -ForegroundColor Cyan
Write-Host ""

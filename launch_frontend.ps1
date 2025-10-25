# Clara Frontend Launcher
# Starts all three frontend applications

Write-Host "Clara AI System - Frontend Launcher" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if backends are running
Write-Host "Checking backend services..." -ForegroundColor Yellow

try {
    $trainingHealth = Invoke-RestMethod -Uri "http://localhost:45680/health" -Method Get -TimeoutSec 2
    Write-Host "[OK] Training Backend: HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "[!!] Training Backend: Not running (Port 45680)" -ForegroundColor Red
}

try {
    $datasetHealth = Invoke-RestMethod -Uri "http://localhost:45681/health" -Method Get -TimeoutSec 2
    Write-Host "[OK] Dataset Backend: HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "[!!] Dataset Backend: Not running (Port 45681)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Select frontend to launch:" -ForegroundColor Cyan
Write-Host "1) Admin Frontend - System Administration"
Write-Host "2) Data Preparation - Dataset Management"
Write-Host "3) Training Frontend - Training Management"
Write-Host "4) Launch All Frontends"
Write-Host "5) Start Backend Services"
Write-Host "0) Exit"
Write-Host ""

$choice = Read-Host "Enter choice"

switch ($choice) {
    "1" {
        Write-Host "[>>] Launching Admin Frontend..." -ForegroundColor Green
        python -m frontend.admin.app
    }
    "2" {
        Write-Host "[>>] Launching Data Preparation Frontend..." -ForegroundColor Green
        python -m frontend.data_preparation.app
    }
    "3" {
        Write-Host "[>>] Launching Training Frontend..." -ForegroundColor Green
        python -m frontend.training.app
    }
    "4" {
        Write-Host "[>>] Launching all frontends..." -ForegroundColor Green
        Start-Process python -ArgumentList "-m","frontend.admin.app" -WindowStyle Normal
        Start-Sleep -Seconds 1
        Start-Process python -ArgumentList "-m","frontend.data_preparation.app" -WindowStyle Normal
        Start-Sleep -Seconds 1
        Start-Process python -ArgumentList "-m","frontend.training.app" -WindowStyle Normal
        Write-Host "[OK] All frontends launched!" -ForegroundColor Green
    }
    "5" {
        Write-Host "[>>] Starting backend services..." -ForegroundColor Yellow
        # Use dedicated startup script
        & "$PSScriptRoot\start_backends.ps1"
        Write-Host ""
        Write-Host "Press any key to return to menu..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        & $PSCommandPath  # Restart launcher
    }
    "0" {
        Write-Host "Goodbye!" -ForegroundColor Cyan
        exit 0
    }
    default {
        Write-Host "[!!] Invalid choice" -ForegroundColor Red
        Start-Sleep -Seconds 2
        & $PSCommandPath  # Restart launcher
    }
}

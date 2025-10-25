# CLARA System - Complete Development Startup
# Starts all backends and frontends for development

param(
    [switch]$BackendsOnly,
    [switch]$FrontendsOnly
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CLARA AI System - Development Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Environment Setup (UDS3 Integration)
# ============================================================================

Write-Host "Configuring environment..." -ForegroundColor Yellow

$ClaraRoot = $PSScriptRoot
$UDS3Root = Join-Path (Split-Path $ClaraRoot -Parent) "uds3"

$env:PYTHONPATH = "$UDS3Root;$ClaraRoot;$env:PYTHONPATH"
$env:UDS3_ROOT = $UDS3Root
$env:CLARA_ROOT = $ClaraRoot
$env:CLARA_ENVIRONMENT = "development"

if (Test-Path $UDS3Root) {
    Write-Host "[OK] UDS3 integration configured" -ForegroundColor Green
} else {
    Write-Host "[!!] UDS3 not found - dataset search limited" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Step 1: Start Backends
# ============================================================================

if (-not $FrontendsOnly) {
    Write-Host "Step 1: Starting Backend Services..." -ForegroundColor Yellow
    Write-Host ""
    
    & "$PSScriptRoot\start_backends.ps1"
    
    Write-Host ""
    Write-Host "[OK] Backends started successfully" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# Step 2: Launch Frontends
# ============================================================================

if (-not $BackendsOnly) {
    Write-Host "Step 2: Launching Frontend Applications..." -ForegroundColor Yellow
    Write-Host ""
    
    # Wait a bit for backends to fully initialize
    if (-not $FrontendsOnly) {
        Write-Host "[..] Waiting 5 seconds for backends to initialize..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
    
    # Launch all frontends
    Write-Host "[>>] Launching Admin Frontend..." -ForegroundColor Green
    Start-Process python -ArgumentList "-m","frontend.admin.app" -WindowStyle Normal
    Start-Sleep -Seconds 1
    
    Write-Host "[>>] Launching Data Preparation Frontend..." -ForegroundColor Green
    Start-Process python -ArgumentList "-m","frontend.data_preparation.app" -WindowStyle Normal
    Start-Sleep -Seconds 1
    
    Write-Host "[>>] Launching Training Frontend..." -ForegroundColor Green
    Start-Process python -ArgumentList "-m","frontend.training.app" -WindowStyle Normal
    
    Write-Host ""
    Write-Host "[OK] All frontends launched" -ForegroundColor Green
}

# ============================================================================
# Summary
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CLARA System Ready!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $FrontendsOnly) {
    Write-Host "Backend Services:" -ForegroundColor White
    Write-Host "  Training API:  http://localhost:45680" -ForegroundColor Gray
    Write-Host "  Dataset API:   http://localhost:45681" -ForegroundColor Gray
    Write-Host ""
}

if (-not $BackendsOnly) {
    Write-Host "Frontend Applications:" -ForegroundColor White
    Write-Host "  Admin Dashboard        (Window 1)" -ForegroundColor Gray
    Write-Host "  Data Preparation       (Window 2)" -ForegroundColor Gray
    Write-Host "  Training Management    (Window 3)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  Stop backends:  .\stop_backends.ps1" -ForegroundColor Gray
Write-Host "  Close frontends: Close GUI windows" -ForegroundColor Gray
Write-Host ""
Write-Host "Parameters:" -ForegroundColor Yellow
Write-Host "  -BackendsOnly   Start only backend services" -ForegroundColor Gray
Write-Host "  -FrontendsOnly  Launch only frontend GUIs" -ForegroundColor Gray
Write-Host ""

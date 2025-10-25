# CLARA Backend Services - Stop Script
# Stops all backend services gracefully

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "CLARA Backend Services - Stop" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Find Python processes running backend services
$backendProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -match "backend\.(training|datasets)\.app" -or
    $_.CommandLine -match "backend\.(training|datasets)\.app"
}

if ($backendProcesses) {
    Write-Host "Found $($backendProcesses.Count) backend process(es)" -ForegroundColor Yellow
    
    foreach ($proc in $backendProcesses) {
        Write-Host "[>>] Stopping process $($proc.Id)..." -ForegroundColor Yellow
        try {
            # Try graceful stop first (CTRL+C equivalent)
            $proc.CloseMainWindow() | Out-Null
            Start-Sleep -Seconds 2
            
            # If still running, force kill
            if (-not $proc.HasExited) {
                Stop-Process -Id $proc.Id -Force
                Write-Host "[OK] Process $($proc.Id) stopped (forced)" -ForegroundColor Green
            } else {
                Write-Host "[OK] Process $($proc.Id) stopped gracefully" -ForegroundColor Green
            }
        } catch {
            Write-Host "[!!] Failed to stop process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[OK] No backend processes running" -ForegroundColor Green
}

Write-Host ""

# Verify they're stopped
Start-Sleep -Seconds 1

try {
    $response = Invoke-RestMethod -Uri "http://localhost:45680/health" -Method Get -TimeoutSec 1
    Write-Host "[!!] Training Backend still responding on port 45680" -ForegroundColor Yellow
} catch {
    Write-Host "[OK] Training Backend stopped (Port 45680)" -ForegroundColor Green
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:45681/health" -Method Get -TimeoutSec 1
    Write-Host "[!!] Dataset Backend still responding on port 45681" -ForegroundColor Yellow
} catch {
    Write-Host "[OK] Dataset Backend stopped (Port 45681)" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Backend Services Stopped!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

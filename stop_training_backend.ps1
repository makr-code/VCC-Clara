# CLARA Training Backend Stop Script
# Stoppt laufende Training Backend Instanzen

Write-Host "🛑 CLARA Training Backend - Stop Script" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Find running Python processes for training backend
$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*clara_training_backend.py*"
}

if ($processes) {
    Write-Host "🔍 Gefundene Training Backend Prozesse:" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($proc in $processes) {
        Write-Host "   PID: $($proc.Id)" -ForegroundColor Gray
        Write-Host "   Command: $($proc.CommandLine)" -ForegroundColor Gray
        Write-Host ""
    }
    
    $confirm = Read-Host "Prozesse beenden? (j/n)"
    
    if ($confirm -eq "j") {
        foreach ($proc in $processes) {
            try {
                Stop-Process -Id $proc.Id -Force
                Write-Host "✅ Prozess $($proc.Id) beendet" -ForegroundColor Green
            } catch {
                Write-Host "❌ Fehler beim Beenden von Prozess $($proc.Id): $_" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "✅ Alle Prozesse gestoppt" -ForegroundColor Green
    } else {
        Write-Host "❌ Abbruch" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️  Keine laufenden Training Backend Prozesse gefunden" -ForegroundColor Gray
}

Write-Host ""

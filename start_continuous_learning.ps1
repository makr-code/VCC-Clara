#!/usr/bin/env powershell

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "CLARA Continuous Learning System" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "Wählen Sie eine Option:" -ForegroundColor Green
    Write-Host ""
    Write-Host "1. 🚀 Kontinuierliches Lernen starten" -ForegroundColor White
    Write-Host "2. 🎮 Live-Demo ausführen" -ForegroundColor White
    Write-Host "3. 📊 Statistiken anzeigen" -ForegroundColor White
    Write-Host "4. 🤖 Interaktiver Modus" -ForegroundColor White
    Write-Host "5. 📈 Status-Monitor" -ForegroundColor White
    Write-Host "6. 🧪 Demo-Modus" -ForegroundColor White
    Write-Host "7. ❌ Beenden" -ForegroundColor Red
    Write-Host ""
}

function Start-ContinuousLearning {
    Write-Host "🚀 Starte kontinuierliches LoRA-Learning..." -ForegroundColor Yellow
    python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml
}

function Start-LiveDemo {
    Write-Host "🎮 Starte Live-Demo..." -ForegroundColor Yellow
    python scripts/live_demo.py
}

function Show-Stats {
    Write-Host "📊 Live-Statistiken:" -ForegroundColor Yellow
    python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --stats
    Read-Host "Drücken Sie Enter zum Fortfahren"
}

function Start-Interactive {
    Write-Host "🤖 Interaktiver Modus:" -ForegroundColor Yellow
    python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --interactive
}

function Start-StatusMonitor {
    Write-Host "📈 Status-Monitor (Strg+C zum Beenden):" -ForegroundColor Yellow
    python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml
}

function Start-Demo {
    Write-Host "🧪 Demo-Modus:" -ForegroundColor Yellow
    python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --demo
}

# Hauptschleife
do {
    Show-Menu
    $choice = Read-Host "Ihre Wahl (1-7)"
    
    switch ($choice) {
        "1" { Start-ContinuousLearning }
        "2" { Start-LiveDemo }
        "3" { Show-Stats }
        "4" { Start-Interactive }
        "5" { Start-StatusMonitor }
        "6" { Start-Demo }
        "7" { 
            Write-Host "👋 Auf Wiedersehen!" -ForegroundColor Green
            break 
        }
        default { 
            Write-Host "❌ Ungültige Auswahl. Bitte versuchen Sie es erneut." -ForegroundColor Red
        }
    }
    
    if ($choice -ne "7") {
        Write-Host ""
        Write-Host "Zurück zum Hauptmenü..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
        Clear-Host
    }
    
} while ($choice -ne "7")

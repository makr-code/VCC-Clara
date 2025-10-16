@echo off
title CLARA Training Monitor
echo.
echo =====================================
echo  🚀 CLARA TRAINING STATUS MONITOR  
echo =====================================
echo.

:loop
cls
echo.
echo =====================================
echo  🚀 CLARA TRAINING STATUS MONITOR  
echo =====================================
echo  ⏰ %date% %time%
echo.

echo 🎮 GPU STATUS:
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits
echo.

echo 📊 DETAILLIERTE GPU INFO:
nvidia-smi --query-gpu=name,driver_version,memory.used,memory.total --format=csv
echo.

echo 🐍 PYTHON PROZESSE:
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE
echo.

echo 📁 TRAINING VERZEICHNIS:
if exist "models\clara_leo_cuda_outputs" (
    echo   ✅ Output-Verzeichnis existiert
    dir "models\clara_leo_cuda_outputs" /B | find /C /V ""
    echo   Dateien im Verzeichnis
) else (
    echo   ⏳ Output-Verzeichnis wird noch erstellt...
)
echo.

echo =====================================
echo  ⏭️ Nächstes Update in 30 Sekunden...
echo  💡 Drücken Sie Ctrl+C zum Beenden
echo =====================================

timeout /t 30 /nobreak >nul
goto loop

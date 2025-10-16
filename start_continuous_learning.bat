@echo off
echo ======================================
echo CLARA Continuous Learning System
echo ======================================
echo.

:menu
echo Wählen Sie eine Option:
echo.
echo 1. Kontinuierliches Lernen starten
echo 2. Live-Demo ausführen
echo 3. Statistiken anzeigen
echo 4. Interaktiver Modus
echo 5. Status-Monitor
echo 6. Beenden
echo.

set /p choice="Ihre Wahl (1-6): "

if "%choice%"=="1" goto start_continuous
if "%choice%"=="2" goto live_demo  
if "%choice%"=="3" goto show_stats
if "%choice%"=="4" goto interactive
if "%choice%"=="5" goto status_monitor
if "%choice%"=="6" goto end

echo Ungültige Auswahl. Bitte versuchen Sie es erneut.
goto menu

:start_continuous
echo.
echo 🚀 Starte kontinuierliches LoRA-Learning...
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml
goto menu

:live_demo
echo.
echo 🎮 Starte Live-Demo...
python scripts/live_demo.py
goto menu

:show_stats
echo.
echo 📊 Live-Statistiken:
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --stats
pause
goto menu

:interactive
echo.
echo 🤖 Interaktiver Modus:
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --interactive
goto menu

:status_monitor
echo.
echo 📈 Status-Monitor (Strg+C zum Beenden):
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml
goto menu

:end
echo.
echo 👋 Auf Wiedersehen!
pause

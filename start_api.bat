@echo off
echo ============================================
echo CLARA Continuous Learning API Server
echo ============================================
echo.

:menu
echo Wählen Sie eine Option:
echo.
echo 1. API Server starten (Standard)
echo 2. API Server mit Auto-Reload (Development)
echo 3. API Server mit Custom Port
echo 4. Dependencies installieren
echo 5. API-Status prüfen
echo 6. Veritas Integration testen
echo 7. Beenden
echo.

set /p choice="Ihre Wahl (1-7): "

if "%choice%"=="1" goto start_api
if "%choice%"=="2" goto start_dev
if "%choice%"=="3" goto start_custom
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto test_veritas
if "%choice%"=="7" goto end

echo Ungültige Auswahl. Bitte versuchen Sie es erneut.
goto menu

:start_api
echo.
echo 🚀 Starte CLARA API Server...
echo 📍 URL: http://127.0.0.1:8000
echo 📚 Docs: http://127.0.0.1:8000/docs
echo 🔄 Veritas: http://127.0.0.1:8000/veritas/question
echo.
python scripts/clara_api.py --host 127.0.0.1 --port 8000
goto menu

:start_dev
echo.
echo 🔧 Starte CLARA API Server (Development Mode)...
echo ⚡ Auto-Reload aktiviert
python scripts/clara_api.py --host 127.0.0.1 --port 8000 --reload
goto menu

:start_custom
echo.
set /p port="Port eingeben (Standard: 8000): "
if "%port%"=="" set port=8000
echo.
echo 🚀 Starte CLARA API Server auf Port %port%...
python scripts/clara_api.py --host 127.0.0.1 --port %port%
goto menu

:install_deps
echo.
echo 📦 Installiere API-Dependencies...
pip install -r requirements_api.txt
echo.
echo ✅ Dependencies installiert
pause
goto menu

:check_status
echo.
echo 📊 Prüfe API-Status...
curl -X GET "http://127.0.0.1:8000/health" -H "accept: application/json" 2>nul
if %errorlevel% equ 0 (
    echo ✅ API läuft
) else (
    echo ❌ API nicht erreichbar
    echo 💡 Starten Sie die API zuerst
)
pause
goto menu

:test_veritas
echo.
echo 🧪 Teste Veritas Integration...
python scripts/veritas_integration.py
pause
goto menu

:end
echo.
echo 👋 API Server gestoppt
pause

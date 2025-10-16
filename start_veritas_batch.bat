@echo off
REM CLARA Veritas Batch Processing Script
REM Automatisierte Verarbeitung des globalen Datenverzeichnisses Y:\data\ (Migration: früher Y:\veritas\data\)

echo.
echo ===============================================
echo  CLARA - Veritas Batch Processing Starter
echo ===============================================
echo.

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ FEHLER: Python ist nicht installiert oder nicht im PATH
    echo    Bitte installieren Sie Python 3.8+
    pause
    exit /b 1
)

REM Wechsle in das richtige Verzeichnis
cd /d Y:\verwLLM\scripts

REM Prüfe ob das neue globale Datenverzeichnis existiert
if not exist "Y:\data\" (
    echo ❌ WARNUNG: Y:\data\ nicht gefunden
    echo    (Früherer Standard war Y:\veritas\data\)
    echo    Verwende Test-Verzeichnis stattdessen...
    set INPUT_DIR=..\data\test_batch\
) else (
    set INPUT_DIR=Y:\data\
)

echo 📁 Input-Verzeichnis: %INPUT_DIR%
echo 📁 Output-Verzeichnis: ..\data\veritas_processed\ (konfigurierbar)
echo.

REM Benutzer-Optionen
echo Wählen Sie eine Option:
echo.
echo [1] 🔍 DRY-RUN (Nur Analyse, keine Verarbeitung)
echo [2] 📊 STANDARD Batch-Processing (empfohlen)
echo [3] 🚀 VOLLSTÄNDIGES Processing (alle Dateien)
echo [4] ⚙️  CUSTOM Konfiguration
echo [5] 📈 STATUS der letzten Verarbeitung anzeigen
echo.

set /p choice="Ihre Wahl (1-5): "

if "%choice%"=="1" goto dry_run
if "%choice%"=="2" goto standard
if "%choice%"=="3" goto full
if "%choice%"=="4" goto custom
if "%choice%"=="5" goto status
goto invalid_choice

:dry_run
echo.
echo 🔍 Starte DRY-RUN Analyse...
python veritas_batch_processor.py --input "%INPUT_DIR%" --config "..\configs\veritas_batch_config.yaml" --dry-run
goto end

:standard
echo.
echo 📊 Starte STANDARD Batch-Processing...
echo    ⚙️  12 parallele Prozesse
echo    📦 1000 Dateien pro Chunk
echo    🎯 Qualitätsfilterung aktiviert
echo.
python veritas_batch_processor.py --input "%INPUT_DIR%" --output "..\data\veritas_processed\" --config "..\configs\veritas_batch_config.yaml"
goto training_offer

:full
echo.
echo 🚀 Starte VOLLSTÄNDIGES Processing...
echo    ⚠️  WARNUNG: Dies kann sehr lange dauern!
echo.
set /p confirm="Fortfahren? (j/n): "
if /i not "%confirm%"=="j" goto end

python veritas_batch_processor.py --input "%INPUT_DIR%" --output "..\data\veritas_processed\" --config "..\configs\veritas_batch_config.yaml"
goto training_offer

:custom
echo.
echo ⚙️ CUSTOM Konfiguration
echo.
set /p custom_input="Input-Pfad (Standard: %INPUT_DIR%): "
if "%custom_input%"=="" set custom_input=%INPUT_DIR%

set /p custom_output="Output-Pfad (Standard: ..\data\veritas_processed\): "
if "%custom_output%"=="" set custom_output=..\data\veritas_processed\

set /p custom_config="Konfigurationsdatei (Standard: ..\configs\veritas_batch_config.yaml): "
if "%custom_config%"=="" set custom_config=..\configs\veritas_batch_config.yaml

echo.
echo 🔧 Starte mit benutzerdefinierten Einstellungen...
python veritas_batch_processor.py --input "%custom_input%" --output "%custom_output%" --config "%custom_config%"
goto training_offer

:status
echo.
echo 📈 Letzter Verarbeitungsstatus:
echo.
if exist "..\data\veritas_processed\veritas_batch_stats_*.json" (
    for /f %%f in ('dir /b /o-d "..\data\veritas_processed\veritas_batch_stats_*.json" ^| head -1') do (
        echo 📊 Letzte Statistik: %%f
        type "..\data\veritas_processed\%%f"
    )
) else (
    echo ❌ Keine Verarbeitungsstatistiken gefunden
    echo    Führen Sie zuerst eine Batch-Verarbeitung durch
)
goto end

:training_offer
echo.
echo ✅ Batch-Processing abgeschlossen!
echo.
echo 🚀 Möchten Sie jetzt das LoRA-Training starten?
echo    Dies verwendet die verarbeiteten Daten für CLARA-Training
echo.
set /p start_training="Training starten? (j/n): "
if /i "%start_training%"=="j" (
    echo.
    echo 🎯 Starte LoRA-Training mit Veritas-Konfiguration...
    python scripts\clara_train_lora.py --config "..\configs\veritas_config.yaml"
) else (
    echo.
    echo ℹ️  Training später starten mit:
    echo    python scripts/clara_train_lora.py --config configs/veritas_config.yaml
)
goto end

:invalid_choice
echo ❌ Ungültige Auswahl. Bitte wählen Sie 1-5.
pause
goto end

:end
echo.
echo 📋 Weitere Optionen:
echo.
echo    🔍 Ergebnisse prüfen: dir ..\data\veritas_processed\
echo    📊 Live-API starten: python scripts\clara_api.py
echo    📈 Training-Status: python scripts\clara_quick_status.py
echo    🛠️  Kontinuierliches Lernen: python scripts\clara_continuous_learning.py
echo.
echo 🎉 CLARA Veritas Batch-Processing beendet
pause

@echo off
REM Multi-GPU LoRA Training Starter für CLARA
REM Verwendung: start_multi_gpu.bat [config_file] [num_gpus]

setlocal

set CONFIG_FILE=%1
set NUM_GPUS=%2

if "%CONFIG_FILE%"=="" (
    echo Verwendung: start_multi_gpu.bat [config_file] [num_gpus]
    echo Beispiel: start_multi_gpu.bat configs/multi_gpu_config.yaml 2
    exit /b 1
)

if "%NUM_GPUS%"=="" (
    set NUM_GPUS=2
)

echo ==============================================
echo   Multi-GPU LoRA Training für CLARA
echo ==============================================
echo Config: %CONFIG_FILE%
echo GPUs: %NUM_GPUS%
echo.

REM Python-Umgebung aktivieren
call conda activate verwLLM 2>nul || (
    echo Warnung: Conda-Umgebung 'verwLLM' nicht gefunden
    echo Verwende System-Python
)

REM CUDA-Sichtbarkeit setzen
set CUDA_VISIBLE_DEVICES=0,1,2,3

REM Distributed Training Parameter
set MASTER_ADDR=localhost
set MASTER_PORT=29500

REM Training starten
echo Starte Multi-GPU Training...
python -m torch.distributed.launch ^
    --nproc_per_node=%NUM_GPUS% ^
    --nnodes=1 ^
    --node_rank=0 ^
    --master_addr=%MASTER_ADDR% ^
    --master_port=%MASTER_PORT% ^
    scripts/clara_train_multi_gpu.py ^
    --config %CONFIG_FILE%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Training mit Fehler beendet
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Multi-GPU Training erfolgreich abgeschlossen!
pause

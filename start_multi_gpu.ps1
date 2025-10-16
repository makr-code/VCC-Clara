# Multi-GPU LoRA Training Launcher für CLARA
# Verwendung: .\start_multi_gpu.ps1 -ConfigFile "configs/multi_gpu_config.yaml" -NumGPUs 2

param(
    [Parameter(Mandatory=$true)]
    [string]$ConfigFile,
    
    [Parameter(Mandatory=$false)]
    [int]$NumGPUs = 2,
    
    [Parameter(Mandatory=$false)]
    [string]$MasterPort = "29500"
)

function Write-Header {
    Write-Host "=============================================="
    Write-Host "   Multi-GPU LoRA Training für CLARA" -ForegroundColor Cyan
    Write-Host "=============================================="
    Write-Host "Config: $ConfigFile" -ForegroundColor Yellow
    Write-Host "GPUs: $NumGPUs" -ForegroundColor Yellow
    Write-Host ""
}

function Test-GPUs {
    Write-Host "🔍 Überprüfe verfügbare GPUs..." -ForegroundColor Blue
    
    try {
        $pythonCheck = python -c "import torch; print(f'CUDA verfügbar: {torch.cuda.is_available()}'); print(f'GPU Anzahl: {torch.cuda.device_count()}'); [print(f'GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"
        Write-Host $pythonCheck -ForegroundColor Green
        
        $gpuCount = python -c "import torch; print(torch.cuda.device_count())"
        if ([int]$gpuCount -lt $NumGPUs) {
            Write-Warning "Nur $gpuCount GPUs verfügbar, aber $NumGPUs angefordert!"
            $NumGPUs = [int]$gpuCount
            Write-Host "Setze GPU-Anzahl auf $NumGPUs" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Error "Fehler beim GPU-Check: $_"
        exit 1
    }
    
    Write-Host ""
}

function Start-Training {
    Write-Host "🚀 Starte Multi-GPU Training..." -ForegroundColor Green
    
    # Umgebungsvariablen setzen
    $env:CUDA_VISIBLE_DEVICES = "0,1,2,3"
    $env:MASTER_ADDR = "localhost"
    $env:MASTER_PORT = $MasterPort
    $env:PYTHONPATH = "${PWD};${env:PYTHONPATH}"
    
    # Training Command
    $trainingCmd = "python -m torch.distributed.launch " +
                   "--nproc_per_node=$NumGPUs " +
                   "--nnodes=1 " +
                   "--node_rank=0 " +
                   "--master_addr=localhost " +
                   "--master_port=$MasterPort " +
                   "scripts/clara_train_multi_gpu.py " +
                   "--config $ConfigFile"
    
    Write-Host "Führe aus: $trainingCmd" -ForegroundColor Cyan
    Write-Host ""
    
    # Training ausführen
    Invoke-Expression $trainingCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Multi-GPU Training erfolgreich abgeschlossen!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Training mit Fehler beendet (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

function Test-Config {
    if (-not (Test-Path $ConfigFile)) {
        Write-Error "Konfigurationsdatei nicht gefunden: $ConfigFile"
        Write-Host ""
        Write-Host "Verfügbare Konfigurationen:" -ForegroundColor Yellow
        Get-ChildItem "configs/*.yaml" | ForEach-Object { Write-Host "  - $($_.Name)" }
        exit 1
    }
}

function Show-Usage {
    Write-Host "Verwendung:" -ForegroundColor Yellow
    Write-Host "  .\start_multi_gpu.ps1 -ConfigFile 'configs/multi_gpu_config.yaml' -NumGPUs 2"
    Write-Host ""
    Write-Host "Parameter:" -ForegroundColor Yellow
    Write-Host "  -ConfigFile  : Pfad zur YAML-Konfigurationsdatei (erforderlich)"
    Write-Host "  -NumGPUs     : Anzahl der GPUs (Standard: 2)"
    Write-Host "  -MasterPort  : Port für Distributed Training (Standard: 29500)"
    Write-Host ""
    Write-Host "Beispiele:" -ForegroundColor Cyan
    Write-Host "  .\start_multi_gpu.ps1 -ConfigFile 'configs/multi_gpu_config.yaml'"
    Write-Host "  .\start_multi_gpu.ps1 -ConfigFile 'configs/multi_gpu_config.yaml' -NumGPUs 4"
}

# Hauptprogramm
try {
    Write-Header
    
    if ($ConfigFile -eq "help" -or $ConfigFile -eq "-h" -or $ConfigFile -eq "--help") {
        Show-Usage
        exit 0
    }
    
    Test-Config
    Test-GPUs
    Start-Training
}
catch {
    Write-Error "Unerwarteter Fehler: $_"
    exit 1
}

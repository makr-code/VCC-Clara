# CLARA + UDS3 Environment Setup
# Configures Python path for UDS3 integration

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "CLARA Environment Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ClaraRoot = $PSScriptRoot
$UDS3Root = Join-Path (Split-Path $ClaraRoot -Parent) "uds3"

Write-Host "[>>] CLARA Root: $ClaraRoot" -ForegroundColor Gray
Write-Host "[>>] UDS3 Root:  $UDS3Root" -ForegroundColor Gray
Write-Host ""

# Check if UDS3 exists
if (Test-Path $UDS3Root) {
    Write-Host "[OK] UDS3 directory found" -ForegroundColor Green
    
    # Check for UDS3 search module
    $searchApiPath = Join-Path $UDS3Root "search\search_api.py"
    if (Test-Path $searchApiPath) {
        Write-Host "[OK] UDS3 search_api.py found" -ForegroundColor Green
    } else {
        Write-Host "[!!] UDS3 search_api.py NOT found" -ForegroundColor Yellow
        Write-Host "     Expected: $searchApiPath" -ForegroundColor Gray
    }
} else {
    Write-Host "[!!] UDS3 directory NOT found" -ForegroundColor Red
    Write-Host "     Expected: $UDS3Root" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Solution:" -ForegroundColor Yellow
    Write-Host "  1. Clone UDS3 repository to: $UDS3Root" -ForegroundColor Gray
    Write-Host "  2. Or adjust path in backend config" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""

# Set environment variables
Write-Host "[>>] Setting environment variables..." -ForegroundColor Yellow

$env:PYTHONPATH = "$UDS3Root;$ClaraRoot;$env:PYTHONPATH"
$env:UDS3_ROOT = $UDS3Root
$env:CLARA_ROOT = $ClaraRoot
$env:CLARA_ENVIRONMENT = "development"

Write-Host "[OK] PYTHONPATH updated" -ForegroundColor Green
Write-Host "     $env:PYTHONPATH" -ForegroundColor Gray
Write-Host ""

# Verify Python can import UDS3
Write-Host "[>>] Verifying UDS3 import..." -ForegroundColor Yellow

$testScript = @"
import sys
sys.path.insert(0, '$($UDS3Root -replace '\\', '\\\\')')

try:
    from search.search_api import UDS3SearchAPI
    print('SUCCESS: UDS3 importable')
    exit(0)
except ImportError as e:
    print(f'FAILED: {e}')
    exit(1)
"@

$testResult = python -c $testScript 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] UDS3 is importable" -ForegroundColor Green
    Write-Host "     $testResult" -ForegroundColor Gray
} else {
    Write-Host "[!!] UDS3 import failed" -ForegroundColor Red
    Write-Host "     $testResult" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  1. UDS3 dependencies not installed" -ForegroundColor Gray
    Write-Host "  2. UDS3 module structure changed" -ForegroundColor Gray
    Write-Host "  3. Python version incompatibility" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Try installing UDS3 dependencies:" -ForegroundColor Cyan
    Write-Host "  cd $UDS3Root" -ForegroundColor Gray
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host ""
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Environment Setup Complete" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment Variables:" -ForegroundColor White
Write-Host "  CLARA_ROOT:        $env:CLARA_ROOT" -ForegroundColor Gray
Write-Host "  UDS3_ROOT:         $env:UDS3_ROOT" -ForegroundColor Gray
Write-Host "  CLARA_ENVIRONMENT: $env:CLARA_ENVIRONMENT" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  Start backends: .\start_backends.ps1" -ForegroundColor Gray
Write-Host "  Or full system: .\start_clara.ps1" -ForegroundColor Gray
Write-Host ""

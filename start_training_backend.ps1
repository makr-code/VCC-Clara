# CLARA Training Backend Start Script
# Startet den Training Backend Service auf Port 45680

param(
    [int]$Port = 45680,
    [int]$MaxConcurrentJobs = 2,
    [switch]$EnableMetrics,
    [int]$MetricsPort = 9310,
    [switch]$Debug
)

Write-Host "🚀 CLARA Training Backend - Start Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python nicht gefunden! Bitte installieren." -ForegroundColor Red
    exit 1
}

# Check if required modules exist
$scriptPath = Join-Path $PSScriptRoot "scripts\clara_training_backend.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Training Backend Script nicht gefunden: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Training Backend Script gefunden" -ForegroundColor Green
Write-Host ""

# Set Environment Variables
Write-Host "⚙️  Konfiguration:" -ForegroundColor Yellow
Write-Host "   Port: $Port" -ForegroundColor Gray
Write-Host "   Max Concurrent Jobs: $MaxConcurrentJobs" -ForegroundColor Gray

$env:CLARA_TRAINING_PORT = $Port
$env:CLARA_MAX_CONCURRENT_JOBS = $MaxConcurrentJobs

if ($EnableMetrics) {
    Write-Host "   Metrics: Enabled (Port $MetricsPort)" -ForegroundColor Gray
    $env:CLARA_METRICS_HTTP = "1"
    $env:CLARA_METRICS_PORT = $MetricsPort
} else {
    Write-Host "   Metrics: Disabled" -ForegroundColor Gray
    $env:CLARA_METRICS_HTTP = "0"
}

if ($Debug) {
    Write-Host "   Debug Mode: Enabled" -ForegroundColor Gray
    $env:CLARA_DEBUG = "1"
}

Write-Host ""

# Check if port is already in use
try {
    $portCheck = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($portCheck) {
        Write-Host "⚠️  Port $Port bereits belegt!" -ForegroundColor Yellow
        Write-Host "   Möglicherweise läuft der Service bereits." -ForegroundColor Yellow
        Write-Host ""
        $continue = Read-Host "Trotzdem starten? (j/n)"
        if ($continue -ne "j") {
            Write-Host "❌ Abbruch" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    # Port frei
}

# Check UDS3 Connection (optional)
Write-Host "🔍 Prüfe UDS3 Verbindung..." -ForegroundColor Yellow

$uds3Host = "192.168.178.94"
$uds3Ports = @{
    "PostgreSQL" = 5432
    "ChromaDB" = 8000
    "Neo4j" = 7687
}

$uds3Available = $true
foreach ($service in $uds3Ports.Keys) {
    $port = $uds3Ports[$service]
    try {
        $test = Test-NetConnection -ComputerName $uds3Host -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if ($test) {
            Write-Host "   ✅ $service ($uds3Host:$port) erreichbar" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $service ($uds3Host:$port) nicht erreichbar" -ForegroundColor Yellow
            $uds3Available = $false
        }
    } catch {
        Write-Host "   ⚠️  $service ($uds3Host:$port) nicht erreichbar" -ForegroundColor Yellow
        $uds3Available = $false
    }
}

if (-not $uds3Available) {
    Write-Host ""
    Write-Host "⚠️  Warnung: Nicht alle UDS3 Services erreichbar" -ForegroundColor Yellow
    Write-Host "   Service läuft ggf. mit eingeschränkter Funktionalität." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starte Training Backend..." -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Start Service
try {
    python $scriptPath
} catch {
    Write-Host ""
    Write-Host "❌ Fehler beim Starten des Services: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🛑 Training Backend gestoppt" -ForegroundColor Yellow

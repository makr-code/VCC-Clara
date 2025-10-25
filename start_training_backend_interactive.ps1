# ============================================================================
# CLARA Training Backend - Quick Start Script
# ============================================================================
# Startet den Training Backend Service mit Environment-Variable Security

# Security Mode auswählen
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                              ║" -ForegroundColor Cyan
Write-Host "║   CLARA Training Backend - Security Mode Selection          ║" -ForegroundColor Cyan
Write-Host "║                                                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Wähle Security Mode:" -ForegroundColor Yellow
Write-Host "1) DEBUG mode (no security, mock user) - Für lokale Entwicklung" -ForegroundColor Green
Write-Host "2) DEVELOPMENT mode (JWT only, no mTLS) - Für Entwicklung mit Keycloak" -ForegroundColor Yellow
Write-Host "3) PRODUCTION mode (JWT + mTLS) - Für Production Deployment" -ForegroundColor Red
Write-Host ""

$choice = Read-Host "Auswahl (1-3)"

switch ($choice) {
    "1" {
        $env:CLARA_SECURITY_MODE = "debug"
        $env:CLARA_JWT_ENABLED = "false"
        $env:CLARA_MTLS_ENABLED = "false"
        $env:DEBUG_USER_ROLES = "admin,trainer,analyst"
        Write-Host "✅ DEBUG MODE aktiviert (no security)" -ForegroundColor Green
        Write-Host "   - Kein JWT erforderlich" -ForegroundColor Gray
        Write-Host "   - Mock User: debug@clara.local" -ForegroundColor Gray
        Write-Host "   - Roles: admin, trainer, analyst" -ForegroundColor Gray
    }
    "2" {
        $env:CLARA_SECURITY_MODE = "development"
        $env:CLARA_JWT_ENABLED = "true"
        $env:CLARA_MTLS_ENABLED = "false"
        Write-Host "✅ DEVELOPMENT MODE aktiviert (JWT only)" -ForegroundColor Yellow
        Write-Host "   - JWT validation enabled" -ForegroundColor Gray
        Write-Host "   - Keycloak required (http://localhost:8080)" -ForegroundColor Gray
        Write-Host "   - No mTLS" -ForegroundColor Gray
    }
    "3" {
        $env:CLARA_SECURITY_MODE = "production"
        $env:CLARA_JWT_ENABLED = "true"
        $env:CLARA_MTLS_ENABLED = "true"
        Write-Host "✅ PRODUCTION MODE aktiviert (Full Security)" -ForegroundColor Red
        Write-Host "   - JWT validation enabled" -ForegroundColor Gray
        Write-Host "   - mTLS enabled" -ForegroundColor Gray
        Write-Host "   - Keycloak + PKI required" -ForegroundColor Gray
    }
    default {
        Write-Host "❌ Ungültige Auswahl. Verwende DEBUG mode." -ForegroundColor Red
        $env:CLARA_SECURITY_MODE = "debug"
        $env:CLARA_JWT_ENABLED = "false"
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Aktiviere Virtual Environment
Write-Host "🔧 Aktiviere Virtual Environment..." -ForegroundColor Cyan
& "C:\VCC\Clara\.venv\Scripts\Activate.ps1"

# Setze weitere Environment Variables
$env:CLARA_TRAINING_PORT = "45680"
$env:CLARA_MAX_CONCURRENT_JOBS = "2"
$env:LOG_LEVEL = "INFO"
$env:ENABLE_API_DOCS = "true"
$env:ENABLE_CORS = "true"

# Check Python Dependencies
Write-Host "📦 Checking Python Dependencies..." -ForegroundColor Cyan

$required_packages = @(
    "fastapi",
    "uvicorn",
    "pydantic",
    "python-multipart"
)

if ($env:CLARA_JWT_ENABLED -eq "true") {
    $required_packages += @("PyJWT", "requests", "cryptography", "python-jose")
}

foreach ($package in $required_packages) {
    $installed = python -c "import $($package.ToLower().Replace('-', '_'))" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Package '$package' not installed. Installing..." -ForegroundColor Yellow
        pip install $package
    }
}

Write-Host "✅ All dependencies installed" -ForegroundColor Green
Write-Host ""

# Print Configuration
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🚀 Starting CLARA Training Backend" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Security Mode:      $env:CLARA_SECURITY_MODE" -ForegroundColor White
Write-Host "JWT Enabled:        $env:CLARA_JWT_ENABLED" -ForegroundColor White
Write-Host "mTLS Enabled:       $env:CLARA_MTLS_ENABLED" -ForegroundColor White
Write-Host "Port:               $env:CLARA_TRAINING_PORT" -ForegroundColor White
Write-Host "Max Concurrent:     $env:CLARA_MAX_CONCURRENT_JOBS" -ForegroundColor White
Write-Host "API Docs:           http://localhost:$env:CLARA_TRAINING_PORT/docs" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($env:CLARA_SECURITY_MODE -eq "debug") {
    Write-Host "⚠️  WARNING: DEBUG MODE - NO SECURITY ENFORCEMENT!" -ForegroundColor Red
    Write-Host "   Only use for local development. NEVER in production!" -ForegroundColor Red
    Write-Host ""
}

# Start Backend
Write-Host "Starting backend service..." -ForegroundColor Cyan
Write-Host ""

try {
    python scripts/clara_training_backend.py
}
catch {
    Write-Host "❌ Error starting backend: $_" -ForegroundColor Red
    exit 1
}

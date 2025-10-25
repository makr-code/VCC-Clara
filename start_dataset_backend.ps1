#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start CLARA Dataset Management Backend Service

.DESCRIPTION
    Starts the Dataset Backend Service on Port 45681
    
    Features:
    - UDS3 Hybrid Search Integration
    - Dataset Quality Pipeline
    - Multi-Format Export (JSONL, Parquet, CSV, JSON)
    - Dataset Registry
    - JWT Authentication

.PARAMETER SecurityMode
    Security mode: production, development, debug, testing
    Default: development

.PARAMETER Port
    Service port (default: 45681)

.EXAMPLE
    .\start_dataset_backend.ps1
    
.EXAMPLE
    .\start_dataset_backend.ps1 -SecurityMode debug

.EXAMPLE
    .\start_dataset_backend.ps1 -SecurityMode production -Port 45681
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("production", "development", "debug", "testing")]
    [string]$SecurityMode = "development",
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 45681
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

# Colors
$ColorReset = "`e[0m"
$ColorGreen = "`e[32m"
$ColorYellow = "`e[33m"
$ColorBlue = "`e[34m"
$ColorRed = "`e[31m"

# ============================================================================
# Functions
# ============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "${ColorBlue}============================================================${ColorReset}"
    Write-Host "${ColorBlue}  $Text${ColorReset}"
    Write-Host "${ColorBlue}============================================================${ColorReset}"
}

function Write-Success {
    param([string]$Text)
    Write-Host "${ColorGreen}✓ $Text${ColorReset}"
}

function Write-Warning {
    param([string]$Text)
    Write-Host "${ColorYellow}⚠ $Text${ColorReset}"
}

function Write-Error {
    param([string]$Text)
    Write-Host "${ColorRed}✗ $Text${ColorReset}"
}

function Write-Info {
    param([string]$Text)
    Write-Host "  $Text"
}

# ============================================================================
# Main Script
# ============================================================================

Write-Header "CLARA Dataset Management Backend"

# Check Python
Write-Host ""
Write-Host "Checking Python..."
try {
    $pythonVersion = & python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.9+"
    exit 1
}

# Activate Virtual Environment (if exists)
$venvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path (Join-Path $venvPath "Scripts\Activate.ps1")) {
    Write-Host ""
    Write-Host "Activating virtual environment..."
    & (Join-Path $venvPath "Scripts\Activate.ps1")
    Write-Success "Virtual environment activated"
}

# Set Environment Variables
Write-Host ""
Write-Host "Setting environment variables..."
$env:CLARA_SECURITY_MODE = $SecurityMode
$env:CLARA_DATASET_PORT = $Port.ToString()

Write-Info "Security Mode: $SecurityMode"
Write-Info "Port: $Port"

# Security Mode Details
Write-Host ""
Write-Header "Security Configuration"

switch ($SecurityMode) {
    "production" {
        Write-Info "🔐 Mode: PRODUCTION"
        Write-Info "    - JWT Authentication: ENABLED"
        Write-Info "    - mTLS: ENABLED"
        Write-Info "    - Keycloak: REQUIRED"
        Write-Info "    - PKI Service: REQUIRED"
        Write-Warning "Ensure Keycloak and PKI Service are running!"
    }
    "development" {
        Write-Info "🛠️  Mode: DEVELOPMENT"
        Write-Info "    - JWT Authentication: ENABLED"
        Write-Info "    - mTLS: DISABLED"
        Write-Info "    - Keycloak: OPTIONAL (graceful fallback)"
        Write-Info "    - PKI Service: NOT REQUIRED"
    }
    "debug" {
        Write-Info "🐛 Mode: DEBUG"
        Write-Info "    - JWT Authentication: DISABLED"
        Write-Info "    - mTLS: DISABLED"
        Write-Info "    - Keycloak: NOT REQUIRED"
        Write-Info "    - PKI Service: NOT REQUIRED"
        Write-Warning "DO NOT USE IN PRODUCTION!"
    }
    "testing" {
        Write-Info "🧪 Mode: TESTING"
        Write-Info "    - JWT Authentication: MOCK"
        Write-Info "    - mTLS: DISABLED"
        Write-Info "    - Keycloak: MOCKED"
        Write-Info "    - PKI Service: NOT REQUIRED"
    }
}

# Check Dependencies
Write-Host ""
Write-Header "Dependency Check"

$missingDeps = @()

# Check JWT Middleware
$jwtMiddlewarePath = Join-Path $ProjectRoot "shared\jwt_middleware.py"
if (Test-Path $jwtMiddlewarePath) {
    Write-Success "JWT Middleware found"
} else {
    Write-Warning "JWT Middleware not found (optional in debug mode)"
    if ($SecurityMode -eq "production") {
        $missingDeps += "jwt_middleware.py"
    }
}

# Check UDS3 Dataset Search
$uds3SearchPath = Join-Path $ProjectRoot "shared\uds3_dataset_search.py"
if (Test-Path $uds3SearchPath) {
    Write-Success "UDS3 Dataset Search API found"
} else {
    Write-Error "UDS3 Dataset Search API not found"
    $missingDeps += "uds3_dataset_search.py"
}

# Check UDS3 Backend
$uds3BackendPath = Join-Path $ProjectRoot "..\uds3"
if (Test-Path $uds3BackendPath) {
    Write-Success "UDS3 Backend found: $uds3BackendPath"
} else {
    Write-Warning "UDS3 Backend not found at parent directory"
    Write-Info "Dataset service will use graceful degradation"
}

if ($missingDeps.Count -gt 0) {
    Write-Host ""
    Write-Error "Missing critical dependencies:"
    foreach ($dep in $missingDeps) {
        Write-Info "  - $dep"
    }
    exit 1
}

# Create Data Directory
$dataDir = Join-Path $ProjectRoot "data\datasets"
if (-not (Test-Path $dataDir)) {
    Write-Host ""
    Write-Host "Creating data directory..."
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    Write-Success "Data directory created: $dataDir"
}

# Start Service
Write-Host ""
Write-Header "Starting Dataset Backend Service"
Write-Info "Port: $Port"
Write-Info "Security Mode: $SecurityMode"
Write-Info "Logs: See console output"
Write-Host ""
Write-Host "Press ${ColorYellow}Ctrl+C${ColorReset} to stop the service"
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Start Service
try {
    & python scripts\clara_dataset_backend.py
} catch {
    Write-Host ""
    Write-Error "Service failed to start: $_"
    exit 1
}

Write-Host ""
Write-Success "Service stopped gracefully"

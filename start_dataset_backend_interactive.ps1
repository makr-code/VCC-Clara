#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Interactive Launcher for CLARA Dataset Management Backend

.DESCRIPTION
    Interactive menu to start the Dataset Backend Service with different security modes
    
.EXAMPLE
    .\start_dataset_backend_interactive.ps1
#>

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Colors
$ColorReset = "`e[0m"
$ColorGreen = "`e[32m"
$ColorYellow = "`e[33m"
$ColorBlue = "`e[34m"
$ColorRed = "`e[31m"
$ColorCyan = "`e[36m"

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

function Write-MenuOption {
    param([string]$Number, [string]$Text, [string]$Description)
    Write-Host ""
    Write-Host "  ${ColorCyan}[$Number]${ColorReset} ${ColorGreen}$Text${ColorReset}"
    Write-Host "       $Description"
}

# ============================================================================
# Main Menu
# ============================================================================

Write-Header "CLARA Dataset Management Backend - Interactive Launcher"

Write-Host ""
Write-Host "Select Security Mode:"

Write-MenuOption "1" "🔐 Production Mode" "JWT + mTLS (Keycloak + PKI Service required)"
Write-MenuOption "2" "🛠️  Development Mode" "JWT only (Keycloak optional, graceful fallback)"
Write-MenuOption "3" "🐛 Debug Mode" "No authentication (FOR DEVELOPMENT ONLY!)"
Write-MenuOption "4" "🧪 Testing Mode" "Mock authentication (for integration tests)"
Write-MenuOption "0" "❌ Exit" "Cancel and exit"

Write-Host ""
Write-Host -NoNewline "Enter choice [0-4]: "
$choice = Read-Host

# Map choice to security mode
$securityMode = switch ($choice) {
    "1" { "production" }
    "2" { "development" }
    "3" { "debug" }
    "4" { "testing" }
    "0" { 
        Write-Host ""
        Write-Host "${ColorYellow}Cancelled.${ColorReset}"
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "${ColorRed}Invalid choice. Exiting.${ColorReset}"
        exit 1
    }
}

# Warning for production mode
if ($securityMode -eq "production") {
    Write-Host ""
    Write-Header "Production Mode - Pre-Flight Check"
    Write-Host ""
    Write-Host "${ColorYellow}⚠️  Production mode requires:${ColorReset}"
    Write-Host "   1. Keycloak running on http://localhost:8080"
    Write-Host "   2. PKI Service running on https://localhost:8443"
    Write-Host "   3. PostgreSQL database configured"
    Write-Host ""
    Write-Host -NoNewline "Are all services running? [y/N]: "
    $confirm = Read-Host
    
    if ($confirm -notmatch '^[yY]') {
        Write-Host ""
        Write-Host "${ColorYellow}Cancelled. Please start required services first.${ColorReset}"
        exit 0
    }
}

# Warning for debug mode
if ($securityMode -eq "debug") {
    Write-Host ""
    Write-Header "Debug Mode - Security Warning"
    Write-Host ""
    Write-Host "${ColorRed}⚠️  WARNING: Debug mode disables ALL authentication!${ColorReset}"
    Write-Host "   ${ColorRed}- DO NOT use in production${ColorReset}"
    Write-Host "   ${ColorRed}- DO NOT expose to network${ColorReset}"
    Write-Host "   ${ColorRed}- ONLY for local development${ColorReset}"
    Write-Host ""
    Write-Host -NoNewline "Continue with debug mode? [y/N]: "
    $confirm = Read-Host
    
    if ($confirm -notmatch '^[yY]') {
        Write-Host ""
        Write-Host "${ColorYellow}Cancelled.${ColorReset}"
        exit 0
    }
}

# Start service
Write-Host ""
Write-Header "Starting Dataset Backend Service"
Write-Host ""
Write-Host "Security Mode: ${ColorGreen}$securityMode${ColorReset}"
Write-Host "Port: ${ColorCyan}45681${ColorReset}"
Write-Host ""

$launcherScript = Join-Path $ScriptDir "start_dataset_backend.ps1"

if (-not (Test-Path $launcherScript)) {
    Write-Host "${ColorRed}Error: Launcher script not found: $launcherScript${ColorReset}"
    exit 1
}

# Execute launcher
& $launcherScript -SecurityMode $securityMode

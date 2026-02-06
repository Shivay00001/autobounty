# AutoBounty Frontend Deployment Script
param(
    [switch]$Dev = $false,
    [switch]$Prod = $false,
    [switch]$Install = $false,
    [switch]$Build = $false
)

$ErrorActionPreference = "Continue"
$FrontendDir = $PSScriptRoot

# Color functions
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error-Custom { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ $msg" -ForegroundColor Cyan }

Write-Info "AutoBounty Frontend Deployment"
Write-Host "==============================="
Write-Host ""

# Check Node.js
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "npm not found. Install Node.js from https://nodejs.org/"
    exit 1
}

$npmVersion = npm --version
Write-Success "npm: v$npmVersion"

# Install dependencies
if ($Install -or -not (Test-Path "$FrontendDir\node_modules")) {
    Write-Info "Installing dependencies..."
    cd $FrontendDir
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
    }
    else {
        Write-Error-Custom "Failed to install dependencies"
        exit 1
    }
}

# Build for production
if ($Build -or $Prod) {
    Write-Info "Building for production..."
    cd $FrontendDir
    npm run build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Production build complete"
    }
    else {
        Write-Error-Custom "Build failed"
        exit 1
    }
}

# Run frontend
Write-Host ""
cd $FrontendDir

if ($Prod -and (Test-Path "$FrontendDir\dist")) {
    # Serve production build
    Write-Info "Serving production build on port 3002..."
    npx serve -s dist -l 3002
}
else {
    # Development mode (default)
    Write-Info "Starting development server on port 3002..."
    npm run dev -- --port 3002
}

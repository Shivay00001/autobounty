# AutoBounty Backend Deployment Script
param(
    [switch]$Dev = $false,
    [switch]$Prod = $false,
    [switch]$Install = $false
)

$ErrorActionPreference = "Continue"
$BackendDir = $PSScriptRoot

# Color functions
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Error-Custom { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ $msg" -ForegroundColor Cyan }

Write-Info "AutoBounty Backend Deployment"
Write-Host "=============================="
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "Python not found. Install from https://www.python.org/"
    exit 1
}

$pythonVersion = python --version
Write-Success "Python: $pythonVersion"

# Create virtual environment if needed
if (-not (Test-Path "$BackendDir\venv")) {
    Write-Info "Creating virtual environment..."
    python -m venv "$BackendDir\venv"
    Write-Success "Virtual environment created"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& "$BackendDir\venv\Scripts\Activate.ps1"

# Install/update dependencies
if ($Install -or -not (Test-Path "$BackendDir\venv\Lib\site-packages\fastapi")) {
    Write-Info "Installing dependencies..."
    if (Test-Path "$BackendDir\requirements.txt") {
        pip install -r "$BackendDir\requirements.txt"
        Write-Success "Dependencies installed"
    }
    else {
        Write-Error-Custom "requirements.txt not found"
        exit 1
    }
}

# Create necessary directories
$dirs = @("data", "logs", "reports", "scans")
foreach ($dir in $dirs) {
    $path = Join-Path $BackendDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Success "Created directory: $dir"
    }
}

# Create .env if needed
if (-not (Test-Path "$BackendDir\.env")) {
    $parentEnv = Join-Path (Split-Path $BackendDir -Parent) ".env.example"
    if (Test-Path $parentEnv) {
        Copy-Item $parentEnv "$BackendDir\.env"
        Write-Success "Created .env file"
    }
}

# Run backend
Write-Host ""
Write-Info "Starting AutoBounty Backend on port 8002..."
Write-Host ""

if ($Prod) {
    # Production mode
    Write-Info "Running in PRODUCTION mode"
    if (Get-Command uvicorn -ErrorAction SilentlyContinue) {
        uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
    }
    else {
        python main.py --port 8002
    }
}
else {
    # Development mode (default)
    Write-Info "Running in DEVELOPMENT mode"
    if (Test-Path "$BackendDir\main.py") {
        python main.py
    }
    else {
        Write-Error-Custom "main.py not found"
        exit 1
    }
}

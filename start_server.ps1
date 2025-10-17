# Quick Start Script for App Builder API
# Run this script to set up and start the API server

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   App Builder API - Quick Start" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Git
Write-Host "[2/6] Checking Git..." -ForegroundColor Yellow
$gitVersion = git --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ $gitVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Git not found. Please install Git" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "[3/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check environment variables
Write-Host "[4/6] Checking environment variables..." -ForegroundColor Yellow
$hasGithubToken = $env:GITHUB_TOKEN -ne $null -and $env:GITHUB_TOKEN -ne ""
$hasGithubUsername = $env:GITHUB_USERNAME -ne $null -and $env:GITHUB_USERNAME -ne ""

if ($hasGithubToken) {
    Write-Host "  ✓ GITHUB_TOKEN is set" -ForegroundColor Green
} else {
    Write-Host "  ✗ GITHUB_TOKEN is not set" -ForegroundColor Red
    Write-Host "    Set it with: `$env:GITHUB_TOKEN = 'your_token'" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

if ($hasGithubUsername) {
    Write-Host "  ✓ GITHUB_USERNAME is set" -ForegroundColor Green
} else {
    Write-Host "  ✗ GITHUB_USERNAME is not set" -ForegroundColor Red
    Write-Host "    Set it with: `$env:GITHUB_USERNAME = 'your_username'" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

if ($env:OPENAI_API_KEY) {
    Write-Host "  ✓ OPENAI_API_KEY is set (optional)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ OPENAI_API_KEY is not set (will use fallback template)" -ForegroundColor Yellow
}

# Check for secrets
Write-Host "[5/6] Checking secrets..." -ForegroundColor Yellow
if (Test-Path "secrets.json") {
    Write-Host "  ✓ secrets.json found" -ForegroundColor Green
} else {
    Write-Host "  ⚠ secrets.json not found" -ForegroundColor Yellow
    Write-Host "    To import secrets: python manage_secrets.py import form_responses.csv" -ForegroundColor Yellow
    Write-Host "    Or add manually: python manage_secrets.py add email@example.com secret" -ForegroundColor Yellow
    
    # Create empty secrets file
    '{"secrets": {}}' | Out-File -FilePath "secrets.json" -Encoding utf8
    Write-Host "  ✓ Created empty secrets.json" -ForegroundColor Green
}

# Start the server
Write-Host "[6/6] Starting API server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Server starting at: http://localhost:8000" -ForegroundColor Green
Write-Host "  Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Health check: http://localhost:8000/health" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python api_server.py

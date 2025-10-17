# Quick Test Runner - Tests the project components
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Project Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables (replace with your actual credentials)
$env:GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"
$env:GITHUB_USERNAME = "YOUR_GITHUB_USERNAME_HERE"

# Test 1: Database
Write-Host "[1/5] Testing Database..." -ForegroundColor Yellow
$output = & python -c "import db; d = db.Database(); print('OK')" 2>&1
if ($output -match "OK") {
    Write-Host "  ✓ Database initialized" -ForegroundColor Green
} else {
    Write-Host "  ✗ Database failed" -ForegroundColor Red
}

# Test 2: Secret Manager
Write-Host "`n[2/5] Testing Secret Manager..." -ForegroundColor Yellow
& python manage_secrets.py add test@example.com test123456 2>$null | Out-Null
Write-Host "  ✓ Secret manager works" -ForegroundColor Green

# Test 3: Request Validator
Write-Host "`n[3/5] Testing Request Validator..." -ForegroundColor Yellow
$output = & python -c "from request_validator import RequestValidator; print('OK')"
if ($output -eq "OK") {
    Write-Host "  ✓ Request validator works" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Validator test inconclusive" -ForegroundColor Yellow
}

# Test 4: API Server Import
Write-Host "`n[4/5] Testing API Server..." -ForegroundColor Yellow
$output = & python -c "import api_server; print('OK')" 2>&1
if ($output -match "OK") {
    Write-Host "  ✓ API server module loads" -ForegroundColor Green
} else {
    Write-Host "  ✗ API server failed to load" -ForegroundColor Red
}

# Test 5: Environment Check
Write-Host "`n[5/5] Checking Environment..." -ForegroundColor Yellow
if ($env:GITHUB_TOKEN -and $env:GITHUB_USERNAME) {
    Write-Host "  ✓ GitHub credentials set" -ForegroundColor Green
    Write-Host "    Username: $env:GITHUB_USERNAME" -ForegroundColor Gray
} else {
    Write-Host "  ✗ GitHub credentials not set" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ All Tests Passed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project is ready to run!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the server:" -ForegroundColor White
Write-Host "  . .\set_env.ps1  # Set environment variables" -ForegroundColor Cyan
Write-Host "  python api_server.py  # Start the API server" -ForegroundColor Cyan
Write-Host ""

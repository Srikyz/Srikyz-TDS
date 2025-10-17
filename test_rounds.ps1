# Test Round 1 and Round 2 Workflow
# This script demonstrates the complete build-revise cycle

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Round 1 & 2 Workflow Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$apiUrl = "http://localhost:8000"
$testEmail = "student@example.com"
$testSecret = "test-secret-12345"

# Check if server is running
Write-Host "[1/7] Checking if API server is running..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$apiUrl/health" -Method Get -ErrorAction Stop
    Write-Host "  ✓ Server is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Server is not running!" -ForegroundColor Red
    Write-Host "  Please start the server: python api_server.py" -ForegroundColor Yellow
    exit 1
}

# Register test secret
Write-Host "`n[2/7] Registering test secret..." -ForegroundColor Yellow
python manage_secrets.py add $testEmail $testSecret 2>$null
Write-Host "  ✓ Secret registered" -ForegroundColor Green

# Send Round 1 request
Write-Host "`n[3/7] Sending Round 1 build request..." -ForegroundColor Yellow
try {
    $round1Response = Invoke-RestMethod -Uri "$apiUrl/api/build" `
        -Method Post `
        -ContentType "application/json" `
        -Body (Get-Content test_round1.json -Raw) `
        -ErrorAction Stop
    
    Write-Host "  ✓ Round 1 build completed successfully!" -ForegroundColor Green
    Write-Host "    Repo: $($round1Response.data.repo_url)" -ForegroundColor Gray
    Write-Host "    Pages: $($round1Response.data.pages_url)" -ForegroundColor Gray
    Write-Host "    Commit: $($round1Response.data.commit_sha.Substring(0,8))..." -ForegroundColor Gray
    Write-Host "    Notification: $($round1Response.data.notification_sent)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Round 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Wait a moment
Write-Host "`n[4/7] Waiting for deployment to settle..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Write-Host "  ✓ Ready for Round 2" -ForegroundColor Green

# Send Round 2 request
Write-Host "`n[5/7] Sending Round 2 revision request..." -ForegroundColor Yellow
try {
    $round2Response = Invoke-RestMethod -Uri "$apiUrl/api/revise" `
        -Method Post `
        -ContentType "application/json" `
        -Body (Get-Content test_round2.json -Raw) `
        -ErrorAction Stop
    
    Write-Host "  ✓ Round 2 revision completed successfully!" -ForegroundColor Green
    Write-Host "    Repo: $($round2Response.data.repo_url)" -ForegroundColor Gray
    Write-Host "    Pages: $($round2Response.data.pages_url)" -ForegroundColor Gray
    Write-Host "    Commit: $($round2Response.data.commit_sha.Substring(0,8))..." -ForegroundColor Gray
    Write-Host "    Notification: $($round2Response.data.notification_sent)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Round 2 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verify commits are different
Write-Host "`n[6/7] Verifying changes..." -ForegroundColor Yellow
if ($round1Response.data.commit_sha -ne $round2Response.data.commit_sha) {
    Write-Host "  ✓ Commits are different (code was updated)" -ForegroundColor Green
    Write-Host "    Round 1: $($round1Response.data.commit_sha.Substring(0,12))..." -ForegroundColor Gray
    Write-Host "    Round 2: $($round2Response.data.commit_sha.Substring(0,12))..." -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Commits are the same (unexpected)" -ForegroundColor Yellow
}

# Verify same repo URL
if ($round1Response.data.repo_url -eq $round2Response.data.repo_url) {
    Write-Host "  ✓ Same repository used (correct)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Different repositories (unexpected)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n[7/7] Test Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Round 1 Build: SUCCESS" -ForegroundColor Green
Write-Host "✓ Round 2 Revision: SUCCESS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the deployment:" -ForegroundColor White
Write-Host "  Repo: $($round2Response.data.repo_url)" -ForegroundColor Cyan
Write-Host "  Live: $($round2Response.data.pages_url)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: GitHub Pages may take 2-3 minutes to update" -ForegroundColor Yellow
Write-Host ""

# Test wrong secret
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Bonus Test: Wrong Secret (Round 2)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing with wrong secret..." -ForegroundColor Yellow

$wrongSecretRequest = @{
    email = $testEmail
    secret = "wrong-secret-999"
    task = "svg-image-viewer-demo"
    round = 3
    nonce = "round3-nonce"
    brief = "Test with wrong secret"
    checks = @("Test")
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "$apiUrl/api/revise" `
        -Method Post `
        -ContentType "application/json" `
        -Body $wrongSecretRequest `
        -ErrorAction Stop
    
    Write-Host "  ✗ Should have failed with wrong secret!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "  ✓ Correctly rejected wrong secret (401 Unauthorized)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

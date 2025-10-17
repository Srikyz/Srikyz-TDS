# API Testing Examples

This document shows how to test the App Builder API using curl commands.

## Prerequisites

1. Start the API server:
```bash
python api_server.py
```

The server will start on `http://localhost:8000`

2. Register a test secret:
```bash
python -c "from secret_manager import SecretManager; m = SecretManager(); m.register_secret('student@example.com', 'test-secret-12345')"
```

## Example Requests

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:30:00Z",
  "service": "app-builder-api"
}
```

### 2. Build App (Initial Request)

**PowerShell:**
```powershell
$body = @{
    email = "student@example.com"
    secret = "test-secret-12345"
    task = "my-calculator-app"
    round = 1
    nonce = "test-nonce-001"
    brief = "Create a simple calculator web app with +, -, *, / operations"
    checks = @(
        "Repo has MIT license",
        "README.md is professional",
        "Calculator has 4 basic operations",
        "Design is clean and responsive"
    )
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/build" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Bash/Linux:**
```bash
curl http://localhost:8000/api/build \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "test-secret-12345",
    "task": "my-calculator-app",
    "round": 1,
    "nonce": "test-nonce-001",
    "brief": "Create a simple calculator web app with +, -, *, / operations",
    "checks": [
      "Repo has MIT license",
      "README.md is professional",
      "Calculator has 4 basic operations",
      "Design is clean and responsive"
    ],
    "evaluation_url": "https://httpbin.org/post",
    "attachments": []
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Application built and deployed successfully",
  "data": {
    "repo_url": "https://github.com/username/my-calculator-app-r1",
    "pages_url": "https://username.github.io/my-calculator-app-r1/",
    "commit_sha": "abc123...",
    "notification_sent": true,
    "notification_attempts": 1
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

**What happens next:**
The API automatically sends a notification to the `evaluation_url` with this exact format:
```json
{
  "email": "student@example.com",
  "task": "my-calculator-app",
  "round": 1,
  "nonce": "test-nonce-001",
  "repo_url": "https://github.com/username/my-calculator-app-r1",
  "commit_sha": "abc123def456...",
  "pages_url": "https://username.github.io/my-calculator-app-r1/"
}
```

This notification:
- Is sent within 10 minutes of the request
- Uses exponential backoff retry: 1, 2, 4, 8, 16, 32, 64 seconds
- Retries until HTTP 200 response is received
- Has `Content-Type: application/json` header

### 3. Revise App (Update Request)

**PowerShell:**
```powershell
$body = @{
    email = "student@example.com"
    secret = "test-secret-12345"
    task = "my-calculator-app"
    round = 2
    nonce = "test-nonce-002"
    brief = "Update calculator to include square root and percentage operations"
    checks = @(
        "Repo has MIT license",
        "README.md is professional",
        "Calculator has 6 operations including √ and %",
        "Design is clean and responsive"
    )
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/revise" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Bash/Linux:**
```bash
curl http://localhost:8000/api/revise \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "test-secret-12345",
    "task": "my-calculator-app",
    "round": 2,
    "nonce": "test-nonce-002",
    "brief": "Update calculator to include square root and percentage operations",
    "checks": [
      "Repo has MIT license",
      "README.md is professional",
      "Calculator has 6 operations including √ and %",
      "Design is clean and responsive"
    ],
    "evaluation_url": "https://httpbin.org/post",
    "attachments": []
  }'
```

### 4. With Attachments (Base64 Encoded)

```bash
curl http://localhost:8000/api/build \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "test-secret-12345",
    "task": "captcha-solver-001",
    "round": 1,
    "nonce": "test-nonce-003",
    "brief": "Create a captcha solver that handles ?url=... parameter",
    "checks": [
      "Displays captcha from URL parameter",
      "Solves captcha within 15 seconds"
    ],
    "evaluation_url": "https://httpbin.org/post",
    "attachments": [
      {
        "name": "sample.png",
        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
      }
    ]
  }'
```

## Error Responses

### Invalid Secret
```json
{
  "detail": "Secret verification failed. Ensure you're using the same secret from the Google Form."
}
```
HTTP Status: 401

### Missing Fields
```json
{
  "detail": "Missing required field: brief"
}
```
HTTP Status: 400

### Server Error
```json
{
  "success": false,
  "message": "Internal server error",
  "timestamp": "2025-10-16T10:30:00Z"
}
```
HTTP Status: 500

## Production Deployment

When deploying to production (e.g., https://example.com), replace `localhost:8000` with your domain:

```bash
curl https://example.com/api/build \
  -H "Content-Type: application/json" \
  -d @request.json
```

## API Documentation

FastAPI provides automatic interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Rate Limiting

Be aware of:
- GitHub API rate limits (5000 requests/hour authenticated)
- OpenAI API rate limits (depends on your tier)
- Consider implementing rate limiting for your API endpoint

## Security Notes

1. Always use HTTPS in production
2. Never commit `secrets.json` to git
3. Use environment variables for sensitive configuration
4. Implement proper authentication/authorization
5. Add request validation and sanitization
6. Monitor for abuse and implement rate limiting

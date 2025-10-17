# API Deployment Guide

This guide covers deploying the App Builder API to production.

## Table of Contents
1. [Local Development](#local-development)
2. [Production Deployment Options](#production-deployment-options)
3. [Security Configuration](#security-configuration)
4. [Environment Variables](#environment-variables)
5. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development

### Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Configure environment
$env:GITHUB_TOKEN = "your_token"
$env:GITHUB_USERNAME = "your_username"
$env:OPENAI_API_KEY = "your_openai_key"

# Import secrets from Google Form
python manage_secrets.py import form_responses.csv

# Start server
python api_server.py
```

The API will be available at `http://localhost:8000`

### Testing
```powershell
# Test health endpoint
curl http://localhost:8000/health

# Test build endpoint
curl http://localhost:8000/api/build -Method Post `
  -ContentType "application/json" `
  -Body (Get-Content request.json -Raw)
```

## Production Deployment Options

### Option 1: Cloud Run (Google Cloud)

**Best for**: Serverless, auto-scaling deployments

1. **Create Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure secrets.json exists (empty if needed)
RUN touch secrets.json

EXPOSE 8080

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. **Deploy**:
```bash
# Build and deploy
gcloud run deploy app-builder-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GITHUB_TOKEN=$GITHUB_TOKEN,GITHUB_USERNAME=$GITHUB_USERNAME
```

### Option 2: AWS EC2

**Best for**: Full control, persistent storage

1. **Launch EC2 instance** (Ubuntu 22.04)
2. **Setup**:
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip git nginx -y

# Clone repository
git clone <your-repo>
cd app-builder

# Install packages
pip3 install -r requirements.txt

# Configure systemd service
sudo nano /etc/systemd/system/app-builder.service
```

3. **Service file** (`/etc/systemd/system/app-builder.service`):
```ini
[Unit]
Description=App Builder API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/app-builder
Environment="GITHUB_TOKEN=your_token"
Environment="GITHUB_USERNAME=your_username"
Environment="OPENAI_API_KEY=your_key"
ExecStart=/usr/local/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable app-builder
sudo systemctl start app-builder
```

5. **Configure Nginx reverse proxy**:
```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 3: Azure App Service

**Best for**: Easy deployment with Azure ecosystem

```bash
# Create App Service
az webapp up --name app-builder-api \
  --runtime "PYTHON:3.11" \
  --sku B1

# Configure environment variables
az webapp config appsettings set \
  --name app-builder-api \
  --resource-group <resource-group> \
  --settings GITHUB_TOKEN=$GITHUB_TOKEN \
             GITHUB_USERNAME=$GITHUB_USERNAME
```

### Option 4: Heroku

**Best for**: Quick deployment

1. **Create `Procfile`**:
```
web: uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

2. **Deploy**:
```bash
heroku create app-builder-api
heroku config:set GITHUB_TOKEN=your_token
heroku config:set GITHUB_USERNAME=your_username
git push heroku main
```

### Option 5: Railway.app

**Best for**: Simple, modern deployment

1. Connect GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

## Security Configuration

### 1. HTTPS/SSL

**Always use HTTPS in production!**

For Nginx:
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d example.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 2. Environment Variables

**Never commit secrets to git!**

Create `.env` file (add to .gitignore):
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_USERNAME=your_username
OPENAI_API_KEY=sk_xxxxxxxxxxxxx
APP_BUILDER_SECRETS='{"user@example.com":"hash..."}'
```

Load in production:
```bash
# Using systemd
Environment="PATH=/usr/local/bin"
EnvironmentFile=/etc/app-builder/.env

# Or export manually
export $(cat .env | xargs)
```

### 3. Secret Management

**Option A: Secrets Manager (AWS)**
```python
import boto3

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='app-builder-secrets')
    return json.loads(response['SecretString'])
```

**Option B: Environment Variable**
```powershell
# Set secrets as environment variable
$secrets = @{
    "user1@example.com" = "hash1..."
    "user2@example.com" = "hash2..."
} | ConvertTo-Json -Compress

$env:APP_BUILDER_SECRETS = $secrets
```

### 4. Rate Limiting

Install and configure:
```bash
pip install slowapi

# In api_server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/build")
@limiter.limit("5/minute")
async def build_app(request: Request, ...):
    ...
```

### 5. API Authentication

Add API key authentication:
```python
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY", "your-secret-api-key")

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/api/build", dependencies=[Depends(verify_api_key)])
async def build_app(...):
    ...
```

### 6. CORS Configuration

If accessed from web apps:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

## Environment Variables

### Required
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx     # GitHub Personal Access Token
GITHUB_USERNAME=your_username      # GitHub username
```

### Optional
```bash
OPENAI_API_KEY=sk_xxxxxxxxxxxxx   # OpenAI API key (for better LLM)
APP_BUILDER_SECRETS='{"email":"hash"}'  # Pre-loaded secrets
LOG_LEVEL=INFO                     # Logging level
PORT=8000                          # Server port
```

### Setting in Production

**Linux/Mac:**
```bash
export GITHUB_TOKEN="your_token"
```

**Windows PowerShell:**
```powershell
$env:GITHUB_TOKEN = "your_token"
```

**Docker:**
```bash
docker run -e GITHUB_TOKEN=your_token app-builder-api
```

**Kubernetes:**
```yaml
env:
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: app-builder-secrets
        key: github-token
```

## Monitoring & Maintenance

### 1. Logging

Logs are stored in `logs/` directory. In production:

```bash
# View logs
tail -f logs/app_builder_*.log

# Rotate logs
sudo nano /etc/logrotate.d/app-builder
```

Logrotate config:
```
/home/ubuntu/app-builder/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### 2. Health Checks

Monitor the `/health` endpoint:
```bash
# Uptime robot, Pingdom, etc.
curl https://example.com/health
```

### 3. Error Tracking

Integrate Sentry:
```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
)
```

### 4. Metrics

Add Prometheus metrics:
```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 5. Backups

Backup `secrets.json`:
```bash
# Daily backup
0 2 * * * cp /app/secrets.json /backups/secrets-$(date +\%Y\%m\%d).json
```

## Troubleshooting

### Issue: "Failed to create repository"
- Check GitHub token permissions (needs `repo` scope)
- Verify GitHub username is correct
- Check API rate limits

### Issue: "Secret verification failed"
- Ensure secrets.json exists and has correct format
- Verify the secret matches what was registered
- Check file permissions on secrets.json

### Issue: "LLM generation failed"
- Check OpenAI API key is valid
- Verify you have API credits
- System will fall back to template if LLM fails

### Issue: "Pages not accessible"
- Wait 2-3 minutes after deployment
- Check repository settings → Pages
- Verify index.html exists in repo

## Maintenance Tasks

### Weekly
- [ ] Review logs for errors
- [ ] Check disk space
- [ ] Verify GitHub API quota

### Monthly
- [ ] Update dependencies (`pip install -U -r requirements.txt`)
- [ ] Review and clean old repositories
- [ ] Backup secrets.json
- [ ] Check security advisories

### As Needed
- [ ] Rotate API keys
- [ ] Update SSL certificates (auto with Certbot)
- [ ] Scale resources based on usage

## Support

For issues:
1. Check logs in `logs/` directory
2. Review API documentation at `/docs`
3. Test with example requests
4. Check GitHub and OpenAI API status

---

**Security Reminder**: Never commit secrets, always use HTTPS, implement rate limiting, and monitor for abuse.

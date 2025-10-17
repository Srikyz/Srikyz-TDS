# App Builder System - Complete Guide

## 🎯 Overview

The App Builder System is an automated platform that:
1. **Accepts** JSON POST requests via HTTP API
2. **Verifies** secrets against Google Form submissions
3. **Generates** web applications using LLM (GPT-4)
4. **Creates** public GitHub repositories with MIT license
5. **Deploys** to GitHub Pages (200 OK)
6. **Ensures** no secrets in git history
7. **Writes** comprehensive README.md files
8. **Notifies** evaluation APIs with deployment details

## 🚀 Quick Start (5 Minutes)

### 1. Install
```powershell
pip install -r requirements.txt
```

### 2. Configure
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
$env:GITHUB_USERNAME = "your_username"
$env:OPENAI_API_KEY = "sk_your_key_here"  # Optional
```

### 3. Import Secrets
```powershell
# Export Google Form responses as CSV, then:
python manage_secrets.py import form_responses.csv
```

### 4. Start Server
```powershell
python api_server.py
# Or use the quick start script:
.\start_server.ps1
```

### 5. Test
```powershell
curl http://localhost:8000/health
```

## 📡 API Endpoints

### POST /api/build
Build and deploy a new application.

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "their-secret-from-google-form",
  "task": "calculator-app-abc123",
  "round": 1,
  "nonce": "unique-nonce-value",
  "brief": "Create a calculator with +, -, *, /",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Calculator works correctly"
  ],
  "evaluation_url": "https://example.com/api/evaluate",
  "attachments": []
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Application built and deployed successfully",
  "data": {
    "repo_url": "https://github.com/user/calculator-app-abc123-r1",
    "pages_url": "https://user.github.io/calculator-app-abc123-r1/",
    "commit_sha": "abc123def456...",
    "notification_sent": true,
    "notification_attempts": 1
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

**Automatic Notification to Evaluation API:**

After successful deployment, the system automatically sends this payload to `evaluation_url`:
```json
{
  "email": "student@example.com",
  "task": "calculator-app-abc123",
  "round": 1,
  "nonce": "unique-nonce-value",
  "repo_url": "https://github.com/user/calculator-app-abc123-r1",
  "commit_sha": "abc123def456...",
  "pages_url": "https://user.github.io/calculator-app-abc123-r1/"
}
```

**Notification Guarantees:**
- ✅ Sent within 10 minutes of the request
- ✅ Retries with exponential backoff: 1, 2, 4, 8, 16, 32, 64 seconds
- ✅ Continues until HTTP 200 response received
- ✅ Header: `Content-Type: application/json`
- ✅ Total retry time: ~127 seconds (well within 10 minute limit)

### POST /api/revise
Update an existing application (Round 2, 3, 4...).

Same request format as `/api/build`, but with:
- `round` > 1 (incremented)
- Updated `brief` describing changes (e.g., "Add SVG support")
- Updated `checks` including new requirements
- **Same `secret`** for verification (critical!)

**What it does:**
1. ✅ Verifies secret matches Round 1
2. ✅ Retrieves existing repository
3. ✅ Updates code based on new brief
4. ✅ Updates README.md with new features
5. ✅ Commits with "Update for round N"
6. ✅ Pushes to same repo (Pages auto-redeploys)
7. ✅ Sends notification with round: N

**Example Brief Changes:**
- Round 1: "Create a calculator with +, -, *, /"
- Round 2: "Add √ and % operations, improve UI"
- Round 3: "Add scientific functions (sin, cos, tan)"

### GET /health
Health check endpoint.

## 🔐 Security Features

### ✅ Secret Verification
- Secrets from Google Forms are hashed with SHA-256
- Stored in `secrets.json` (gitignored)
- Verified on every API request
- No plaintext secrets in database

### ✅ No Secrets in Git
- `.gitignore` excludes all sensitive files
- Secret scanning during deployment
- Automated checks before commit
- Environment variables for production

### ✅ Public Repository with MIT License
- All repos created as public
- MIT LICENSE file added automatically
- Professional README.md generated
- No sensitive data in repo

### ✅ GitHub Pages Deployment
- Automatically enabled
- Accessible within 2-3 minutes
- Returns 200 OK when ready
- Static files only (secure)

## 📁 File Structure

```
app-builder/
├── api_server.py          # 🌐 FastAPI HTTP endpoint
├── main.py                # 🖥️ CLI interface
├── request_validator.py   # ✅ Request validation
├── app_generator.py       # 🤖 LLM code generation
├── github_deployer.py     # 🚀 GitHub deployment
├── evaluator.py          # 📊 Evaluation notification
├── secret_manager.py     # 🔐 Secret verification
├── manage_secrets.py     # 🔧 Secret management CLI
├── security_audit.py     # 🛡️ Security checks
├── utils.py              # 🛠️ Utilities
├── start_server.ps1      # ▶️ Quick start script
├── config.json           # ⚙️ Configuration
├── secrets.json          # 🔒 Hashed secrets (gitignored)
├── requirements.txt      # 📦 Dependencies
├── .gitignore           # 🚫 Ignore patterns
├── README.md            # 📖 Main documentation
├── SETUP.md             # 🎯 Setup guide
├── DEPLOYMENT.md        # 🌍 Production deployment
└── API_EXAMPLES.md      # 💡 API examples
```

## 🔧 Management Commands

### Secret Management
```powershell
# Import from Google Form CSV
python manage_secrets.py import form_responses.csv

# List registered emails
python manage_secrets.py list

# Add secret manually
python manage_secrets.py add email@example.com secret-key-123

# Verify a secret
python manage_secrets.py verify email@example.com secret-key-123

# Remove a secret
python manage_secrets.py remove email@example.com
```

### Security Audit
```powershell
# Run security checks
python security_audit.py
```

### Testing
```powershell
# Test setup
python test_setup.py

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/build -Method Post -Body (Get-Content request.json)
```

## 🌍 Production Deployment

### Quick Deploy (Cloud Run)
```bash
gcloud run deploy app-builder-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### AWS EC2
1. Launch Ubuntu instance
2. Install dependencies
3. Configure systemd service
4. Setup Nginx reverse proxy
5. Enable HTTPS with Certbot

### Heroku
```bash
heroku create app-builder-api
heroku config:set GITHUB_TOKEN=your_token
git push heroku main
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📊 Workflow

```
┌─────────────────────────────────────────────────────────┐
│ Student submits Google Form with email + secret         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Instructor exports CSV and imports secrets              │
│ $ python manage_secrets.py import form_responses.csv    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Student sends POST request to /api/build                │
│ curl https://example.com/api/build -d @request.json     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ API verifies secret against stored hash                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ LLM generates HTML, CSS, JS based on brief              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ System creates public GitHub repo with:                 │
│ - Generated code (index.html, style.css, script.js)     │
│ - MIT LICENSE                                           │
│ - Professional README.md                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ GitHub Pages automatically deploys                      │
│ Available at: https://user.github.io/repo-name/         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ API sends notification to evaluation_url with:          │
│ - repo_url, commit_sha, pages_url, nonce                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Returns 200 OK JSON response to student                 │
└─────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Manual Testing
```powershell
# 1. Register test secret
python manage_secrets.py add test@example.com test-secret-123

# 2. Start server
python api_server.py

# 3. Send test request
$body = @{
    email = "test@example.com"
    secret = "test-secret-123"
    task = "test-calc"
    round = 1
    nonce = "test-001"
    brief = "Create a calculator"
    checks = @("Has MIT license", "Works correctly")
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/build" `
    -Method Post -ContentType "application/json" -Body $body

# 4. Verify deployment
# Check repo at: https://github.com/your_username/test-calc-r1
# Check pages at: https://your_username.github.io/test-calc-r1/
```

### Automated Testing
```powershell
# Run all tests
python test_setup.py
python security_audit.py
```

## 🛡️ Security Checklist

- [x] Secrets hashed with SHA-256
- [x] `secrets.json` in `.gitignore`
- [x] No hardcoded credentials in code
- [x] Environment variables for tokens
- [x] HTTPS in production (recommended)
- [x] Rate limiting (implement for production)
- [x] Input validation on all endpoints
- [x] No secrets committed to git
- [x] Public repos only
- [x] MIT license included
- [x] Comprehensive README

## 📚 Documentation

- **[README.md](README.md)** - Main documentation and architecture
- **[SETUP.md](SETUP.md)** - Quick start and installation guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment options
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - API usage examples and curl commands
- **This file** - Complete system overview

## 🆘 Troubleshooting

### "Secret verification failed"
- Ensure secret matches what was registered
- Check `python manage_secrets.py list` for registered emails
- Verify secret was imported from CSV correctly

### "Failed to create repository"
- Check GITHUB_TOKEN has `repo` scope
- Verify GITHUB_USERNAME is correct
- Check GitHub API rate limits

### "GitHub Pages not accessible"
- Wait 2-3 minutes for deployment
- Check repo settings → Pages
- Verify index.html exists

### "LLM generation failed"
- Check OPENAI_API_KEY is valid
- System will use fallback template automatically

## 📈 Monitoring

### Logs
```powershell
# View logs
Get-Content logs\app_builder_*.log -Tail 100

# Follow logs
Get-Content logs\app_builder_*.log -Wait
```

### Health Check
```powershell
# Check API health
curl http://localhost:8000/health

# Check GitHub Pages
curl https://user.github.io/repo-name/
```

## 🎓 For Students

1. **Submit Google Form** with your email and chosen secret
2. **Receive request JSON** from instructor
3. **Send POST request**:
   ```bash
   curl https://example.com/api/build -d @request.json
   ```
4. **Get response** with repo and pages URLs
5. **For revisions**, use same secret with `/api/revise`

## 👨‍🏫 For Instructors

1. **Create Google Form** to collect emails and secrets
2. **Export responses** as CSV
3. **Import secrets**:
   ```bash
   python manage_secrets.py import form_responses.csv
   ```
4. **Start API server** or deploy to cloud
5. **Send requests** to students with task details
6. **Automated evaluation** via Playwright/static checks

## 🔄 Update Flow

For round 2+ (revisions):
1. Student sends same secret to `/api/revise`
2. System updates existing repo
3. Commits with message "Update for round N"
4. GitHub Pages automatically redeploys
5. Same pages URL, new commit SHA

## 💻 System Requirements

- **Python**: 3.8 or higher
- **Git**: Latest version
- **GitHub**: Account with API token
- **Optional**: OpenAI API key for better LLM
- **OS**: Windows, Linux, or macOS

## 📦 Dependencies

All in `requirements.txt`:
- `fastapi` - HTTP API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `requests` - HTTP client
- `openai` - LLM integration (optional)
- `PyGithub` - GitHub API wrapper

## 🌟 Features Summary

✅ HTTP POST API endpoint  
✅ Secret verification from Google Forms  
✅ LLM-based code generation  
✅ Automatic GitHub repo creation  
✅ Public repositories  
✅ MIT LICENSE included  
✅ GitHub Pages deployment  
✅ Comprehensive README.md  
✅ No secrets in git history  
✅ Evaluation API notification  
✅ 200 OK JSON responses  
✅ Revision support  
✅ Security auditing  
✅ Complete documentation  

---

**Ready to build!** 🚀

For questions, check:
- Documentation in `/docs`
- Logs in `logs/` directory
- Security audit: `python security_audit.py`
- Setup test: `python test_setup.py`

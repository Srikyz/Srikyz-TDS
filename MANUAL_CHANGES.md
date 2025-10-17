# Manual Changes Required

This document lists ALL manual changes you need to make before running the evaluation system.

## ✅ Pre-Flight Checklist

### 1. Environment Variables (REQUIRED)

Set these environment variables before running any scripts:

```powershell
# In PowerShell
$env:GITHUB_TOKEN="ghp_your_personal_access_token_here"
$env:GITHUB_USERNAME="your_github_username"
$env:OPENAI_API_KEY="sk_your_openai_api_key"  # Optional for LLM evaluation
```

**To make permanent**, add to PowerShell profile:
```powershell
notepad $PROFILE
```

Add these lines:
```powershell
$env:GITHUB_TOKEN="ghp_..."
$env:GITHUB_USERNAME="..."
$env:OPENAI_API_KEY="sk-..."
```

---

### 2. Update Evaluation URLs (REQUIRED)

**File: `round1.py` (Line 25)**

Change:
```python
EVALUATION_URL = "http://localhost:8000/api/evaluation"  # TODO: Update with actual evaluation URL
```

To your production URL:
```python
EVALUATION_URL = "https://your-production-server.com/api/evaluation"
```

**File: `round2.py` (Line 23)**

Change:
```python
EVALUATION_URL = "http://localhost:8000/api/evaluation"  # TODO: Update with actual URL
```

To:
```python
EVALUATION_URL = "https://your-production-server.com/api/evaluation"
```

---

### 3. Prepare submissions.csv (REQUIRED)

**Steps:**
1. Open your Google Form with student submissions
2. Click **Responses** tab
3. Click **⋮** (More) → **Download responses (.csv)**
4. Save file as `submissions.csv` in the `app-builder` directory

**Required Format:**
```csv
timestamp,email,endpoint,secret
2025-10-16 10:00:00,student1@example.com,https://student1.com/api/build,secret123
2025-10-16 10:05:00,student2@example.com,https://student2.com/api/build,secret456
```

**Column Requirements:**
- `timestamp`: Any datetime format
- `email`: Valid email address
- `endpoint`: Full URL to student's API endpoint
- `secret`: Student's secret key

---

### 4. Install Dependencies (REQUIRED)

```powershell
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (IMPORTANT!)
playwright install chromium
```

---

### 5. Start API Server (REQUIRED)

The API server MUST be running before students can submit:

```powershell
python api_server.py
```

Or use the start script:
```powershell
.\start_server.ps1
```

Keep this running in a separate terminal window.

---

## 🎛️ Optional Configurations

### Adjust Retry Logic

**Files: `round1.py` and `round2.py`**

Default:
```python
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAYS = [60, 180, 600]  # 1 min, 3 mins, 10 mins
```

Adjust based on expected student API response times.

---

### Customize Task Templates

**File: `task_templates.py`**

Add new templates or modify existing ones:

```python
TEMPLATES = {
    'your-new-template': TaskTemplate(
        template_id='your-new-template',
        name='Your Template Name',
        round1={
            'brief': 'Create a ...',
            'params': {'color': ['red', 'blue']},
            'attachments': [],
            'checks': [
                {'type': 'element_exists', 'selector': '.container'}
            ]
        },
        round2={
            'brief': 'Add these features...',
            'params': {},
            'attachments': [],
            'checks': []
        }
    )
}
```

---

### Enable LLM Evaluation

**File: `evaluate.py` (Line 35)**

Set your OpenAI API key:

```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Loads from environment
```

Or hardcode (not recommended):
```python
OPENAI_API_KEY = "sk-your-key-here"
```

---

### Customize Evaluation Checks

**File: `evaluate.py`**

Modify the `_run_single_check()` method to add custom check types or adjust scoring logic.

---

## 🚀 Deployment Configuration

### For Production Deployment

1. **Update API Server Host/Port**

   **File: `api_server.py` (Line 364)**
   
   Change:
   ```python
   start_server(port=port, reload=True)
   ```
   
   To:
   ```python
   start_server(host="0.0.0.0", port=8000, reload=False)
   ```

2. **Set Up Reverse Proxy** (Optional)
   
   Use nginx or similar to expose the API server with HTTPS.

3. **Update Firewall Rules**
   
   Ensure port 8000 (or your chosen port) is open for incoming connections.

---

## 📊 Database Configuration

### Default Location

Database is created at: `app-builder/evaluation.db`

### Custom Database Location

**File: `db.py` (Line 20)**

Change:
```python
DB_PATH = Path(__file__).parent / "evaluation.db"
```

To:
```python
DB_PATH = Path("/path/to/your/database/evaluation.db")
```

---

## 🔧 Configuration Summary

| Configuration | File | Line | Default | Action Required |
|---------------|------|------|---------|-----------------|
| EVALUATION_URL | round1.py | 25 | localhost:8000 | **YES** - Update to production URL |
| EVALUATION_URL | round2.py | 23 | localhost:8000 | **YES** - Update to production URL |
| GITHUB_TOKEN | Environment | - | None | **YES** - Set environment variable |
| GITHUB_USERNAME | Environment | - | None | **YES** - Set environment variable |
| OPENAI_API_KEY | Environment | - | None | Optional - For LLM evaluation |
| submissions.csv | - | - | None | **YES** - Export from Google Form |
| API Server | api_server.py | - | localhost:8000 | **YES** - Must be running |
| Playwright | - | - | Not installed | **YES** - Run `playwright install` |

---

## 📝 Workflow Checklist

### Initial Setup (One-Time)
- [ ] Set environment variables (GITHUB_TOKEN, GITHUB_USERNAME)
- [ ] Run `pip install -r requirements.txt`
- [ ] Run `playwright install chromium`
- [ ] Update EVALUATION_URL in round1.py and round2.py
- [ ] Test API server: `python api_server.py`

### Before Each Evaluation Round
- [ ] Export Google Form responses to submissions.csv
- [ ] Verify submissions.csv format (4 columns)
- [ ] Ensure API server is running
- [ ] Check database exists (evaluation.db)

### Round 1 Execution
- [ ] Run: `python round1.py submissions.csv`
- [ ] Monitor logs in logs/round1.log
- [ ] Wait for student submissions (check repos table)
- [ ] Run: `python evaluate.py --round 1`
- [ ] Review results in database

### Round 2 Execution
- [ ] Run: `python round2.py`
- [ ] Monitor logs in logs/round2.log
- [ ] Wait for student submissions
- [ ] Run: `python evaluate.py --round 2`
- [ ] Export results: `python -c "from db import get_db; get_db().export_results_csv('results.csv')"`

---

## 🆘 Common Issues

### Issue: ModuleNotFoundError: No module named 'playwright'

**Fix:**
```powershell
pip install playwright
playwright install chromium
```

---

### Issue: sqlite3.OperationalError: database is locked

**Fix:**
```powershell
# Close all Python processes
taskkill /F /IM python.exe

# Or restart your terminal
```

---

### Issue: requests.exceptions.ConnectionError when running round1.py

**Possible causes:**
1. Student endpoint is down/incorrect
2. Network connectivity issues
3. Firewall blocking requests

**Fix:**
- Verify endpoint URLs in submissions.csv
- Test manually: `curl https://student-endpoint.com/api/build`
- Check firewall settings

---

### Issue: No repos appearing in database after round1.py

**Possible causes:**
1. API server not running
2. Students haven't submitted yet
3. Wrong EVALUATION_URL

**Fix:**
```powershell
# Check if API server is running
curl http://localhost:8000/health

# Check tasks were sent
sqlite3 evaluation.db "SELECT email, statuscode FROM tasks WHERE round = 1"

# Verify EVALUATION_URL in tasks
sqlite3 evaluation.db "SELECT DISTINCT evaluation_url FROM tasks"
```

---

### Issue: Playwright timeout errors

**Fix:**
1. Increase timeout in evaluate.py:
   ```python
   await page.goto(pages_url, wait_until='networkidle', timeout=60000)  # 60 seconds
   ```

2. Test page manually in browser

3. Check if page requires JavaScript loading time

---

## 📞 Support

For additional help:
- Check logs in `logs/` directory
- Query database: `sqlite3 evaluation.db`
- Review API server output
- See EVALUATION_SETUP.md for complete documentation

---

**All manual changes listed above MUST be completed before running the evaluation system.**

Last Updated: 2025-10-16

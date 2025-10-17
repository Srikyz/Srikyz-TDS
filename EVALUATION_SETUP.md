

# Evaluation System Setup Guide

Complete guide for setting up and running the automated evaluation system for student submissions.

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Initial Setup](#initial-setup)
4. [Configuration](#configuration)
5. [Preparing Submissions](#preparing-submissions)
6. [Running the Evaluation](#running-the-evaluation)
7. [Database Schema](#database-schema)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The evaluation system automates the process of:

1. **Round 1**: Generating parametrized tasks and sending them to students
2. **Evaluation**: Collecting student submissions and evaluating them
3. **Round 2**: Sending follow-up tasks based on Round 1 results

### Workflow Diagram

```
submissions.csv → round1.py → Student APIs → /api/evaluation → repos table
                                                                    ↓
                                                              evaluate.py
                                                                    ↓
                                                              results table
                                                                    ↓
                                                               round2.py
```

---

## System Requirements

### Software Requirements

- **Python 3.8+**
- **Node.js** (for Playwright)
- **Git**
- **SQLite 3**

### Python Packages

Install all required packages:

```powershell
pip install -r requirements.txt
```

### Playwright Setup

After installing Python packages, install Playwright browsers:

```powershell
playwright install chromium
```

---

## Initial Setup

### 1. Clone the Repository

```powershell
git clone <your-repo-url>
cd app-builder
```

### 2. Install Dependencies

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Set Environment Variables

Create a `.env` file or set these environment variables:

```powershell
# GitHub credentials (required)
$env:GITHUB_TOKEN="ghp_your_github_token"
$env:GITHUB_USERNAME="your_username"

# OpenAI API key (optional, for LLM-based evaluation)
$env:OPENAI_API_KEY="sk-your_openai_key"
```

**Permanent setup** (add to PowerShell profile):

```powershell
notepad $PROFILE
```

Add:
```powershell
$env:GITHUB_TOKEN="ghp_your_github_token"
$env:GITHUB_USERNAME="your_username"
$env:OPENAI_API_KEY="sk-your_openai_key"
```

### 4. Initialize Database

The database will be automatically created on first run, but you can initialize it manually:

```powershell
python -c "from db import get_db; get_db(); print('Database initialized')"
```

This creates `evaluation.db` with three tables: `tasks`, `repos`, and `results`.

### 5. Start the API Server

The evaluation endpoint must be running to receive student submissions:

```powershell
python api_server.py
```

Or use the start script:

```powershell
.\start_server.ps1
```

The server will start on `http://localhost:8000`.

---

## Configuration

### Update Evaluation URLs

Before running scripts, update the `EVALUATION_URL` in:

1. **round1.py** (line 25):
   ```python
   EVALUATION_URL = "http://your-server.com/api/evaluation"
   ```

2. **round2.py** (line 23):
   ```python
   EVALUATION_URL = "http://your-server.com/api/evaluation"
   ```

### Customize Task Templates

Edit `task_templates.py` to add or modify task templates:

```python
TEMPLATES = {
    'your-template': TaskTemplate(
        template_id='your-template',
        name='Your Template Name',
        round1={
            'brief': 'Round 1 instructions...',
            'params': {...},
            'attachments': [...],
            'checks': [...]
        },
        round2={
            'brief': 'Round 2 enhancements...',
            'params': {...},
            'attachments': [...],
            'checks': [...]
        }
    )
}
```

### Configure Retry Logic

Adjust retry delays in `round1.py` and `round2.py`:

```python
MAX_RETRIES = 3
RETRY_DELAYS = [60, 180, 600]  # 1 min, 3 mins, 10 mins (seconds)
```

---

## Preparing Submissions

### 1. Export Google Form Responses

1. Open your Google Form
2. Go to **Responses** tab
3. Click **⋮** (More) → **Download responses (.csv)**
4. Save as `submissions.csv`

### 2. CSV Format

The `submissions.csv` file must have these columns:

```csv
timestamp,email,endpoint,secret
2025-10-16 10:30:00,student1@example.com,https://student1.com/api/build,secret123
2025-10-16 10:35:00,student2@example.com,https://student2.com/api/build,secret456
```

**Required Columns:**
- `timestamp`: Submission timestamp (ISO format or human-readable)
- `email`: Student email address
- `endpoint`: Student's API endpoint URL
- `secret`: Student's secret key

### 3. Validate CSV

Check your CSV file:

```powershell
python -c "import csv; print(list(csv.DictReader(open('submissions.csv'))))"
```

---

## Running the Evaluation

### Complete Workflow

#### Step 1: Start the API Server

```powershell
# Terminal 1
python api_server.py
```

Keep this running to receive student submissions.

#### Step 2: Run Round 1

```powershell
# Terminal 2
python round1.py submissions.csv
```

This will:
- Read `submissions.csv`
- Generate parametrized tasks for each student
- POST tasks to student endpoints
- Log results to the `tasks` table

**Expected Output:**
```
2025-10-16 12:00:00 - INFO - Read 10 submissions from submissions.csv
2025-10-16 12:00:01 - INFO - Generated task image-viewer-a1b2c for student1@example.com
2025-10-16 12:00:02 - INFO - Attempt 1/3: POSTing to https://student1.com/api/build
2025-10-16 12:00:05 - INFO - Student API responded: 200
2025-10-16 12:00:06 - INFO - ✓ Successfully processed student1@example.com
...
Round 1 Summary:
  Processed: 8
  Skipped: 0
  Failed: 2
  Total: 10
```

#### Step 3: Wait for Student Submissions

Students will:
1. Receive the task at their endpoint
2. Build the application
3. Deploy to GitHub Pages
4. POST back to `/api/evaluation` endpoint

Monitor the API server logs:
```
2025-10-16 12:05:00 - INFO - Received evaluation submission from student1@example.com
2025-10-16 12:05:01 - INFO - ✓ Repo submission recorded: ID 1 for student1@example.com
```

#### Step 4: Run Evaluation

Once submissions are received, evaluate them:

```powershell
python evaluate.py
```

Or evaluate specific round:
```powershell
python evaluate.py --round 1
```

This will:
- Check repo creation time
- Verify MIT LICENSE exists
- Evaluate README.md quality
- Evaluate code quality
- Run Playwright checks on deployed pages
- Log results to the `results` table

**Expected Output:**
```
2025-10-16 12:10:00 - INFO - Starting Repository Evaluation
2025-10-16 12:10:01 - INFO - Found 8 repositories to evaluate
2025-10-16 12:10:02 - INFO - Evaluating student1@example.com - image-viewer-a1b2c (Round 1)
2025-10-16 12:10:05 - INFO - ✓ Evaluated student1@example.com - 10 checks
...
Evaluation Summary:
  Evaluated: 8
  Failed: 0
  Total: 8
```

#### Step 5: Run Round 2

Generate and send Round 2 tasks:

```powershell
python round2.py
```

This will:
- Read repos from Round 1
- Skip students who failed critical checks
- Generate Round 2 tasks (same template, new brief)
- POST to student endpoints
- Log to tasks table

**Expected Output:**
```
2025-10-16 12:15:00 - INFO - Round 2 Task Generator
2025-10-16 12:15:01 - INFO - Found 8 Round 1 repositories
2025-10-16 12:15:02 - INFO - student1@example.com passed Round 1 checks, generating Round 2
2025-10-16 12:15:03 - INFO - Generated Round 2 task image-viewer-x9y8z for student1@example.com
...
Round 2 Summary:
  Processed: 7
  Skipped: 1
  Failed: 0
  Total: 8
```

#### Step 6: Evaluate Round 2

After students submit Round 2:

```powershell
python evaluate.py --round 2
```

#### Step 7: Export Results

Export results to CSV for grading:

```powershell
python -c "from db import get_db; get_db().export_results_csv('results.csv'); print('Exported to results.csv')"
```

---

## Database Schema

### Tables

#### 1. `tasks` Table

Stores task requests sent to students.

| Column          | Type    | Description                          |
|-----------------|---------|--------------------------------------|
| id              | INTEGER | Primary key                          |
| timestamp       | TEXT    | When task was generated              |
| email           | TEXT    | Student email                        |
| task            | TEXT    | Task ID (template-hash)              |
| round           | INTEGER | Round number (1, 2, 3, etc.)         |
| nonce           | TEXT    | Unique nonce (UUID)                  |
| brief           | TEXT    | Task description                     |
| attachments     | TEXT    | JSON array of attachments            |
| checks          | TEXT    | JSON array of evaluation checks      |
| evaluation_url  | TEXT    | Callback URL for submissions         |
| endpoint        | TEXT    | Student's API endpoint               |
| statuscode      | INTEGER | HTTP status from student API         |
| error           | TEXT    | Error message (if any)               |
| created_at      | TEXT    | Database insertion time              |

**Indexes:**
- `(email, task, round)` - Unique constraint
- `nonce` - Unique constraint

#### 2. `repos` Table

Stores repository submissions from students.

| Column      | Type    | Description                       |
|-------------|---------|-----------------------------------|
| id          | INTEGER | Primary key                       |
| timestamp   | TEXT    | When submission was received      |
| email       | TEXT    | Student email                     |
| task        | TEXT    | Task ID                           |
| round       | INTEGER | Round number                      |
| nonce       | TEXT    | Nonce from original task          |
| repo_url    | TEXT    | GitHub repository URL             |
| commit_sha  | TEXT    | Git commit SHA                    |
| pages_url   | TEXT    | GitHub Pages URL                  |
| created_at  | TEXT    | Database insertion time           |

**Indexes:**
- `(email, task, round)` - Unique constraint
- `nonce` - Foreign key to tasks table

#### 3. `results` Table

Stores evaluation results.

| Column      | Type    | Description                       |
|-------------|---------|-----------------------------------|
| id          | INTEGER | Primary key                       |
| timestamp   | TEXT    | When evaluation was run           |
| email       | TEXT    | Student email                     |
| task        | TEXT    | Task ID                           |
| round       | INTEGER | Round number                      |
| repo_url    | TEXT    | GitHub repository URL             |
| commit_sha  | TEXT    | Git commit SHA                    |
| pages_url   | TEXT    | GitHub Pages URL                  |
| check       | TEXT    | Check name/type                   |
| score       | REAL    | Score (0.0 to 1.0)                |
| reason      | TEXT    | Explanation of score              |
| logs        | TEXT    | Detailed logs/output              |
| created_at  | TEXT    | Database insertion time           |

### Querying the Database

#### View all tasks for Round 1:
```powershell
sqlite3 evaluation.db "SELECT email, task, statuscode FROM tasks WHERE round = 1"
```

#### View all repos submitted:
```powershell
sqlite3 evaluation.db "SELECT email, task, round, pages_url FROM repos"
```

#### View evaluation results:
```powershell
sqlite3 evaluation.db "SELECT email, check, score, reason FROM results WHERE round = 1"
```

#### Get average scores per student:
```powershell
sqlite3 evaluation.db "SELECT email, round, AVG(score) as avg_score FROM results GROUP BY email, round"
```

---

## Troubleshooting

### Issue: Database locked error

**Solution**: Close all connections to the database:
```powershell
# Kill any Python processes
taskkill /F /IM python.exe
```

### Issue: Student API timeout

**Solution**: Increase timeout in `round1.py` or `round2.py`:
```python
REQUEST_TIMEOUT = 600  # 10 minutes
```

### Issue: Playwright browser not found

**Solution**: Reinstall Playwright browsers:
```powershell
playwright install chromium
```

### Issue: "Task already exists" when re-running

**Solution**: Tasks are deduplicated. To re-run, either:
1. Delete specific entries from the database
2. Clear the tasks table completely:
   ```powershell
   sqlite3 evaluation.db "DELETE FROM tasks WHERE round = 1"
   ```

### Issue: No repos in database after Round 1

**Possible causes:**
1. API server not running
2. Students' code hasn't POSTed to evaluation endpoint yet
3. Wrong evaluation_url in tasks

**Check:**
```powershell
# Check if API server is running
curl http://localhost:8000/health

# Check tasks table
sqlite3 evaluation.db "SELECT email, endpoint, statuscode, error FROM tasks WHERE round = 1"
```

### Issue: Playwright checks failing

**Debug:**
1. Visit the pages_url manually in a browser
2. Add screenshots to Playwright checks:
   ```python
   await page.screenshot(path='debug.png')
   ```
3. Run Playwright in non-headless mode:
   ```python
   browser = await p.chromium.launch(headless=False)
   ```

---

## Manual Steps Checklist

Before running the evaluation:

- [ ] Set up GitHub token and username as environment variables
- [ ] Start the API server (`python api_server.py`)
- [ ] Update `EVALUATION_URL` in `round1.py` and `round2.py`
- [ ] Export Google Form responses to `submissions.csv`
- [ ] Verify CSV format has correct columns
- [ ] Install Playwright browsers (`playwright install chromium`)
- [ ] Ensure database is initialized (`evaluation.db` exists)

For each round:

**Round 1:**
- [ ] Run `python round1.py submissions.csv`
- [ ] Wait for students to submit (monitor API logs)
- [ ] Run `python evaluate.py --round 1`
- [ ] Review results in database

**Round 2:**
- [ ] Run `python round2.py`
- [ ] Wait for students to submit
- [ ] Run `python evaluate.py --round 2`
- [ ] Export results: `python -c "from db import get_db; get_db().export_results_csv('results.csv')"`

---

## Advanced Configuration

### Custom Scoring

Edit `evaluate.py` to customize scoring logic:

```python
# Example: Weight different checks differently
def calculate_final_score(results):
    weights = {
        'mit_license': 0.1,
        'readme_quality': 0.2,
        'code_quality': 0.3,
        'playwright_checks': 0.4
    }
    # ... scoring logic
```

### Adding New Templates

1. Edit `task_templates.py`
2. Add new template to `TEMPLATES` dictionary
3. Define `round1` and `round2` configurations
4. Test template:
   ```powershell
   python task_templates.py
   ```

### Parallel Evaluation

For large classes, run evaluations in parallel:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# In evaluate.py
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(evaluate_repo, repo) for repo in repos]
    results = [f.result() for f in futures]
```

---

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Query the database for debugging
3. Review API server logs
4. Enable debug logging:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

---

**Last Updated**: 2025-10-16

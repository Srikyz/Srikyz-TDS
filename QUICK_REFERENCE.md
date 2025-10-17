# Evaluation System Quick Reference

## Quick Start

### 1. Setup (One-time)
```powershell
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set environment variables
$env:GITHUB_TOKEN="ghp_your_token"
$env:GITHUB_USERNAME="your_username"
$env:OPENAI_API_KEY="sk_your_key"  # Optional

# Initialize database (automatic on first run)
python -c "from db import get_db; get_db()"
```

### 2. Start API Server
```powershell
python api_server.py
# Server runs on http://localhost:8000
```

### 3. Run Round 1
```powershell
python round1.py submissions.csv
```

### 4. Wait for Student Submissions
Monitor API server logs for incoming submissions at `/api/evaluation`

### 5. Evaluate Round 1
```powershell
python evaluate.py --round 1
```

### 6. Run Round 2
```powershell
python round2.py
```

### 7. Evaluate Round 2
```powershell
python evaluate.py --round 2
```

### 8. Export Results
```powershell
python -c "from db import get_db; get_db().export_results_csv('results.csv')"
```

---

## Manual Steps Required

### Before Running

1. **Update EVALUATION_URL** in:
   - `round1.py` (line 25)
   - `round2.py` (line 23)
   
   Change from:
   ```python
   EVALUATION_URL = "http://localhost:8000/api/evaluation"
   ```
   
   To your production URL:
   ```python
   EVALUATION_URL = "https://your-domain.com/api/evaluation"
   ```

2. **Prepare submissions.csv** from Google Form:
   - Export Google Form responses
   - Ensure columns: `timestamp,email,endpoint,secret`
   - Save as `submissions.csv`

3. **Start the API server** before running evaluation scripts

### Configuration Files to Edit

1. **task_templates.py**
   - Modify existing templates or add new ones
   - Adjust parameters, checks, and briefs

2. **evaluate.py**
   - Set `OPENAI_API_KEY` if using LLM evaluation (line 35)
   - Customize check logic in `_run_single_check()` method

3. **round1.py / round2.py**
   - Adjust `REQUEST_TIMEOUT` (default: 300 seconds)
   - Adjust `MAX_RETRIES` (default: 3)
   - Adjust `RETRY_DELAYS` (default: [60, 180, 600] seconds)

---

## File Structure

```
app-builder/
├── db.py                   # Database management
├── task_templates.py       # Task template definitions
├── round1.py              # Round 1 task generator
├── round2.py              # Round 2 task generator
├── evaluate.py            # Evaluation script
├── api_server.py          # FastAPI server with /api/evaluation
├── evaluation.db          # SQLite database (auto-created)
├── submissions.csv        # Student submissions (from Google Form)
├── results.csv            # Exported results (generated)
├── logs/                  # Log files
│   ├── round1.log
│   ├── round2.log
│   └── evaluate.log
└── EVALUATION_SETUP.md    # Complete setup guide
```

---

## Database Tables

### tasks
- Stores task requests sent to students
- Key fields: `email`, `task`, `round`, `nonce`, `brief`, `endpoint`, `statuscode`

### repos
- Stores repository submissions from students
- Key fields: `email`, `task`, `round`, `nonce`, `repo_url`, `commit_sha`, `pages_url`

### results
- Stores evaluation results
- Key fields: `email`, `task`, `round`, `check`, `score`, `reason`

---

## Common Database Queries

```powershell
# View all Round 1 tasks
sqlite3 evaluation.db "SELECT email, task, statuscode FROM tasks WHERE round = 1"

# View all submitted repos
sqlite3 evaluation.db "SELECT email, task, round, pages_url FROM repos"

# View evaluation results
sqlite3 evaluation.db "SELECT email, check, score FROM results WHERE round = 1"

# Get average score per student
sqlite3 evaluation.db "SELECT email, AVG(score) FROM results GROUP BY email"

# Count submissions by round
sqlite3 evaluation.db "SELECT round, COUNT(*) FROM repos GROUP BY round"
```

---

## API Endpoints

### POST /api/build
- Accepts student Round 1 build requests
- Validates secret, builds app, deploys to GitHub

### POST /api/revise
- Accepts student Round 2+ revision requests
- Updates existing repo with new features

### POST /api/evaluation
- Accepts student submissions with repo details
- Validates nonce, logs to repos table
- Returns HTTP 200 on success, 400 on error

### GET /health
- Health check endpoint

### GET /docs
- Interactive API documentation

---

## Task Templates

Available templates (in `task_templates.py`):

1. **image-viewer**
   - Round 1: Basic image gallery with lightbox
   - Round 2: SVG support, zoom/pan, thumbnails

2. **calculator**
   - Round 1: Basic arithmetic operations
   - Round 2: Scientific functions, memory, history

3. **todo-list**
   - Round 1: Add, complete, delete tasks
   - Round 2: Categories, filters, drag-and-drop

4. **weather-dashboard**
   - Round 1: Current weather display
   - Round 2: Hourly forecast, charts, favorites

5. **quiz-app**
   - Round 1: Multiple choice questions
   - Round 2: Timer, categories, leaderboard

---

## Evaluation Checks

### Automated Checks

1. **repo_creation_time**: Repo created after task time
2. **mit_license**: MIT LICENSE exists in root
3. **readme_quality**: README has proper sections
4. **code_quality**: Code structure and practices
5. **Playwright checks**: Based on task template
   - Element existence
   - Button clicks
   - Responsive design
   - Interactions

### Scoring

- Each check returns a score from 0.0 to 1.0
- Results stored in `results` table with `reason` field
- Export to CSV for final grading

---

## Troubleshooting

### Student API not responding
- Check if endpoint is correct in `submissions.csv`
- Increase `REQUEST_TIMEOUT` in round scripts
- Review `logs/round1.log` for errors

### No repos in database
- Ensure API server is running
- Check `/api/evaluation` endpoint is accessible
- Verify `evaluation_url` in tasks table

### Playwright errors
- Run `playwright install chromium`
- Check if page loads manually
- Review logs in `logs/evaluate.log`

### Database locked
- Close all connections: `taskkill /F /IM python.exe`
- Only one process should write to DB at a time

---

## Environment Variables

```powershell
# Required
$env:GITHUB_TOKEN="ghp_..."         # GitHub personal access token
$env:GITHUB_USERNAME="username"     # GitHub username

# Optional
$env:OPENAI_API_KEY="sk-..."       # For LLM-based evaluation
```

To make permanent (add to PowerShell profile):
```powershell
notepad $PROFILE
```

---

## Support Checklist

If something goes wrong:

1. [ ] Check logs in `logs/` directory
2. [ ] Query database for status:
   ```powershell
   sqlite3 evaluation.db "SELECT * FROM tasks WHERE statuscode != 200"
   ```
3. [ ] Verify API server is running:
   ```powershell
   curl http://localhost:8000/health
   ```
4. [ ] Test evaluation endpoint:
   ```powershell
   curl -X POST http://localhost:8000/api/evaluation -H "Content-Type: application/json" -d '{"email":"test@test.com","task":"test-12345","round":1,"nonce":"test-nonce","repo_url":"https://github.com/user/repo","commit_sha":"abc123","pages_url":"https://user.github.io/repo"}'
   ```
5. [ ] Enable debug logging:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

---

**For complete documentation, see EVALUATION_SETUP.md**

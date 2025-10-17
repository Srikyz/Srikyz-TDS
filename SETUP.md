# Setup and Quick Start Guide

## Quick Setup (5 minutes)

### Step 1: Install Dependencies

```powershell
# Navigate to project directory
cd app-builder

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Set Environment Variables

```powershell
# Set GitHub credentials
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
$env:GITHUB_USERNAME = "your-github-username"

# Optional: Set OpenAI API key for better LLM generation
$env:OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"
```

### Step 3: Test with Example Request

```powershell
# Run with example request
python main.py example_request.json
```

## Getting GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow`
4. Click "Generate token"
5. Copy the token (starts with `ghp_`)

## Verifying Installation

```powershell
# Check Python version (need 3.8+)
python --version

# Check Git is installed
git --version

# Optional: Check GitHub CLI
gh --version
```

## Creating Your First Request

Create a file called `my_request.json`:

```json
{
  "email": "your.email@example.com",
  "secret": "my-secure-secret-123",
  "task": "my-first-app",
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
}
```

Then run:

```powershell
python main.py my_request.json
```

## Expected Output

```
2025-10-16 10:30:00 - INFO - Processing request for task: my-first-app
2025-10-16 10:30:01 - INFO - Step 1: Validating request...
2025-10-16 10:30:01 - INFO - Step 2: Saving attachments...
2025-10-16 10:30:01 - INFO - Step 3: Generating app code using LLM...
2025-10-16 10:30:15 - INFO - Step 4: Deploying to GitHub Pages...
2025-10-16 10:30:25 - INFO - Step 5: Notifying evaluation API...

================================================================================
✓ SUCCESS!
Repository: https://github.com/your-username/my-first-app-r1
Live App: https://your-username.github.io/my-first-app-r1/
Commit: abc123def456...
Notification Sent: True
================================================================================
```

## Common Issues and Solutions

### Issue: "GITHUB_TOKEN not set"
**Solution**: Set the environment variable:
```powershell
$env:GITHUB_TOKEN = "your_token_here"
```

### Issue: "Failed to create repo"
**Solution**: 
- Check token permissions (need `repo` scope)
- Verify username is correct
- Ensure you haven't hit GitHub rate limits

### Issue: "LLM generation failed, using fallback"
**Solution**: 
- This is OK! System will use a template
- For better results, set `OPENAI_API_KEY`
- Or manually edit the generated code

### Issue: "GitHub Pages not loading"
**Solution**: 
- Wait 2-3 minutes for GitHub Pages to deploy
- Check repo settings → Pages
- Verify `index.html` exists in repo

## Testing the Revision Flow

1. First, create an app (round 1):
```powershell
python main.py my_request.json
```

2. Create a revision request `my_revision.json`:
```json
{
  "email": "your.email@example.com",
  "secret": "my-secure-secret-123",
  "task": "my-first-app",
  "round": 2,
  "nonce": "test-nonce-002",
  "brief": "Update the calculator to include square root and percentage operations",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Calculator has 6 operations including √ and %",
    "Design is clean and responsive"
  ],
  "evaluation_url": "https://httpbin.org/post",
  "attachments": []
}
```

3. Run the revision:
```powershell
python main.py --revision my_revision.json
```

## Directory Structure After Running

```
app-builder/
├── workdir/
│   └── my-first-app-r1/
│       ├── index.html
│       ├── style.css
│       ├── script.js
│       ├── README.md
│       └── LICENSE
├── logs/
│   └── app_builder_20251016_103000.log
├── main.py
└── ... (other files)
```

## Next Steps

1. ✅ Verify the app is live at the GitHub Pages URL
2. ✅ Check the repository was created on GitHub
3. ✅ Review the generated code in `workdir/`
4. ✅ Test the revision flow
5. ✅ Customize the LLM prompts in `app_generator.py`

## Production Deployment Tips

1. **Use a database** for storing secrets instead of in-memory storage
2. **Set up API rate limiting** to avoid hitting GitHub/LLM quotas
3. **Add monitoring** and alerting for failures
4. **Implement queue system** for handling multiple requests
5. **Add authentication** for the request endpoint
6. **Use environment-specific configs** (dev/staging/prod)

## Getting Help

- Check logs in `logs/` directory for detailed error messages
- Review the main README.md for architecture details
- Check GitHub API status: https://www.githubstatus.com/
- Verify OpenAI API status: https://status.openai.com/

---

Happy building! 🚀

# App Builder System

An automated system for building, deploying, and evaluating web applications based on AI-generated code.

## Overview

This system serves two audiences:

### For Students
1. **Build**: Receive app requirements, generate code using LLM, and deploy to GitHub Pages
2. **Revise**: Update apps based on feedback and re-deploy
3. **Submit**: Automatically notify evaluation endpoints

### For Instructors
1. **Generate Tasks**: Create parametrized tasks from templates
2. **Distribute**: Send tasks to student endpoints  
3. **Evaluate**: Automatically test submissions with Playwright and LLM
4. **Iterate**: Send Round 2+ tasks based on results

## Features

### Student-Facing Features
- 🤖 **LLM-Assisted Code Generation**: Uses GPT-4 or other LLMs to generate complete web applications
- 🚀 **Automatic GitHub Deployment**: Creates repositories and deploys to GitHub Pages
- ✅ **Request Validation**: Validates all incoming requests and secrets
- 📊 **Evaluation Integration**: Notifies evaluation APIs with deployment details
- 🔄 **Revision Support**: Handles app updates and redeployment (Round 2+)
- 📝 **Comprehensive Logging**: Tracks all operations for debugging

### Instructor-Facing Features
- 📋 **Task Templates**: 5 parametrizable templates (image viewer, calculator, todo, weather, quiz)
- 🔄 **Multi-Round Support**: Automatic Round 1 → Evaluation → Round 2 workflow
- 🤹 **Parametrization**: Tasks vary by student and time (prevents copying)
- 🔍 **Automated Evaluation**: LICENSE checks, README/code quality, Playwright tests
- 📊 **Database Tracking**: SQLite database with tasks, repos, results tables
- 📈 **Results Export**: CSV export for grading

## Architecture

```
┌─────────────────┐
│  Request JSON   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validator     │  ◄── Validates request & secret
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  App Generator  │  ◄── Uses LLM to generate code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Deployer │  ◄── Creates repo & deploys
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Evaluator    │  ◄── Notifies evaluation API
└─────────────────┘
```

## Setup

### Prerequisites

- Python 3.8+
- Git installed and configured
- GitHub CLI (`gh`) installed (optional but recommended)
- GitHub account with Personal Access Token

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd app-builder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "your_github_token"
$env:GITHUB_USERNAME = "your_github_username"
$env:OPENAI_API_KEY = "your_openai_api_key"  # Optional, for LLM

# Linux/Mac
export GITHUB_TOKEN="your_github_token"
export GITHUB_USERNAME="your_github_username"
export OPENAI_API_KEY="your_openai_api_key"  # Optional
```

4. Import secrets from Google Form:
```bash
# Export responses from Google Forms as CSV
# Then import:
python manage_secrets.py import form_responses.csv

# Or add secrets manually:
python manage_secrets.py add student@example.com their-secret-key
```

5. Update `config.json` with your settings (optional):
```json
{
  "llm_model": "gpt-4",
  "github_username": "your-username",
  "log_level": "INFO"
}
```

6. Start the API server:
```bash
python api_server.py
```

The API will be available at `http://localhost:8000` with automatic documentation at `/docs`.

## Usage

### Method 1: API Endpoint (Recommended)

Start the API server:

```bash
python api_server.py
```

Then send POST requests:

```bash
# Build a new app (Round 1)
curl http://localhost:8000/api/build \
  -H "Content-Type: application/json" \
  -d @request.json

# Revise an existing app (Round 2+)
curl http://localhost:8000/api/revise \
  -H "Content-Type: application/json" \
  -d @revision_request.json
```

**API Features:**
- ✅ HTTP POST endpoint at `/api/build` and `/api/revise`
- ✅ Returns JSON with 200 OK on success
- ✅ Secret verification against Google Form submissions (same secret for all rounds)
- ✅ Round 2+ modifies existing repo and updates README
- ✅ Automatic GitHub Pages redeployment
- ✅ Notification sent within 10 minutes with retry logic
- ✅ Automatic interactive documentation at `/docs`

See [API_EXAMPLES.md](API_EXAMPLES.md) and [REVISION_GUIDE.md](REVISION_GUIDE.md) for detailed examples.

### Method 2: Command Line

Process a request to build and deploy a new app:

```bash
python main.py request.json
```

Process a revision request to update an existing app:

```bash
python main.py --revision revision_request.json
```

## Request Format

### Build Request

```json
{
  "email": "student@example.com",
  "secret": "your-secret-key",
  "task": "captcha-solver-abc123",
  "round": 1,
  "nonce": "unique-nonce-value",
  "brief": "Create a captcha solver that handles ?url=... parameter",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Page displays captcha URL passed at ?url=...",
    "Page displays solved captcha text within 15 seconds"
  ],
  "evaluation_url": "https://example.com/api/evaluate",
  "attachments": [
    {
      "name": "sample.png",
      "url": "data:image/png;base64,iVBORw..."
    }
  ]
}
```

### Revision Request

Same format as build request, but with:
- Updated `brief` and `checks`
- Same `secret` for verification
- Incremented `round` number

## Instructor Evaluation System

For instructors managing student assignments, this system includes automated evaluation tools:

### Quick Start for Instructors

```bash
# 1. Export Google Form submissions to submissions.csv
# 2. Start the API server
python api_server.py

# 3. Send Round 1 tasks to students
python round1.py submissions.csv

# 4. Evaluate submissions (after students submit)
python evaluate.py --round 1

# 5. Send Round 2 tasks
python round2.py

# 6. Evaluate Round 2
python evaluate.py --round 2

# 7. Export results
python -c "from db import get_db; get_db().export_results_csv('results.csv')"
```

### What's Included

- **Task Templates**: 5 parametrizable templates (image viewer, calculator, todo, weather, quiz)
- **Database System**: SQLite with tasks, repos, results tables
- **Automated Evaluation**: LICENSE checks, README/code quality, Playwright tests
- **Multi-Round Support**: Round 1 → Evaluation → Round 2 workflow
- **Parametrization**: Tasks vary by student/time to prevent copying

### Documentation for Instructors

- **[EVALUATION_SUMMARY.md](EVALUATION_SUMMARY.md)** - System overview ⭐
- **[MANUAL_CHANGES.md](MANUAL_CHANGES.md)** - Required setup steps ⚠️
- **[EVALUATION_SETUP.md](EVALUATION_SETUP.md)** - Complete guide with troubleshooting
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick commands

### Database Schema

Three tables for tracking:
- **tasks**: Task requests sent to students
- **repos**: Repository submissions received
- **results**: Evaluation results per check

See [EVALUATION_SETUP.md](EVALUATION_SETUP.md) for complete details.

---

## Project Structure

```
app-builder/
├── Student-Facing System
│   ├── api_server.py           # FastAPI server (API endpoint)
│   ├── main.py                 # Main orchestrator (CLI)
│   ├── request_validator.py    # Request validation
│   ├── app_generator.py        # LLM-based code generation
│   ├── github_deployer.py      # GitHub deployment
│   ├── evaluator.py           # Evaluation API integration
│   ├── secret_manager.py      # Secret verification
│   ├── manage_secrets.py      # Secret management CLI
│   └── utils.py               # Utility functions
│
├── Instructor Evaluation System
│   ├── db.py                  # Database management
│   ├── task_templates.py      # Task template definitions
│   ├── round1.py              # Round 1 task generator
│   ├── round2.py              # Round 2 task generator
│   ├── evaluate.py            # Evaluation script (Playwright)
│   ├── evaluation.db          # SQLite database (auto-created)
│   └── submissions.csv        # Input from Google Form
│
├── Configuration
│   ├── config.json            # System configuration
│   ├── secrets.json           # Hashed secrets (gitignored)
│   └── requirements.txt       # Python dependencies
│
├── Documentation
│   ├── README.md              # This file
│   ├── SETUP.md              # Quick start guide
│   ├── EVALUATION_SUMMARY.md  # Instructor system overview ⭐
│   ├── MANUAL_CHANGES.md      # Required manual steps ⚠️
│   ├── EVALUATION_SETUP.md    # Complete evaluation guide
│   ├── QUICK_REFERENCE.md     # Quick commands
│   ├── API_EXAMPLES.md        # API usage examples
│   └── REVISION_GUIDE.md      # Round 2 workflow
│
├── Working Directories
│   ├── workdir/              # Working directory for repos
│   └── logs/                 # Log files
└── Example Files
    ├── example_request.json   # Example request
    └── submissions_sample.csv # Sample submissions file
```

## Components

### Request Validator (`request_validator.py`)
- Validates required fields
- Checks email format
- Verifies secrets for revisions
- Ensures data integrity

### App Generator (`app_generator.py`)
- Constructs prompts for LLM
- Generates HTML, CSS, and JavaScript
- Creates README and LICENSE files
- Handles app revisions

### GitHub Deployer (`github_deployer.py`)
- Creates GitHub repositories
- Initializes Git repositories
- Commits and pushes code
- Enables GitHub Pages
- Manages updates

### Evaluator (`evaluator.py`)
- Sends notifications to evaluation APIs within 10 minutes
- Includes repo URL, commit SHA, and Pages URL
- Implements exponential backoff retry: 1, 2, 4, 8, 16, 32, 64 seconds
- Ensures HTTP 200 response or retries until max attempts
- Handles timeouts, connection errors, and HTTP errors gracefully

### Utilities (`utils.py`)
- Logging setup
- Configuration management
- Attachment handling
- Helper functions

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes |
| `GITHUB_USERNAME` | GitHub username | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM | Optional* |

*If not provided, a fallback template will be used.

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token (classic) with these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Actions workflows)
   - `admin:repo_hook` (Full control of repository hooks)
3. Copy the token and set it as `GITHUB_TOKEN`

## Logging

Logs are stored in the `logs/` directory with timestamps:
- Format: `app_builder_YYYYMMDD_HHMMSS.log`
- Includes all operations, errors, and debug information
- Also output to console

## Error Handling

The system includes comprehensive error handling:
- Request validation errors
- LLM generation failures (fallback to template)
- GitHub API failures
- Network errors
- File system errors

All errors are logged and returned in the result dictionary.

## Security Considerations

1. **Secrets**: Store secrets securely (use a database in production)
2. **API Keys**: Never commit API keys to version control
3. **Token Permissions**: Use minimal required GitHub token permissions
4. **Input Validation**: All inputs are validated before processing
5. **Rate Limiting**: Be aware of GitHub and LLM API rate limits

## Limitations

- Static websites only (no server-side code)
- GitHub Pages deployment only
- Single-page applications work best
- LLM-generated code quality depends on prompt and model

## Troubleshooting

### "Repository not found" error
- Ensure `GITHUB_USERNAME` matches your GitHub username
- Check that `GITHUB_TOKEN` has correct permissions

### "LLM generation failed"
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and billing
- System will use fallback template if LLM fails

### "GitHub Pages not enabled"
- Pages may take a few minutes to activate
- Check repository settings manually if needed

### "Evaluation notification failed"
- Check network connectivity
- Verify `evaluation_url` is correct
- Review logs for detailed error messages

## Future Enhancements

- [ ] Support for multiple LLM providers (Claude, Gemini, etc.)
- [ ] Database integration for secret storage
- [ ] Web interface for submitting requests
- [ ] More sophisticated app templates
- [ ] Support for multi-file projects
- [ ] Automated testing before deployment
- [ ] Rollback functionality

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:
- Check the logs in `logs/` directory
- Review the troubleshooting section
- Open an issue on GitHub

---

**Note**: This system is designed for educational purposes. Ensure compliance with GitHub's Terms of Service and API usage limits.

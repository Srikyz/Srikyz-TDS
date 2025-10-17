# Round 2 Revision Request - Complete Example

This document demonstrates the complete workflow for submitting a Round 2 revision request.

## Scenario

**Round 1:** Built a calculator with basic operations (+, -, *, /)  
**Round 2:** Add square root and percentage operations, improve UI

## Step-by-Step Process

### 1. Initial Build (Round 1)

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "my-secret-key-12345",
  "task": "calculator-app-2024",
  "round": 1,
  "nonce": "nonce-round1-001",
  "brief": "Create a simple calculator web app with +, -, *, / operations",
  "checks": [
    "Repo has MIT license",
    "README.md is professional",
    "Calculator has 4 basic operations",
    "Design is clean and responsive"
  ],
  "evaluation_url": "https://example.com/api/evaluate",
  "attachments": []
}
```

**Command:**
```powershell
curl http://localhost:8000/api/build `
  -H "Content-Type: application/json" `
  -d (Get-Content round1_request.json -Raw)
```

**Response:**
```json
{
  "success": true,
  "message": "Application built and deployed successfully",
  "data": {
    "repo_url": "https://github.com/user/calculator-app-2024-r1",
    "pages_url": "https://user.github.io/calculator-app-2024-r1/",
    "commit_sha": "a1b2c3d4e5f6",
    "notification_sent": true,
    "notification_attempts": 1
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

**What Happened:**
1. ✅ Secret verified against Google Form submission
2. ✅ LLM generated calculator with +, -, *, /
3. ✅ Created repo: `calculator-app-2024-r1`
4. ✅ Deployed to GitHub Pages
5. ✅ Sent notification to evaluation API with round: 1

---

### 2. Revision Request (Round 2)

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "my-secret-key-12345",
  "task": "calculator-app-2024",
  "round": 2,
  "nonce": "nonce-round2-002",
  "brief": "Update calculator to include square root (√) and percentage (%) operations. Improve the UI with gradient background and larger buttons. Add keyboard support.",
  "checks": [
    "Repo has MIT license",
    "README.md is professional and updated",
    "Calculator has 6 operations: +, -, *, /, √, %",
    "Design is clean and responsive with improved UI",
    "Keyboard support works (0-9, +, -, *, /, Enter, Escape)"
  ],
  "evaluation_url": "https://example.com/api/evaluate",
  "attachments": []
}
```

**Command:**
```powershell
curl http://localhost:8000/api/revise `
  -H "Content-Type: application/json" `
  -d (Get-Content round2_request.json -Raw)
```

**Response:**
```json
{
  "success": true,
  "message": "Application revised and redeployed successfully",
  "data": {
    "repo_url": "https://github.com/user/calculator-app-2024-r1",
    "pages_url": "https://user.github.io/calculator-app-2024-r1/",
    "commit_sha": "g7h8i9j0k1l2",
    "notification_sent": true,
    "notification_attempts": 1
  },
  "timestamp": "2025-10-16T11:45:00Z"
}
```

**What Happened:**
1. ✅ Secret verified (must match Round 1)
2. ✅ Retrieved existing code from `calculator-app-2024-r1`
3. ✅ LLM updated code based on new brief:
   - Added √ and % operations
   - Enhanced UI with gradient and larger buttons
   - Added keyboard event listeners
4. ✅ Updated README.md with new features
5. ✅ Committed with message: "Update for round 2"
6. ✅ Pushed to same repo (GitHub Pages auto-redeploys)
7. ✅ Sent notification with round: 2

---

## Key Differences Between Rounds

### Round 1 (Build)
- Creates **new repository** with name `{task}-r{round}`
- Initializes git
- Enables GitHub Pages
- First deployment

### Round 2+ (Revise)
- Uses **existing repository**
- Updates existing files
- Commits with "Update for round N"
- Same Pages URL (auto-redeploys)
- Can have multiple revisions

---

## Secret Verification

Both rounds use the **same secret**:
- Must match what was submitted in Google Form
- Stored as SHA-256 hash
- Verified on every request

```powershell
# Register secret (done once from Google Form)
python manage_secrets.py add student@example.com my-secret-key-12345

# Both rounds use the same secret
# Round 1: secret = "my-secret-key-12345" ✓
# Round 2: secret = "my-secret-key-12345" ✓
# Round 2: secret = "wrong-secret" ✗ (401 Unauthorized)
```

---

## Repository Updates

### Before Round 2
```
calculator-app-2024-r1/
├── index.html       (basic calculator)
├── style.css        (simple styling)
├── script.js        (4 operations: +, -, *, /)
├── README.md        (describes 4 operations)
└── LICENSE          (MIT)
```

### After Round 2
```
calculator-app-2024-r1/
├── index.html       (updated with √ and % buttons)
├── style.css        (gradient, larger buttons)
├── script.js        (6 operations, keyboard support)
├── README.md        (updated with new features)
└── LICENSE          (unchanged)
```

**Git History:**
```
g7h8i9j0k1l2 - Update for round 2
a1b2c3d4e5f6 - Initial deployment
```

---

## Notification to Evaluation API

### Round 1 Notification
```json
{
  "email": "student@example.com",
  "task": "calculator-app-2024",
  "round": 1,
  "nonce": "nonce-round1-001",
  "repo_url": "https://github.com/user/calculator-app-2024-r1",
  "commit_sha": "a1b2c3d4e5f6",
  "pages_url": "https://user.github.io/calculator-app-2024-r1/"
}
```

### Round 2 Notification
```json
{
  "email": "student@example.com",
  "task": "calculator-app-2024",
  "round": 2,
  "nonce": "nonce-round2-002",
  "repo_url": "https://github.com/user/calculator-app-2024-r1",
  "commit_sha": "g7h8i9j0k1l2",
  "pages_url": "https://user.github.io/calculator-app-2024-r1/"
}
```

**Note:** Same `repo_url` and `pages_url`, different `commit_sha`

---

## Complete PowerShell Example

```powershell
# Round 1: Initial Build
$round1 = @{
    email = "student@example.com"
    secret = "my-secret-key-12345"
    task = "svg-image-viewer"
    round = 1
    nonce = "nonce-r1"
    brief = "Create an image viewer that displays images from ?url= parameter"
    checks = @(
        "Repo has MIT license",
        "README.md is professional",
        "Displays image from URL parameter",
        "Shows error for invalid URLs"
    )
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/build" `
    -Method Post -ContentType "application/json" -Body $round1

# Wait for evaluation...
Start-Sleep -Seconds 5

# Round 2: Add SVG Support
$round2 = @{
    email = "student@example.com"
    secret = "my-secret-key-12345"  # Same secret!
    task = "svg-image-viewer"
    round = 2  # Incremented
    nonce = "nonce-r2"
    brief = "Update to handle SVG images specifically. Add zoom controls and pan functionality for SVG files."
    checks = @(
        "Repo has MIT license",
        "README.md is professional and updated",
        "Displays image from URL parameter",
        "Handles SVG images correctly",
        "Has zoom in/out controls",
        "Has pan functionality for SVG"
    )
    evaluation_url = "https://httpbin.org/post"
    attachments = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/revise" `
    -Method Post -ContentType "application/json" -Body $round2
```

---

## Error Scenarios

### Wrong Secret (Round 2)
```json
{
  "email": "student@example.com",
  "secret": "wrong-secret",
  "task": "calculator-app-2024",
  "round": 2,
  ...
}
```
**Response:** HTTP 401
```json
{
  "detail": "Secret verification failed"
}
```

### Repository Not Found
```json
{
  "email": "student@example.com",
  "secret": "my-secret-key-12345",
  "task": "non-existent-task",
  "round": 2,
  ...
}
```
**Response:** HTTP 404
```json
{
  "detail": "Repository not found. Was the initial build completed?"
}
```

### Round 2 Before Round 1
If you try Round 2 without completing Round 1 first, you'll get a 404 error.

---

## Testing Round 2 Workflow

```powershell
# 1. Register test secret
python manage_secrets.py add test@example.com test-secret-123

# 2. Start server
python api_server.py

# 3. Send Round 1 request
curl http://localhost:8000/api/build -Method Post `
  -ContentType "application/json" `
  -Body (Get-Content test_round1.json -Raw)

# 4. Verify deployment
# Check: https://github.com/your_username/test-task-r1
# Check: https://your_username.github.io/test-task-r1/

# 5. Send Round 2 request (same secret!)
curl http://localhost:8000/api/revise -Method Post `
  -ContentType "application/json" `
  -Body (Get-Content test_round2.json -Raw)

# 6. Verify update
# Same URLs, new commit, updated code
```

---

## Best Practices

### For Students
1. **Keep your secret safe** - Use the same one for all rounds
2. **Wait for Round 1 to complete** before sending Round 2
3. **Check GitHub Pages** after each round
4. **Verify the new commit** was pushed

### For Instructors
1. **Provide clear revision briefs** with specific changes
2. **Include all checks** from Round 1 plus new ones
3. **Allow time between rounds** for evaluation
4. **Monitor notification success** in logs

---

## Troubleshooting

### "Repository not found"
- Ensure Round 1 completed successfully
- Check task ID is exactly the same
- Verify repo exists on GitHub

### "Secret verification failed"
- Must use the **same secret** as Round 1
- Check for typos
- Verify secret was registered

### "Pages not updating"
- Wait 2-3 minutes for GitHub Pages to rebuild
- Hard refresh browser (Ctrl+F5)
- Check commit SHA changed

### "Notification failed"
- Deployment still succeeds
- Check evaluation_url is correct
- Review logs for retry attempts

---

## Summary

✅ **Round 2 accepts revision requests** at `/api/revise`  
✅ **Secret is verified** (must match Round 1)  
✅ **Returns HTTP 200 JSON** on success  
✅ **Modifies existing repo** based on new brief  
✅ **Updates README.md** with new features  
✅ **Pushes changes** to same repo  
✅ **GitHub Pages auto-redeploys**  
✅ **Sends notification** with round: 2  
✅ **Retry logic** ensures HTTP 200 response  
✅ **Completes within 10 minutes**  

The revision system is **production-ready**! 🎉

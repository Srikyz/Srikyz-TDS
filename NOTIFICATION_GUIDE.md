# Evaluation Notification - Retry Logic

## Overview

The system sends notifications to the evaluation API with robust retry logic to ensure delivery.

## Retry Flow

```
Request Received
      │
      ▼
Build & Deploy
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ Send Notification to evaluation_url                     │
│ POST with JSON payload                                  │
│ Header: Content-Type: application/json                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
            HTTP Response?
                  │
        ┌─────────┴─────────┐
        │                   │
    HTTP 200          Non-200/Error
        │                   │
        ▼                   ▼
    ✓ SUCCESS         Retry Needed
        │                   │
        │                   ▼
        │         ┌──────────────────┐
        │         │ Wait with delay: │
        │         │ Attempt 1: 1s    │
        │         │ Attempt 2: 2s    │
        │         │ Attempt 3: 4s    │
        │         │ Attempt 4: 8s    │
        │         │ Attempt 5: 16s   │
        │         │ Attempt 6: 32s   │
        │         │ Attempt 7: 64s   │
        │         └────────┬─────────┘
        │                  │
        │                  ▼
        │         Retry POST Request
        │                  │
        │                  ▼
        │         ┌────────────────┐
        │         │ Max attempts?  │
        │         └────┬──────┬────┘
        │              │      │
        │             No     Yes
        │              │      │
        └──────────────┘      ▼
                          ✗ FAIL
                    (deployment still
                     succeeded)
```

## Timing Analysis

### Exponential Backoff Delays

| Attempt | Delay  | Cumulative Time |
|---------|--------|-----------------|
| 1       | 0s     | 0s              |
| 2       | 1s     | 1s              |
| 3       | 2s     | 3s              |
| 4       | 4s     | 7s              |
| 5       | 8s     | 15s             |
| 6       | 16s    | 31s             |
| 7       | 32s    | 63s             |
| 8       | 64s    | 127s            |

**Total maximum retry time: ~127 seconds (2.1 minutes)**

This is well within the 10-minute requirement (600 seconds).

## Error Handling

### Retryable Errors
- HTTP 4xx (except 401/403)
- HTTP 5xx
- Connection errors
- Timeout errors
- Network errors

### Non-Retryable (after max attempts)
- After 8 attempts (initial + 7 retries)
- Deployment still succeeds, notification marked as failed

## JSON Payload Format

```json
{
  "email": "student@example.com",
  "task": "captcha-solver-abc123",
  "round": 1,
  "nonce": "ab12-cd34-ef56",
  "repo_url": "https://github.com/user/captcha-solver-abc123-r1",
  "commit_sha": "a1b2c3d4e5f6789...",
  "pages_url": "https://user.github.io/captcha-solver-abc123-r1/"
}
```

**Fields from request:** `email`, `task`, `round`, `nonce`  
**Fields from deployment:** `repo_url`, `commit_sha`, `pages_url`

## HTTP Requirements

✅ **Method:** POST  
✅ **Header:** `Content-Type: application/json`  
✅ **Success:** HTTP 200  
✅ **Timeout:** 30 seconds per request  
✅ **Retry:** Exponential backoff (1, 2, 4, 8, 16, 32, 64 seconds)  

## Code Example

```python
from evaluator import EvaluationNotifier

notifier = EvaluationNotifier()

result = notifier.notify(
    evaluation_url="https://example.com/api/evaluate",
    repo_url="https://github.com/user/repo",
    commit_sha="abc123",
    pages_url="https://user.github.io/repo/",
    nonce="test-nonce",
    email="student@example.com",
    task="test-task",
    round_num=1
)

# Result format:
# {
#     'success': True/False,
#     'status_code': 200,
#     'response': '...',
#     'attempts': 1
# }
```

## Testing

```powershell
# Run notification tests
python test_evaluator.py

# Test with httpbin.org
curl https://httpbin.org/post -Method Post `
  -ContentType "application/json" `
  -Body '{"test":"data"}'
```

## Monitoring

Check logs for notification attempts:
```
[task-r1] Sending notification to: https://example.com/api/evaluate
[task-r1] Attempt 1/8
[task-r1] ✓ Notification sent successfully: HTTP 200
[task-r1] Notification completed in 0.52 seconds
```

Or with retries:
```
[task-r1] Sending notification to: https://example.com/api/evaluate
[task-r1] Attempt 1/8
[task-r1] Received HTTP 500, will retry
[task-r1] Retrying in 1 seconds...
[task-r1] Attempt 2/8
[task-r1] Received HTTP 500, will retry
[task-r1] Retrying in 2 seconds...
[task-r1] Attempt 3/8
[task-r1] ✓ Notification sent successfully: HTTP 200
[task-r1] Notification completed in 3.85 seconds
```

## Best Practices

1. **Evaluation API should respond quickly** (< 5 seconds ideal)
2. **Return HTTP 200 only on successful processing**
3. **Log all notification attempts** for debugging
4. **Monitor notification success rate** in production
5. **Set up alerts** if notification failures exceed threshold

## Troubleshooting

### All retries failed
- Check evaluation URL is correct
- Verify evaluation API is accessible
- Check firewall/network rules
- Review API logs for errors

### Notifications slow
- Check network latency
- Verify evaluation API response time
- Consider increasing timeout if needed

### Wrong payload format
- Use `test_evaluator.py` to verify format
- Check evaluation API expects exact JSON structure
- Review logs for payload sent

---

**Note:** Even if notification fails after all retries, the deployment itself succeeds. The app is still built and deployed to GitHub Pages.

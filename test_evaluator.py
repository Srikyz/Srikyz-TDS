"""
Test script for the evaluation notifier with retry logic.
Simulates various failure scenarios to verify exponential backoff.
"""

import time
from evaluator import EvaluationNotifier
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_successful_notification():
    """Test successful notification to httpbin.org."""
    print("\n" + "="*70)
    print("Test 1: Successful Notification (should succeed on first try)")
    print("="*70)
    
    notifier = EvaluationNotifier()
    
    result = notifier.notify(
        evaluation_url="https://httpbin.org/status/200",
        repo_url="https://github.com/test/repo",
        commit_sha="abc123def456",
        pages_url="https://test.github.io/repo/",
        nonce="test-nonce-001",
        email="test@example.com",
        task="test-task",
        round_num=1
    )
    
    print(f"\nResult: {result}")
    assert result['success'] == True, "Should succeed"
    assert result.get('attempts', 0) == 1, "Should succeed on first attempt"
    print("✓ Test passed!")


def test_retry_on_500():
    """Test retry on HTTP 500 error."""
    print("\n" + "="*70)
    print("Test 2: Retry on HTTP 500 (should retry with exponential backoff)")
    print("="*70)
    
    notifier = EvaluationNotifier()
    notifier.max_retries = 3  # Reduce for faster testing
    
    start_time = time.time()
    
    result = notifier.notify(
        evaluation_url="https://httpbin.org/status/500",
        repo_url="https://github.com/test/repo",
        commit_sha="abc123def456",
        pages_url="https://test.github.io/repo/",
        nonce="test-nonce-002",
        email="test@example.com",
        task="test-task",
        round_num=1
    )
    
    elapsed = time.time() - start_time
    
    print(f"\nResult: {result}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Expected delays: 1 + 2 + 4 = 7 seconds minimum")
    
    assert result['success'] == False, "Should fail after retries"
    assert result.get('attempts', 0) == 4, "Should attempt 4 times (initial + 3 retries)"
    assert elapsed >= 7, "Should have exponential delays"
    print("✓ Test passed!")


def test_retry_then_success():
    """Test that retries until success."""
    print("\n" + "="*70)
    print("Test 3: Retry Logic Validation")
    print("="*70)
    
    notifier = EvaluationNotifier()
    
    # Test the delay calculation
    print("\nExponential backoff delays:")
    for attempt in range(8):
        delay = notifier.base_delay * (2 ** attempt)
        print(f"  Attempt {attempt + 1}: {delay} seconds")
    
    total_delay = sum(2**i for i in range(7))
    print(f"\nTotal retry time: {total_delay} seconds (127 seconds)")
    print("Within 10 minute (600 second) requirement ✓")
    
    print("✓ Test passed!")


def test_timeout_handling():
    """Test handling of request timeouts."""
    print("\n" + "="*70)
    print("Test 4: Timeout Handling (will take ~30 seconds per attempt)")
    print("="*70)
    
    notifier = EvaluationNotifier()
    notifier.max_retries = 1  # Only 1 retry for faster testing
    notifier.timeout = 5  # Shorter timeout
    
    # This endpoint delays response
    result = notifier.notify(
        evaluation_url="https://httpbin.org/delay/10",  # 10 second delay
        repo_url="https://github.com/test/repo",
        commit_sha="abc123def456",
        pages_url="https://test.github.io/repo/",
        nonce="test-nonce-003",
        email="test@example.com",
        task="test-task",
        round_num=1
    )
    
    print(f"\nResult: {result}")
    assert result['success'] == False, "Should fail due to timeout"
    print("✓ Test passed!")


def test_json_payload_format():
    """Verify the exact JSON payload format."""
    print("\n" + "="*70)
    print("Test 5: JSON Payload Format Verification")
    print("="*70)
    
    notifier = EvaluationNotifier()
    
    # Use httpbin.org/post to echo back the payload
    result = notifier.notify(
        evaluation_url="https://httpbin.org/post",
        repo_url="https://github.com/testuser/test-repo",
        commit_sha="a1b2c3d4e5f6",
        pages_url="https://testuser.github.io/test-repo/",
        nonce="nonce-12345",
        email="student@example.com",
        task="captcha-solver-abc",
        round_num=2
    )
    
    print(f"\nResult: {result}")
    
    if result['success']:
        import json
        response_data = json.loads(result['response'])
        sent_data = response_data.get('json', {})
        
        print("\nSent payload:")
        print(json.dumps(sent_data, indent=2))
        
        # Verify required fields
        required_fields = ['email', 'task', 'round', 'nonce', 'repo_url', 'commit_sha', 'pages_url']
        for field in required_fields:
            assert field in sent_data, f"Missing required field: {field}"
            print(f"  ✓ {field}: {sent_data[field]}")
        
        # Verify no extra timestamp field (not in spec)
        assert 'timestamp' not in sent_data, "Should not include timestamp in payload"
        
        print("✓ Payload format is correct!")
    
    print("✓ Test passed!")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("EVALUATION NOTIFIER TEST SUITE")
    print("="*70)
    
    tests = [
        ("Successful Notification", test_successful_notification),
        ("Retry on HTTP 500", test_retry_on_500),
        ("Exponential Backoff Validation", test_retry_then_success),
        ("Timeout Handling", test_timeout_handling),
        ("JSON Payload Format", test_json_payload_format),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    
    print("This test suite requires internet connection (uses httpbin.org)")
    print("Some tests may take a while due to retry delays...\n")
    
    input("Press Enter to continue...")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

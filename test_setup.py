"""
Test script for the app builder system.
Run this to verify your setup is working correctly.
"""

import os
import sys
from pathlib import Path
import json

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import requests
        print("  ✓ requests")
    except ImportError:
        print("  ✗ requests - run: pip install requests")
        return False
    
    try:
        import openai
        print("  ✓ openai (optional)")
    except ImportError:
        print("  ⚠ openai not installed (optional) - for better LLM: pip install openai")
    
    return True

def test_environment():
    """Test that environment variables are set."""
    print("\nTesting environment variables...")
    
    github_token = os.getenv('GITHUB_TOKEN')
    github_username = os.getenv('GITHUB_USERNAME')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    all_good = True
    
    if github_token:
        print(f"  ✓ GITHUB_TOKEN is set ({github_token[:10]}...)")
    else:
        print("  ✗ GITHUB_TOKEN is not set")
        all_good = False
    
    if github_username:
        print(f"  ✓ GITHUB_USERNAME is set ({github_username})")
    else:
        print("  ✗ GITHUB_USERNAME is not set")
        all_good = False
    
    if openai_key:
        print(f"  ✓ OPENAI_API_KEY is set ({openai_key[:10]}...)")
    else:
        print("  ⚠ OPENAI_API_KEY is not set (optional)")
    
    return all_good

def test_git():
    """Test that git is installed."""
    print("\nTesting git installation...")
    import subprocess
    
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Git is installed: {result.stdout.strip()}")
            return True
        else:
            print("  ✗ Git command failed")
            return False
    except FileNotFoundError:
        print("  ✗ Git is not installed")
        return False

def test_github_cli():
    """Test if GitHub CLI is installed (optional)."""
    print("\nTesting GitHub CLI (optional)...")
    import subprocess
    
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ GitHub CLI is installed: {result.stdout.split()[0]}")
            return True
        else:
            print("  ⚠ GitHub CLI command failed (optional)")
            return False
    except FileNotFoundError:
        print("  ⚠ GitHub CLI is not installed (optional, but recommended)")
        return False

def test_file_structure():
    """Test that required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'request_validator.py',
        'app_generator.py',
        'github_deployer.py',
        'evaluator.py',
        'utils.py',
        'config.json',
        'requirements.txt'
    ]
    
    all_exist = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} is missing")
            all_exist = False
    
    return all_exist

def test_config():
    """Test that config.json is valid."""
    print("\nTesting configuration...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("  ✓ config.json is valid JSON")
        
        required_keys = ['llm_model', 'log_level']
        for key in required_keys:
            if key in config:
                print(f"  ✓ config has '{key}': {config[key]}")
            else:
                print(f"  ⚠ config missing '{key}'")
        
        return True
    except Exception as e:
        print(f"  ✗ config.json error: {e}")
        return False

def test_request_validation():
    """Test request validation with example."""
    print("\nTesting request validation...")
    
    try:
        from request_validator import RequestValidator
        
        validator = RequestValidator()
        
        # Test valid request
        valid_request = {
            'email': 'test@example.com',
            'secret': 'test-secret-12345',
            'task': 'test-task',
            'round': 1,
            'nonce': 'test-nonce',
            'brief': 'This is a test brief that is long enough',
            'checks': ['Check 1', 'Check 2'],
            'evaluation_url': 'https://example.com/eval'
        }
        
        is_valid, error = validator.validate_request(valid_request)
        if is_valid:
            print("  ✓ Valid request accepted")
        else:
            print(f"  ✗ Valid request rejected: {error}")
            return False
        
        # Test invalid request (missing field)
        invalid_request = {
            'email': 'test@example.com',
            'secret': 'test'
        }
        
        is_valid, error = validator.validate_request(invalid_request)
        if not is_valid:
            print(f"  ✓ Invalid request rejected: {error}")
        else:
            print("  ✗ Invalid request accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Validation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("="*80)
    print("APP BUILDER SYSTEM - SETUP TEST")
    print("="*80)
    
    results = {
        'Imports': test_imports(),
        'Environment': test_environment(),
        'Git': test_git(),
        'GitHub CLI': test_github_cli(),
        'File Structure': test_file_structure(),
        'Configuration': test_config(),
        'Request Validation': test_request_validation()
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print("="*80)
    
    # Check critical tests
    critical_tests = ['Imports', 'Environment', 'Git', 'File Structure']
    all_critical_passed = all(results[test] for test in critical_tests)
    
    if all_critical_passed:
        print("\n✓ All critical tests passed! You're ready to run the app builder.")
        print("\nNext steps:")
        print("  1. Review and update config.json if needed")
        print("  2. Run: python main.py example_request.json")
        print("  3. Check the generated app in workdir/")
        return 0
    else:
        print("\n✗ Some critical tests failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - SETUP.md for detailed setup instructions")
        print("  - README.md for troubleshooting")
        return 1

if __name__ == '__main__':
    sys.exit(main())

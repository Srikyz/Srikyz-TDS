"""
Setup verification script for the evaluation system.

Run this script to check if everything is configured correctly.

Usage:
    python verify_setup.py

Author: Evaluation System
Date: 2025-10-16
"""

import sys
import os
from pathlib import Path
import subprocess

def print_header(text):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_pass(msg):
    """Print a success message."""
    print(f"✅ {msg}")

def check_fail(msg):
    """Print a failure message."""
    print(f"❌ {msg}")

def check_warning(msg):
    """Print a warning message."""
    print(f"⚠️  {msg}")

def check_environment_variables():
    """Check if required environment variables are set."""
    print_header("Environment Variables")
    
    all_ok = True
    
    # Required variables
    required = {
        'GITHUB_TOKEN': 'GitHub Personal Access Token',
        'GITHUB_USERNAME': 'GitHub Username'
    }
    
    for var, description in required.items():
        value = os.getenv(var)
        if value:
            check_pass(f"{var} is set ({description})")
        else:
            check_fail(f"{var} is NOT set ({description})")
            all_ok = False
    
    # Optional variables
    optional = {
        'OPENAI_API_KEY': 'OpenAI API Key (for LLM evaluation)'
    }
    
    for var, description in optional.items():
        value = os.getenv(var)
        if value:
            check_pass(f"{var} is set ({description})")
        else:
            check_warning(f"{var} is not set ({description}) - Optional, but recommended")
    
    return all_ok

def check_python_packages():
    """Check if required Python packages are installed."""
    print_header("Python Packages")
    
    required_packages = [
        'requests',
        'openai',
        'fastapi',
        'uvicorn',
        'pydantic',
        'playwright'
    ]
    
    all_ok = True
    
    for package in required_packages:
        try:
            __import__(package)
            check_pass(f"{package} is installed")
        except ImportError:
            check_fail(f"{package} is NOT installed")
            all_ok = False
    
    return all_ok

def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print_header("Playwright Browsers")
    
    try:
        result = subprocess.run(
            ['playwright', 'install', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'chromium' in result.stdout.lower() or 'already installed' in result.stdout.lower():
            check_pass("Playwright browsers are installed")
            return True
        else:
            check_fail("Playwright browsers are NOT installed")
            print("   Run: playwright install chromium")
            return False
    except Exception as e:
        check_fail(f"Could not check Playwright browsers: {str(e)}")
        return False

def check_files():
    """Check if required files exist."""
    print_header("Required Files")
    
    files = {
        'db.py': 'Database module',
        'task_templates.py': 'Task templates',
        'round1.py': 'Round 1 script',
        'round2.py': 'Round 2 script',
        'evaluate.py': 'Evaluation script',
        'api_server.py': 'API server'
    }
    
    all_ok = True
    
    for file, description in files.items():
        path = Path(file)
        if path.exists():
            check_pass(f"{file} exists ({description})")
        else:
            check_fail(f"{file} does NOT exist ({description})")
            all_ok = False
    
    return all_ok

def check_configuration():
    """Check configuration in scripts."""
    print_header("Configuration Check")
    
    all_ok = True
    
    # Check round1.py
    try:
        with open('round1.py', 'r') as f:
            content = f.read()
            if 'localhost' in content and 'EVALUATION_URL' in content:
                check_warning("round1.py still has localhost EVALUATION_URL - Update for production")
            else:
                check_pass("round1.py EVALUATION_URL appears to be configured")
    except FileNotFoundError:
        check_fail("round1.py not found")
        all_ok = False
    
    # Check round2.py
    try:
        with open('round2.py', 'r') as f:
            content = f.read()
            if 'localhost' in content and 'EVALUATION_URL' in content:
                check_warning("round2.py still has localhost EVALUATION_URL - Update for production")
            else:
                check_pass("round2.py EVALUATION_URL appears to be configured")
    except FileNotFoundError:
        check_fail("round2.py not found")
        all_ok = False
    
    return all_ok

def check_submissions_csv():
    """Check if submissions.csv exists."""
    print_header("Submissions File")
    
    if Path('submissions.csv').exists():
        check_pass("submissions.csv exists")
        
        # Try to read it
        try:
            import csv
            with open('submissions.csv', 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                required_headers = ['timestamp', 'email', 'endpoint', 'secret']
                missing = [h for h in required_headers if h not in headers]
                
                if missing:
                    check_fail(f"submissions.csv missing required columns: {', '.join(missing)}")
                    return False
                else:
                    check_pass("submissions.csv has all required columns")
                    
                    # Count rows
                    rows = list(reader)
                    check_pass(f"submissions.csv has {len(rows)} entries")
                    return True
        except Exception as e:
            check_fail(f"Could not read submissions.csv: {str(e)}")
            return False
    else:
        check_warning("submissions.csv does NOT exist - You'll need this to run round1.py")
        print("   Export from Google Form and save as submissions.csv")
        return False

def check_database():
    """Check if database can be initialized."""
    print_header("Database")
    
    try:
        from db import get_db
        db = get_db()
        check_pass("Database module loaded successfully")
        
        if Path('evaluation.db').exists():
            check_pass("evaluation.db exists")
        else:
            check_warning("evaluation.db does not exist yet (will be created on first run)")
        
        return True
    except Exception as e:
        check_fail(f"Could not load database module: {str(e)}")
        return False

def check_api_server():
    """Check if API server can be imported."""
    print_header("API Server")
    
    try:
        # Just try to import, don't start it
        import api_server
        check_pass("API server module loads successfully")
        check_warning("Remember to start the API server before running evaluation scripts")
        print("   Run: python api_server.py")
        return True
    except Exception as e:
        check_fail(f"Could not load API server: {str(e)}")
        return False

def main():
    """Main verification routine."""
    print("\n" + "🔍 " * 20)
    print("  EVALUATION SYSTEM SETUP VERIFICATION")
    print("🔍 " * 20)
    
    results = []
    
    # Run all checks
    results.append(("Environment Variables", check_environment_variables()))
    results.append(("Python Packages", check_python_packages()))
    results.append(("Playwright Browsers", check_playwright_browsers()))
    results.append(("Required Files", check_files()))
    results.append(("Configuration", check_configuration()))
    results.append(("Submissions CSV", check_submissions_csv()))
    results.append(("Database", check_database()))
    results.append(("API Server", check_api_server()))
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} checks passed\n")
    
    if passed == total:
        print("🎉 All checks passed! You're ready to run the evaluation system.")
        print("\nNext steps:")
        print("1. Update EVALUATION_URL in round1.py and round2.py")
        print("2. Ensure submissions.csv has student data")
        print("3. Start API server: python api_server.py")
        print("4. Run round 1: python round1.py submissions.csv")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nSee MANUAL_CHANGES.md for complete setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

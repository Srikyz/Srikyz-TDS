"""
Security audit script for the app builder system.
Checks for common security issues and provides recommendations.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Tuple


class SecurityAuditor:
    """Performs security checks on the app builder system."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def audit(self):
        """Run all security checks."""
        print("="*70)
        print("App Builder Security Audit")
        print("="*70)
        print()
        
        self.check_gitignore()
        self.check_secrets_file()
        self.check_environment_variables()
        self.check_config_file()
        self.check_code_for_secrets()
        self.check_file_permissions()
        self.check_dependencies()
        
        self.print_report()
    
    def check_gitignore(self):
        """Check if .gitignore properly excludes secrets."""
        print("[1/7] Checking .gitignore...")
        
        gitignore_path = Path('.gitignore')
        if not gitignore_path.exists():
            self.issues.append("❌ .gitignore file not found")
            return
        
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        required_patterns = [
            'secrets.json',
            '.env',
            'config.local.json',
            '*.key',
            '*.pem',
        ]
        
        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)
        
        if missing:
            self.warnings.append(f"⚠ .gitignore missing patterns: {', '.join(missing)}")
        else:
            self.passed.append("✓ .gitignore properly configured")
    
    def check_secrets_file(self):
        """Check if secrets.json exists and is properly formatted."""
        print("[2/7] Checking secrets.json...")
        
        secrets_path = Path('secrets.json')
        if not secrets_path.exists():
            self.warnings.append("⚠ secrets.json not found (create with manage_secrets.py)")
            return
        
        # Check file is not empty
        if secrets_path.stat().st_size == 0:
            self.warnings.append("⚠ secrets.json is empty")
            return
        
        # Check JSON is valid
        try:
            with open(secrets_path, 'r') as f:
                data = json.load(f)
            
            if 'secrets' not in data:
                self.issues.append("❌ secrets.json missing 'secrets' key")
                return
            
            # Check for plaintext secrets
            for email, secret_hash in data['secrets'].items():
                if len(secret_hash) < 32:
                    self.issues.append(f"❌ Secret for {email} appears to be plaintext, not hashed!")
                    return
            
            self.passed.append(f"✓ secrets.json valid ({len(data['secrets'])} secrets)")
            
        except json.JSONDecodeError:
            self.issues.append("❌ secrets.json is not valid JSON")
    
    def check_environment_variables(self):
        """Check if sensitive data is in environment variables."""
        print("[3/7] Checking environment variables...")
        
        github_token = os.getenv('GITHUB_TOKEN')
        github_username = os.getenv('GITHUB_USERNAME')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not github_token:
            self.warnings.append("⚠ GITHUB_TOKEN not set in environment")
        elif not github_token.startswith('ghp_'):
            self.issues.append("❌ GITHUB_TOKEN appears invalid (should start with ghp_)")
        else:
            self.passed.append("✓ GITHUB_TOKEN set")
        
        if not github_username:
            self.warnings.append("⚠ GITHUB_USERNAME not set in environment")
        else:
            self.passed.append("✓ GITHUB_USERNAME set")
        
        if openai_key:
            if not openai_key.startswith('sk-'):
                self.warnings.append("⚠ OPENAI_API_KEY appears invalid")
            else:
                self.passed.append("✓ OPENAI_API_KEY set")
    
    def check_config_file(self):
        """Check config.json for hardcoded secrets."""
        print("[4/7] Checking config.json...")
        
        config_path = Path('config.json')
        if not config_path.exists():
            self.warnings.append("⚠ config.json not found")
            return
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for hardcoded secrets
        sensitive_keys = ['api_key', 'token', 'password', 'secret']
        for key, value in config.items():
            if any(s in key.lower() for s in sensitive_keys):
                if value and len(str(value)) > 10:
                    self.issues.append(f"❌ config.json contains hardcoded secret: {key}")
                    return
        
        self.passed.append("✓ config.json has no hardcoded secrets")
    
    def check_code_for_secrets(self):
        """Scan Python files for potential secrets."""
        print("[5/7] Scanning code for secrets...")
        
        # Patterns that might indicate secrets
        secret_patterns = [
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub token'),
            (r'sk-[a-zA-Z0-9]{32,}', 'OpenAI API key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
            (r'["\']password["\']\s*[:=]\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
        ]
        
        python_files = list(Path('.').glob('*.py'))
        
        for file_path in python_files:
            if 'test' in file_path.name or 'example' in file_path.name:
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, secret_type in secret_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    self.issues.append(f"❌ {file_path.name} may contain {secret_type}")
                    return
        
        self.passed.append("✓ No secrets found in code")
    
    def check_file_permissions(self):
        """Check file permissions on sensitive files."""
        print("[6/7] Checking file permissions...")
        
        if os.name != 'posix':
            self.warnings.append("⚠ File permission check skipped (Windows)")
            return
        
        sensitive_files = ['secrets.json', 'config.json']
        
        for filename in sensitive_files:
            file_path = Path(filename)
            if not file_path.exists():
                continue
            
            # Check permissions (should be 600 or similar)
            mode = file_path.stat().st_mode
            # Check if file is readable by others
            if mode & 0o004:
                self.warnings.append(f"⚠ {filename} is readable by others (chmod 600 recommended)")
        
        self.passed.append("✓ File permissions checked")
    
    def check_dependencies(self):
        """Check for known vulnerabilities in dependencies."""
        print("[7/7] Checking dependencies...")
        
        # This would ideally use `safety` or `pip-audit`
        try:
            import subprocess
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.passed.append("✓ Dependencies listed successfully")
                self.warnings.append("⚠ Run 'pip-audit' for security vulnerability scan")
            else:
                self.warnings.append("⚠ Could not check dependencies")
                
        except Exception as e:
            self.warnings.append(f"⚠ Could not check dependencies: {e}")
    
    def print_report(self):
        """Print the audit report."""
        print()
        print("="*70)
        print("Security Audit Report")
        print("="*70)
        print()
        
        if self.passed:
            print("✓ PASSED CHECKS:")
            for item in self.passed:
                print(f"  {item}")
            print()
        
        if self.warnings:
            print("⚠ WARNINGS:")
            for item in self.warnings:
                print(f"  {item}")
            print()
        
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for item in self.issues:
                print(f"  {item}")
            print()
        
        print("="*70)
        print(f"Summary: {len(self.passed)} passed, {len(self.warnings)} warnings, {len(self.issues)} issues")
        print("="*70)
        print()
        
        if self.issues:
            print("🔴 ACTION REQUIRED: Fix critical issues before deployment!")
            return 1
        elif self.warnings:
            print("🟡 Review warnings and address as needed")
            return 0
        else:
            print("🟢 All security checks passed!")
            return 0


def main():
    """Run the security audit."""
    auditor = SecurityAuditor()
    return auditor.audit()


if __name__ == '__main__':
    import sys
    sys.exit(main())

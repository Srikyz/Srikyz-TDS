"""
Script to import secrets from Google Form responses.
Run this after exporting responses from Google Forms.
"""

import csv
import sys
from pathlib import Path
from secret_manager import SecretManager


def import_from_csv(csv_path: str):
    """
    Import secrets from Google Form CSV export.
    
    Expected CSV columns:
    - Timestamp
    - Email Address (or just "Email")
    - Secret (or "What is your secret key?")
    
    Args:
        csv_path: Path to CSV file
    """
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return
    
    manager = SecretManager()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Try to detect the delimiter
            sample = f.read(1024)
            f.seek(0)
            
            # Auto-detect delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            # Find the email and secret columns
            headers = reader.fieldnames
            print(f"Found columns: {headers}")
            
            # Try to find email column
            email_col = None
            for col in headers:
                if 'email' in col.lower():
                    email_col = col
                    break
            
            # Try to find secret column
            secret_col = None
            for col in headers:
                if 'secret' in col.lower() or 'key' in col.lower():
                    secret_col = col
                    break
            
            if not email_col or not secret_col:
                print("❌ Could not find Email and Secret columns")
                print(f"   Available columns: {headers}")
                print("\n   Please ensure your CSV has columns containing 'Email' and 'Secret'")
                return
            
            print(f"\n✓ Using columns:")
            print(f"  - Email: {email_col}")
            print(f"  - Secret: {secret_col}")
            print()
            
            # Import secrets
            count = 0
            errors = 0
            
            for i, row in enumerate(reader, 1):
                email = row.get(email_col, '').strip()
                secret = row.get(secret_col, '').strip()
                
                if not email:
                    print(f"⚠ Row {i}: Empty email, skipping")
                    errors += 1
                    continue
                
                if not secret:
                    print(f"⚠ Row {i}: Empty secret for {email}, skipping")
                    errors += 1
                    continue
                
                if len(secret) < 8:
                    print(f"⚠ Row {i}: Secret too short for {email} (must be ≥8 chars), skipping")
                    errors += 1
                    continue
                
                if manager.register_secret(email, secret):
                    count += 1
                    print(f"✓ Registered: {email}")
                else:
                    print(f"❌ Failed: {email}")
                    errors += 1
            
            print(f"\n{'='*60}")
            print(f"✓ Import complete!")
            print(f"  - Successfully imported: {count}")
            print(f"  - Errors: {errors}")
            print(f"  - Total registered secrets: {len(manager.list_registered_emails())}")
            print(f"{'='*60}")
            
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()


def list_secrets():
    """List all registered email addresses."""
    manager = SecretManager()
    emails = manager.list_registered_emails()
    
    print(f"\n{'='*60}")
    print(f"Registered Secrets ({len(emails)} total)")
    print(f"{'='*60}")
    
    if emails:
        for i, email in enumerate(sorted(emails), 1):
            print(f"{i:3}. {email}")
    else:
        print("No secrets registered yet.")
    
    print(f"{'='*60}\n")


def add_secret(email: str, secret: str):
    """Add a single secret manually."""
    manager = SecretManager()
    
    if manager.register_secret(email, secret):
        print(f"✓ Secret registered for {email}")
    else:
        print(f"❌ Failed to register secret for {email}")


def remove_secret(email: str):
    """Remove a secret."""
    manager = SecretManager()
    
    if manager.remove_secret(email):
        print(f"✓ Removed secret for {email}")
    else:
        print(f"❌ Secret not found for {email}")


def verify_secret(email: str, secret: str):
    """Verify a secret."""
    manager = SecretManager()
    
    if manager.verify_secret(email, secret):
        print(f"✓ Secret verified for {email}")
    else:
        print(f"❌ Secret verification failed for {email}")


def print_usage():
    """Print usage instructions."""
    print("""
App Builder Secret Manager
===========================

Usage:
  python manage_secrets.py import <csv_file>     Import from Google Form CSV
  python manage_secrets.py list                  List all registered emails
  python manage_secrets.py add <email> <secret>  Add a secret manually
  python manage_secrets.py remove <email>        Remove a secret
  python manage_secrets.py verify <email> <secret> Test secret verification

Examples:
  python manage_secrets.py import form_responses.csv
  python manage_secrets.py list
  python manage_secrets.py add student@example.com my-secret-123
  python manage_secrets.py verify student@example.com my-secret-123
  python manage_secrets.py remove student@example.com

CSV Format:
  Your Google Form CSV should have columns like:
  - "Email Address" or "Email"
  - "Secret" or "What is your secret key?"

Security:
  - Secrets are stored as hashes in secrets.json
  - Never commit secrets.json to git (it's in .gitignore)
  - Use environment variable APP_BUILDER_SECRETS for production
""")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'import':
        if len(sys.argv) < 3:
            print("❌ Error: CSV file path required")
            print("Usage: python manage_secrets.py import <csv_file>")
            return
        import_from_csv(sys.argv[2])
    
    elif command == 'list':
        list_secrets()
    
    elif command == 'add':
        if len(sys.argv) < 4:
            print("❌ Error: Email and secret required")
            print("Usage: python manage_secrets.py add <email> <secret>")
            return
        add_secret(sys.argv[2], sys.argv[3])
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("❌ Error: Email required")
            print("Usage: python manage_secrets.py remove <email>")
            return
        
        email = sys.argv[2]
        confirm = input(f"⚠ Remove secret for {email}? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            remove_secret(email)
        else:
            print("Cancelled.")
    
    elif command == 'verify':
        if len(sys.argv) < 4:
            print("❌ Error: Email and secret required")
            print("Usage: python manage_secrets.py verify <email> <secret>")
            return
        verify_secret(sys.argv[2], sys.argv[3])
    
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main()

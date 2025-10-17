"""
Secret manager for verifying student secrets from Google Form submissions.
Securely stores and validates secrets without exposing them in code or git history.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Manages student secrets for verification.
    Secrets are stored as hashes, never in plaintext in git.
    """
    
    def __init__(self, secrets_file: str = "secrets.json"):
        """
        Initialize the secret manager.
        
        Args:
            secrets_file: Path to secrets file (should be in .gitignore)
        """
        self.secrets_file = Path(secrets_file)
        self.secrets = self._load_secrets()
    
    def _load_secrets(self) -> Dict[str, str]:
        """
        Load secrets from file or environment.
        
        Returns:
            Dictionary mapping email to hashed secret
        """
        secrets = {}
        
        # Try to load from file
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    secrets = data.get('secrets', {})
                logger.info(f"Loaded {len(secrets)} secrets from {self.secrets_file}")
            except Exception as e:
                logger.error(f"Failed to load secrets file: {e}")
        
        # Also check environment variable for secrets (for production)
        env_secrets = os.getenv('APP_BUILDER_SECRETS')
        if env_secrets:
            try:
                env_data = json.loads(env_secrets)
                secrets.update(env_data)
                logger.info(f"Loaded secrets from environment variable")
            except Exception as e:
                logger.error(f"Failed to parse secrets from environment: {e}")
        
        return secrets
    
    def _save_secrets(self):
        """Save secrets to file."""
        try:
            self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.secrets_file, 'w', encoding='utf-8') as f:
                json.dump({'secrets': self.secrets}, f, indent=2)
            logger.info(f"Saved {len(self.secrets)} secrets to {self.secrets_file}")
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
    
    def _hash_secret(self, secret: str, email: str) -> str:
        """
        Hash a secret with email as salt.
        
        Args:
            secret: Plain text secret
            email: Email address (used as salt)
            
        Returns:
            Hashed secret
        """
        # Use email as salt to make hashes unique per user
        salted = f"{email}:{secret}"
        return hashlib.sha256(salted.encode()).hexdigest()
    
    def register_secret(self, email: str, secret: str) -> bool:
        """
        Register a new secret for an email.
        This should be called when processing Google Form submissions.
        
        Args:
            email: Student email
            secret: Plain text secret from form
            
        Returns:
            True if registered successfully
        """
        try:
            # Validate inputs
            if not email or not secret:
                logger.error("Email and secret are required")
                return False
            
            if len(secret) < 8:
                logger.error("Secret must be at least 8 characters")
                return False
            
            # Hash and store
            hashed = self._hash_secret(secret, email)
            self.secrets[email] = hashed
            self._save_secrets()
            
            logger.info(f"Registered secret for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register secret: {e}")
            return False
    
    def verify_secret(self, email: str, secret: str) -> bool:
        """
        Verify a secret against stored hash.
        
        Args:
            email: Student email
            secret: Plain text secret to verify
            
        Returns:
            True if secret matches, False otherwise
        """
        try:
            # Check if email exists
            if email not in self.secrets:
                logger.warning(f"No secret found for {email}")
                return False
            
            # Hash the provided secret
            hashed = self._hash_secret(secret, email)
            
            # Compare with stored hash
            is_valid = hashed == self.secrets[email]
            
            if is_valid:
                logger.info(f"Secret verified for {email}")
            else:
                logger.warning(f"Secret verification failed for {email}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying secret: {e}")
            return False
    
    def import_from_google_form_csv(self, csv_path: str):
        """
        Import secrets from Google Form CSV export.
        
        Expected CSV format:
        Timestamp, Email, Secret
        
        Args:
            csv_path: Path to CSV file
        """
        try:
            import csv
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                count = 0
                for row in reader:
                    email = row.get('Email', '').strip()
                    secret = row.get('Secret', '').strip()
                    
                    if email and secret:
                        if self.register_secret(email, secret):
                            count += 1
                
                logger.info(f"Imported {count} secrets from {csv_path}")
                
        except Exception as e:
            logger.error(f"Failed to import from CSV: {e}")
    
    def list_registered_emails(self) -> list:
        """Get list of registered email addresses (for admin purposes)."""
        return list(self.secrets.keys())
    
    def remove_secret(self, email: str) -> bool:
        """
        Remove a secret (for admin purposes).
        
        Args:
            email: Email to remove
            
        Returns:
            True if removed, False if not found
        """
        if email in self.secrets:
            del self.secrets[email]
            self._save_secrets()
            logger.info(f"Removed secret for {email}")
            return True
        return False


def init_secrets_from_env():
    """
    Initialize secrets from environment or create empty file.
    This should be run during setup.
    """
    manager = SecretManager()
    
    if not manager.secrets:
        logger.info("No secrets loaded. You can:")
        logger.info("1. Import from Google Form CSV: manager.import_from_google_form_csv('form_responses.csv')")
        logger.info("2. Register manually: manager.register_secret('email@example.com', 'secret')")
        logger.info("3. Set APP_BUILDER_SECRETS environment variable")
    else:
        logger.info(f"Loaded {len(manager.secrets)} secrets")
    
    return manager


if __name__ == "__main__":
    # Example usage
    manager = SecretManager()
    
    # Register a test secret
    manager.register_secret("student@example.com", "test-secret-12345")
    
    # Verify it
    is_valid = manager.verify_secret("student@example.com", "test-secret-12345")
    print(f"Verification result: {is_valid}")
    
    # Try wrong secret
    is_valid = manager.verify_secret("student@example.com", "wrong-secret")
    print(f"Wrong secret result: {is_valid}")

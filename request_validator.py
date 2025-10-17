"""
Request validator for the app builder system.
Validates incoming requests for building and revising apps.
"""

import re
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class RequestValidator:
    """Validates request data for app building and revision."""
    
    REQUIRED_FIELDS = ['email', 'secret', 'task', 'round', 'nonce', 'brief', 'checks', 'evaluation_url']
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self, secret_manager: Optional[Any] = None):
        """
        Initialize the validator.
        
        Args:
            secret_manager: SecretManager instance for verifying secrets
        """
        self.secret_manager = secret_manager
        self.stored_secrets = {}  # Fallback for backward compatibility
    
    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a build request.
        
        Args:
            request_data: The request dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in request_data:
                return False, f"Missing required field: {field}"
        
        # Validate email format
        if not self.EMAIL_PATTERN.match(request_data['email']):
            return False, "Invalid email format"
        
        # Validate secret (store it for later revision verification)
        secret = request_data['secret']
        if not secret or len(secret) < 8:
            return False, "Secret must be at least 8 characters long"
        
        task_id = request_data['task']
        self.stored_secrets[task_id] = secret
        
        # Validate task ID format
        if not task_id or len(task_id) < 3:
            return False, "Invalid task ID"
        
        # Validate round number
        round_num = request_data['round']
        if not isinstance(round_num, int) or round_num < 1:
            return False, "Round must be a positive integer"
        
        # Validate nonce
        if not request_data['nonce']:
            return False, "Nonce cannot be empty"
        
        # Validate brief
        if not request_data['brief'] or len(request_data['brief']) < 10:
            return False, "Brief must be at least 10 characters long"
        
        # Validate checks
        checks = request_data['checks']
        if not isinstance(checks, list) or len(checks) == 0:
            return False, "Checks must be a non-empty list"
        
        # Validate evaluation URL
        eval_url = request_data['evaluation_url']
        if not eval_url.startswith('http://') and not eval_url.startswith('https://'):
            return False, "Evaluation URL must start with http:// or https://"
        
        logger.info(f"Request validation passed for task: {task_id}")
        return True, ""
    
    def validate_revision_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a revision request.
        
        Args:
            request_data: The revision request dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # First, validate as a normal request
        is_valid, error_msg = self.validate_request(request_data)
        if not is_valid:
            return False, error_msg
        
        # Verify the secret matches the stored one
        task_id = request_data['task']
        provided_secret = request_data['secret']
        
        stored_secret = self.stored_secrets.get(task_id)
        if not stored_secret:
            return False, "No stored secret found for this task. Was the initial build completed?"
        
        if provided_secret != stored_secret:
            return False, "Secret verification failed"
        
        logger.info(f"Revision request validation passed for task: {task_id}")
        return True, ""
    
    def store_secret(self, task_id: str, secret: str):
        """Store a secret for later verification."""
        self.stored_secrets[task_id] = secret
    
    def get_secret(self, task_id: str) -> str:
        """Retrieve a stored secret."""
        return self.stored_secrets.get(task_id)

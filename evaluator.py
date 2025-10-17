"""
Evaluation notifier for the app builder system.
Sends notifications to evaluation APIs with repository details.
Implements exponential backoff retry logic for reliability.
"""

import requests
from typing import Dict, Any
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class EvaluationNotifier:
    """Notifies evaluation APIs about deployments with retry logic."""
    
    def __init__(self):
        """Initialize the notifier."""
        self.timeout = 30  # seconds per request
        self.max_retries = 7  # 1, 2, 4, 8, 16, 32, 64 seconds = ~127 seconds total
        self.base_delay = 1  # Base delay in seconds
    
    def notify(self, evaluation_url: str, repo_url: str, commit_sha: str, 
               pages_url: str, nonce: str, email: str, task: str, round_num: int) -> Dict[str, Any]:
        """
        Send a notification to the evaluation API with retry logic.
        
        Implements exponential backoff: 1, 2, 4, 8, 16, 32, 64 seconds
        Ensures HTTP 200 response or retries until max attempts reached.
        
        Args:
            evaluation_url: The URL to send the notification to
            repo_url: GitHub repository URL
            commit_sha: Git commit SHA
            pages_url: GitHub Pages URL
            nonce: Nonce from the original request
            email: Student email
            task: Task ID
            round_num: Round number
            
        Returns:
            Result dictionary with success status
        """
        request_id = f"{task}-r{round_num}"
        logger.info(f"[{request_id}] Sending notification to: {evaluation_url}")
        
        # Build notification payload (exact format as specified)
        # Fields copied from request: email, task, round, nonce
        # Fields from deployment: repo_url, commit_sha, pages_url
        payload = {
            'email': email,
            'task': task,
            'round': round_num,
            'nonce': nonce,
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }
        
        logger.debug(f"[{request_id}] Payload: {payload}")
        
        # Try to send with exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"[{request_id}] Attempt {attempt + 1}/{self.max_retries + 1}")
                
                # Send POST request
                response = requests.post(
                    evaluation_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )
                
                # Check for HTTP 200 specifically
                if response.status_code == 200:
                    logger.info(f"[{request_id}] ✓ Notification sent successfully: HTTP 200")
                    return {
                        'success': True,
                        'status_code': 200,
                        'response': response.text,
                        'attempts': attempt + 1
                    }
                else:
                    # Non-200 response - will retry
                    logger.warning(f"[{request_id}] Received HTTP {response.status_code}, will retry")
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    # If this was the last attempt, return failure
                    if attempt >= self.max_retries:
                        logger.error(f"[{request_id}] Max retries reached, giving up")
                        return {
                            'success': False,
                            'status_code': response.status_code,
                            'error': error_msg,
                            'attempts': attempt + 1
                        }
                    
                    # Calculate delay for next attempt: 1, 2, 4, 8, 16, 32, 64 seconds
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"[{request_id}] Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
            except requests.exceptions.Timeout:
                logger.warning(f"[{request_id}] Request timed out")
                
                if attempt >= self.max_retries:
                    logger.error(f"[{request_id}] Max retries reached after timeout")
                    return {
                        'success': False,
                        'error': 'Request timed out after all retries',
                        'attempts': attempt + 1
                    }
                
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"[{request_id}] Retrying in {delay} seconds after timeout...")
                time.sleep(delay)
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"[{request_id}] Connection error: {str(e)[:100]}")
                
                if attempt >= self.max_retries:
                    logger.error(f"[{request_id}] Max retries reached after connection error")
                    return {
                        'success': False,
                        'error': f'Connection error: {str(e)}',
                        'attempts': attempt + 1
                    }
                
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"[{request_id}] Retrying in {delay} seconds after connection error...")
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"[{request_id}] Request exception: {str(e)[:100]}")
                
                if attempt >= self.max_retries:
                    logger.error(f"[{request_id}] Max retries reached after request exception")
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1
                    }
                
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"[{request_id}] Retrying in {delay} seconds after exception...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
                
                if attempt >= self.max_retries:
                    return {
                        'success': False,
                        'error': f'Unexpected error: {str(e)}',
                        'attempts': attempt + 1
                    }
                
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"[{request_id}] Retrying in {delay} seconds after unexpected error...")
                time.sleep(delay)
        
        # Should never reach here, but just in case
        logger.error(f"[{request_id}] Failed to send notification after all attempts")
        return {
            'success': False,
            'error': 'Failed after all retry attempts',
            'attempts': self.max_retries + 1
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + 'Z'

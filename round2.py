"""
Round 2 task generator and dispatcher.

For each repository in the repos table (from Round 1):
1. Skip if results indicate failure or Round 2 already exists
2. Generate Round 2 task with same template but new brief/checks
3. POST to student endpoint
4. Log to tasks table

Usage:
    python round2.py

Author: Evaluation System
Date: 2025-10-16
"""

import sys
import logging
import requests
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import time

from db import get_db
from task_templates import get_template, generate_task_id

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/round2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EVALUATION_URL = "http://localhost:8000/api/evaluation"  # TODO: Update with actual URL
REQUEST_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAYS = [60, 180, 600]  # 1 min, 3 mins, 10 mins


def get_template_from_task_id(task_id: str):
    """Extract template ID from task ID (format: template-id-hash)."""
    parts = task_id.split('-')
    if len(parts) >= 2:
        # Handle multi-part template IDs like "image-viewer"
        template_id = '-'.join(parts[:-1])
        return get_template(template_id)
    return None


def generate_round2_task(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Round 2 task for an existing repository."""
    # Get timestamp in YYYY-MM-DD-HH format
    dt = datetime.utcnow()
    timestamp_hour = dt.strftime("%Y-%m-%d-%H")
    
    # Get the original template
    template = get_template_from_task_id(repo['task'])
    if not template:
        logger.error(f"Could not determine template from task ID: {repo['task']}")
        return None
    
    # Generate Round 2 content with same seed (for consistency)
    seed = f"{repo['email']}-{timestamp_hour}"
    task_content = template.generate(2, repo['email'], timestamp_hour)
    
    # Generate new task ID for Round 2
    task_id = generate_task_id(
        template.id,
        task_content['brief'],
        task_content['attachments']
    )
    
    # Generate new nonce
    nonce = str(uuid.uuid4())
    
    # Get original task to get endpoint and secret
    db = get_db()
    original_task = db.get_task_by_nonce(repo['nonce'])
    
    if not original_task:
        logger.error(f"Original task not found for repo: {repo['email']}")
        return None
    
    # Build Round 2 task
    task = {
        'timestamp': dt.isoformat(),
        'email': repo['email'],
        'task': task_id,
        'round': 2,
        'nonce': nonce,
        'brief': task_content['brief'],
        'attachments': task_content['attachments'],
        'checks': task_content['checks'],
        'evaluation_url': EVALUATION_URL,
        'endpoint': original_task['endpoint'],
        'secret': original_task['secret']
    }
    
    logger.info(f"Generated Round 2 task {task_id} for {repo['email']} (template: {template.id})")
    return task


def post_task_to_student(task: Dict[str, Any]) -> tuple[int, str]:
    """
    POST Round 2 task to student's endpoint.
    
    Returns: (status_code, error_message)
    """
    endpoint = task['endpoint']
    
    # Build payload
    payload = {
        'email': task['email'],
        'task': task['task'],
        'round': task['round'],
        'nonce': task['nonce'],
        'brief': task['brief'],
        'attachments': task['attachments'],
        'checks': task['checks'],
        'evaluation_url': task['evaluation_url'],
        'secret': task['secret']
    }
    
    # Try up to MAX_RETRIES times
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES}: POSTing Round 2 to {endpoint}")
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            status_code = response.status_code
            logger.info(f"Student API responded: {status_code}")
            
            if status_code == 200:
                return (status_code, None)
            else:
                error_msg = f"HTTP {status_code}: {response.text[:200]}"
                logger.warning(f"Student API error: {error_msg}")
                
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    return (status_code, error_msg)
        
        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {REQUEST_TIMEOUT}s"
            logger.error(error_msg)
            
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return (0, error_msg)
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return (0, error_msg)
    
    return (0, "Failed after all retries")


def should_generate_round2(repo: Dict[str, Any], db) -> bool:
    """
    Determine if Round 2 should be generated for this repo.
    
    Skip if:
    - Round 2 task already exists
    - Round 1 evaluation failed critically
    """
    email = repo['email']
    
    # Check if Round 2 task already exists
    if db.task_exists(email, repo['task'], 2):
        logger.info(f"Skipping {email} - Round 2 task already exists")
        return False
    
    # Check if Round 2 repo submission already exists
    if db.repo_exists(email, repo['task'], 2):
        logger.info(f"Skipping {email} - Round 2 repo already submitted")
        return False
    
    # Optional: Check if Round 1 evaluation passed minimum criteria
    results = db.get_results(email=email, round=1)
    
    if not results:
        logger.warning(f"No Round 1 results found for {email}, generating Round 2 anyway")
        return True
    
    # Check if any critical checks failed
    critical_checks = ['mit_license', 'page_load']
    for result in results:
        if result['check'] in critical_checks and result['score'] == 0:
            logger.warning(f"Skipping {email} - Critical check failed: {result['check']}")
            return False
    
    logger.info(f"{email} passed Round 1 checks, generating Round 2")
    return True


def process_repos():
    """Process all Round 1 repos and generate Round 2 tasks."""
    db = get_db()
    
    # Get all Round 1 repos
    repos = db.get_repos_to_evaluate(round=1)
    logger.info(f"Found {len(repos)} Round 1 repositories")
    
    processed = 0
    skipped = 0
    failed = 0
    
    for repo in repos:
        email = repo['email']
        
        # Check if should generate Round 2
        if not should_generate_round2(repo, db):
            skipped += 1
            continue
        
        # Generate Round 2 task
        task = generate_round2_task(repo)
        
        if not task:
            logger.error(f"Failed to generate Round 2 task for {email}")
            failed += 1
            continue
        
        # POST to student endpoint
        status_code, error = post_task_to_student(task)
        
        # Log to database
        task['statuscode'] = status_code
        task['error'] = error
        db.insert_task(task)
        
        if status_code == 200:
            processed += 1
            logger.info(f"✓ Successfully sent Round 2 to {email}")
        else:
            failed += 1
            logger.error(f"✗ Failed to send Round 2 to {email}: {error}")
        
        # Small delay between requests
        time.sleep(1)
    
    logger.info(f"\nRound 2 Summary:")
    logger.info(f"  Processed: {processed}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total: {len(repos)}")


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Round 2 Task Generator")
    logger.info("=" * 60)
    
    process_repos()
    
    logger.info("\nRound 2 complete!")
    logger.info(f"Check the database for results: evaluation.db")
    logger.info(f"Check logs: logs/round2.log")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    main()

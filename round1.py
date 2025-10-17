"""
Round 1 task generator and dispatcher.

Reads submissions.csv, generates parametrized tasks from templates,
POSTs them to student endpoints, and logs results to the tasks table.

Usage:
    python round1.py submissions.csv

CSV format: timestamp,email,endpoint,secret

Author: Evaluation System
Date: 2025-10-16
"""

import csv
import sys
import logging
import requests
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import time

from db import get_db
from task_templates import get_random_template, generate_task_id

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/round1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EVALUATION_URL = "http://localhost:8000/api/evaluation"  # TODO: Update with actual evaluation URL
REQUEST_TIMEOUT = 300  # 5 minutes timeout for student API
MAX_RETRIES = 3  # Retry up to 3 times if student API fails
RETRY_DELAYS = [60, 180, 600]  # 1 min, 3 mins, 10 mins (in seconds, over 3-24 hours as per spec)


def read_submissions(csv_path: Path) -> List[Dict[str, str]]:
    """Read submissions from CSV file."""
    submissions = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            submissions.append({
                'timestamp': row['timestamp'],
                'email': row['email'],
                'endpoint': row['endpoint'],
                'secret': row['secret']
            })
    
    logger.info(f"Read {len(submissions)} submissions from {csv_path}")
    return submissions


def generate_task(submission: Dict[str, str], round: int = 1) -> Dict[str, Any]:
    """Generate a parametrized task for a submission."""
    # Get timestamp in YYYY-MM-DD-HH format for hourly expiry
    dt = datetime.utcnow()
    timestamp_hour = dt.strftime("%Y-%m-%d-%H")
    
    # Generate seed for template selection and parametrization
    seed = f"{submission['email']}-{timestamp_hour}"
    
    # Randomly pick a template based on seed
    template = get_random_template(seed)
    
    # Generate parametrized task content
    task_content = template.generate(round, submission['email'], timestamp_hour)
    
    # Generate task ID: {template.id}-{hash[:5]}
    task_id = generate_task_id(
        template.id,
        task_content['brief'],
        task_content['attachments']
    )
    
    # Generate nonce (UUID7 for timestamp ordering)
    nonce = str(uuid.uuid4())
    
    # Build task
    task = {
        'timestamp': dt.isoformat(),
        'email': submission['email'],
        'task': task_id,
        'round': round,
        'nonce': nonce,
        'brief': task_content['brief'],
        'attachments': task_content['attachments'],
        'checks': task_content['checks'],
        'evaluation_url': EVALUATION_URL,
        'endpoint': submission['endpoint'],
        'secret': submission['secret']
    }
    
    logger.info(f"Generated task {task_id} for {submission['email']} (template: {template.id})")
    return task


def post_task_to_student(task: Dict[str, Any]) -> tuple[int, str]:
    """
    POST task to student's endpoint.
    
    Returns: (status_code, error_message)
    """
    endpoint = task['endpoint']
    
    # Build payload (exclude internal fields)
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
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES}: POSTing to {endpoint}")
            
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
                
                # If not the last attempt, wait before retry
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


def process_submissions(submissions: List[Dict[str, str]], round: int = 1):
    """Process all submissions and generate tasks."""
    db = get_db()
    
    processed = 0
    skipped = 0
    failed = 0
    
    for submission in submissions:
        email = submission['email']
        
        # Check if task already exists for this email and round
        # Note: We generate the task first to get the task ID
        task = generate_task(submission, round)
        
        if db.task_exists(email, task['task'], round):
            logger.info(f"Skipping {email} - task already exists for round {round}")
            skipped += 1
            continue
        
        # POST to student endpoint
        status_code, error = post_task_to_student(task)
        
        # Log to database
        task['statuscode'] = status_code
        task['error'] = error
        db.insert_task(task)
        
        if status_code == 200:
            processed += 1
            logger.info(f"✓ Successfully processed {email}")
        else:
            failed += 1
            logger.error(f"✗ Failed to process {email}: {error}")
        
        # Small delay between requests to avoid overwhelming student APIs
        time.sleep(1)
    
    logger.info(f"\nRound {round} Summary:")
    logger.info(f"  Processed: {processed}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total: {len(submissions)}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python round1.py submissions.csv")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Round 1 Task Generator")
    logger.info("=" * 60)
    
    # Read submissions
    submissions = read_submissions(csv_path)
    
    # Process submissions
    process_submissions(submissions, round=1)
    
    logger.info("\nRound 1 complete!")
    logger.info(f"Check the database for results: evaluation.db")
    logger.info(f"Check logs: logs/round1.log")


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    main()

"""
Utility functions for the app builder system.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'app_builder_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger


def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return get_default_config()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        'llm_model': 'gpt-4',
        'llm_api_key': os.getenv('OPENAI_API_KEY'),
        'github_token': os.getenv('GITHUB_TOKEN'),
        'github_username': os.getenv('GITHUB_USERNAME'),
        'log_level': 'INFO'
    }


def save_attachments(attachments: List[Dict[str, str]], output_dir: Path) -> str:
    """
    Save attachments from data URIs to files.
    
    Args:
        attachments: List of attachment dictionaries with 'name' and 'url' keys
        output_dir: Directory to save attachments to
        
    Returns:
        Path to attachments directory
    """
    if not attachments:
        return None
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for attachment in attachments:
        name = attachment['name']
        data_uri = attachment['url']
        
        try:
            # Parse data URI
            if data_uri.startswith('data:'):
                # Format: data:mime/type;base64,<data>
                header, encoded = data_uri.split(',', 1)
                
                # Decode base64
                file_data = base64.b64decode(encoded)
                
                # Write to file
                file_path = output_dir / name
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                logger.info(f"Saved attachment: {name} ({len(file_data)} bytes)")
            else:
                logger.warning(f"Unsupported attachment format for {name}")
                
        except Exception as e:
            logger.error(f"Failed to save attachment {name}: {e}")
    
    return str(output_dir)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to make it safe for filesystems.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    return filename


def extract_repo_info(repo_url: str) -> Dict[str, str]:
    """
    Extract owner and repo name from a GitHub URL.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Dictionary with 'owner' and 'repo' keys
    """
    # Example: https://github.com/owner/repo or git@github.com:owner/repo.git
    
    if 'github.com' in repo_url:
        parts = repo_url.rstrip('/').rstrip('.git').split('/')
        repo = parts[-1]
        owner = parts[-2] if len(parts) >= 2 else None
        
        return {
            'owner': owner,
            'repo': repo
        }
    
    return {'owner': None, 'repo': None}


def format_checks_list(checks: List[str]) -> str:
    """
    Format a list of checks into a readable string.
    
    Args:
        checks: List of check descriptions
        
    Returns:
        Formatted string with checkboxes
    """
    formatted = []
    for i, check in enumerate(checks, 1):
        formatted.append(f"  [ ] {i}. {check}")
    
    return '\n'.join(formatted)


def validate_github_credentials() -> bool:
    """
    Validate that GitHub credentials are configured.
    
    Returns:
        True if credentials are available, False otherwise
    """
    token = os.getenv('GITHUB_TOKEN')
    username = os.getenv('GITHUB_USERNAME')
    
    if not token:
        logger.error("GITHUB_TOKEN environment variable not set")
        return False
    
    if not username:
        logger.error("GITHUB_USERNAME environment variable not set")
        return False
    
    logger.info("GitHub credentials validated")
    return True


def print_summary(result: Dict[str, Any]):
    """
    Print a formatted summary of the operation result.
    
    Args:
        result: Result dictionary
    """
    print("\n" + "="*80)
    print("OPERATION SUMMARY")
    print("="*80)
    
    if result.get('success'):
        print("✓ Status: SUCCESS")
        print(f"\n📦 Repository: {result.get('repo_url')}")
        print(f"🌐 Live URL: {result.get('pages_url')}")
        print(f"📝 Commit: {result.get('commit_sha')}")
        print(f"✉️  Notification: {'Sent' if result.get('notification_sent') else 'Failed'}")
    else:
        print("✗ Status: FAILED")
        print(f"\n❌ Error: {result.get('error')}")
    
    print("="*80 + "\n")

"""
Main orchestrator for the automated app builder system.
Handles receiving requests, building apps, deploying to GitHub Pages, and notifying evaluation APIs.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from request_validator import RequestValidator
from app_generator import AppGenerator
from github_deployer import GitHubDeployer
from evaluator import EvaluationNotifier
from utils import setup_logging, save_attachments, load_config

# Setup logging
logger = setup_logging()


class AppBuilderOrchestrator:
    """Main orchestrator for the app builder system."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the orchestrator with configuration."""
        self.config = load_config(config_path)
        self.validator = RequestValidator()
        self.generator = AppGenerator(self.config)
        self.deployer = GitHubDeployer(self.config)
        self.notifier = EvaluationNotifier()
        
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single request to build and deploy an app.
        
        Args:
            request_data: The request JSON containing app brief and requirements
            
        Returns:
            Result dictionary with status and details
        """
        try:
            logger.info(f"Processing request for task: {request_data.get('task')}")
            
            # Step 1: Validate the request
            logger.info("Step 1: Validating request...")
            is_valid, error_msg = self.validator.validate_request(request_data)
            if not is_valid:
                logger.error(f"Request validation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Step 2: Save attachments
            logger.info("Step 2: Saving attachments...")
            attachments_dir = self._save_attachments(request_data)
            
            # Step 3: Generate the app using LLM
            logger.info("Step 3: Generating app code using LLM...")
            app_code = self.generator.generate_app(
                brief=request_data['brief'],
                checks=request_data['checks'],
                attachments=request_data.get('attachments', []),
                task_id=request_data['task']
            )
            
            if not app_code:
                return {"success": False, "error": "Failed to generate app code"}
            
            # Step 4: Deploy to GitHub Pages
            logger.info("Step 4: Deploying to GitHub Pages...")
            deployment_result = self.deployer.deploy(
                app_code=app_code,
                task_id=request_data['task'],
                round_num=request_data['round'],
                attachments_dir=attachments_dir
            )
            
            if not deployment_result['success']:
                return {"success": False, "error": deployment_result.get('error')}
            
            # Step 5: Notify evaluation API
            logger.info("Step 5: Notifying evaluation API...")
            notification_result = self.notifier.notify(
                evaluation_url=request_data['evaluation_url'],
                repo_url=deployment_result['repo_url'],
                commit_sha=deployment_result['commit_sha'],
                pages_url=deployment_result['pages_url'],
                nonce=request_data['nonce'],
                email=request_data['email'],
                task=request_data['task'],
                round_num=request_data['round']
            )
            
            if not notification_result['success']:
                logger.warning(f"Evaluation notification failed: {notification_result.get('error')}")
            
            logger.info("Request processed successfully!")
            return {
                "success": True,
                "repo_url": deployment_result['repo_url'],
                "pages_url": deployment_result['pages_url'],
                "commit_sha": deployment_result['commit_sha'],
                "notification_sent": notification_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def process_revision_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a revision request to update an existing app.
        
        Args:
            request_data: The revision request JSON
            
        Returns:
            Result dictionary with status and details
        """
        try:
            logger.info(f"Processing revision request for task: {request_data.get('task')}")
            
            # Step 1: Validate the request and secret
            logger.info("Step 1: Validating revision request and secret...")
            is_valid, error_msg = self.validator.validate_revision_request(request_data)
            if not is_valid:
                logger.error(f"Revision request validation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Step 2: Get existing repo
            repo_info = self.deployer.get_existing_repo(request_data['task'])
            if not repo_info:
                return {"success": False, "error": "Repository not found"}
            
            # Step 3: Generate updated app code
            logger.info("Step 3: Generating updated app code...")
            updated_code = self.generator.revise_app(
                brief=request_data['brief'],
                checks=request_data['checks'],
                task_id=request_data['task'],
                existing_repo=repo_info['local_path']
            )
            
            if not updated_code:
                return {"success": False, "error": "Failed to generate revised app code"}
            
            # Step 4: Update and redeploy
            logger.info("Step 4: Updating and redeploying to GitHub Pages...")
            deployment_result = self.deployer.update_and_deploy(
                app_code=updated_code,
                task_id=request_data['task'],
                round_num=request_data['round']
            )
            
            if not deployment_result['success']:
                return {"success": False, "error": deployment_result.get('error')}
            
            # Step 5: Notify evaluation API
            logger.info("Step 5: Notifying evaluation API...")
            notification_result = self.notifier.notify(
                evaluation_url=request_data['evaluation_url'],
                repo_url=deployment_result['repo_url'],
                commit_sha=deployment_result['commit_sha'],
                pages_url=deployment_result['pages_url'],
                nonce=request_data['nonce'],
                email=request_data['email'],
                task=request_data['task'],
                round_num=request_data['round']
            )
            
            logger.info("Revision request processed successfully!")
            return {
                "success": True,
                "repo_url": deployment_result['repo_url'],
                "pages_url": deployment_result['pages_url'],
                "commit_sha": deployment_result['commit_sha'],
                "notification_sent": notification_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error processing revision request: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _save_attachments(self, request_data: Dict[str, Any]) -> str:
        """Save attachments from the request to disk."""
        attachments = request_data.get('attachments', [])
        if not attachments:
            return None
        
        task_id = request_data['task']
        attachments_dir = Path(f"workdir/{task_id}/attachments")
        attachments_dir.mkdir(parents=True, exist_ok=True)
        
        return save_attachments(attachments, attachments_dir)


def main():
    """Main entry point for the application."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <request_file.json>")
        print("   or: python main.py --revision <revision_request.json>")
        sys.exit(1)
    
    is_revision = sys.argv[1] == "--revision"
    request_file = sys.argv[2] if is_revision else sys.argv[1]
    
    # Load request
    try:
        with open(request_file, 'r', encoding='utf-8') as f:
            # Remove comments from JSON (simple approach)
            content = f.read()
            # Remove single-line comments
            lines = []
            for line in content.split('\n'):
                # Remove // comments
                if '//' in line:
                    idx = line.index('//')
                    line = line[:idx]
                if line.strip():
                    lines.append(line)
            clean_content = '\n'.join(lines)
            request_data = json.loads(clean_content)
    except Exception as e:
        logger.error(f"Failed to load request file: {e}")
        sys.exit(1)
    
    # Process request
    orchestrator = AppBuilderOrchestrator()
    
    if is_revision:
        result = orchestrator.process_revision_request(request_data)
    else:
        result = orchestrator.process_request(request_data)
    
    # Print result
    print("\n" + "="*80)
    if result['success']:
        print("✓ SUCCESS!")
        print(f"Repository: {result.get('repo_url')}")
        print(f"Live App: {result.get('pages_url')}")
        print(f"Commit: {result.get('commit_sha')}")
        print(f"Notification Sent: {result.get('notification_sent')}")
    else:
        print("✗ FAILED!")
        print(f"Error: {result.get('error')}")
    print("="*80)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()

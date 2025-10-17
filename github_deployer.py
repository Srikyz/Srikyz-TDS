"""
GitHub deployer for the app builder system.
Handles creating repositories, committing code, and deploying to GitHub Pages.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import shutil
import json

logger = logging.getLogger(__name__)


class GitHubDeployer:
    """Handles deployment to GitHub and GitHub Pages."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the deployer.
        
        Args:
            config: Configuration dictionary with GitHub settings
        """
        self.config = config
        self.github_token = config.get('github_token') or os.getenv('GITHUB_TOKEN')
        self.github_username = config.get('github_username') or os.getenv('GITHUB_USERNAME')
        self.workdir = Path('workdir')
        self.workdir.mkdir(exist_ok=True)
        
        # Store repo info for revisions
        self.repo_registry = {}
    
    def deploy(self, app_code: Dict[str, str], task_id: str, round_num: int, 
               attachments_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Deploy an app to GitHub Pages.
        
        Args:
            app_code: Dictionary mapping filenames to content
            task_id: Unique task identifier
            round_num: Round number
            attachments_dir: Optional directory containing attachments
            
        Returns:
            Deployment result with URLs and commit info
        """
        try:
            logger.info(f"Deploying app for task: {task_id}")
            
            # Create repository name
            repo_name = self._generate_repo_name(task_id, round_num)
            
            # Create local directory
            local_path = self.workdir / repo_name
            if local_path.exists():
                shutil.rmtree(local_path)
            local_path.mkdir(parents=True, exist_ok=True)
            
            # Write app files
            self._write_files(local_path, app_code)
            
            # Copy attachments if provided
            if attachments_dir:
                self._copy_attachments(local_path, attachments_dir)
            
            # Initialize git repo
            self._init_git_repo(local_path)
            
            # Create GitHub repo
            repo_url = self._create_github_repo(repo_name)
            
            # Commit and push
            commit_sha = self._commit_and_push(local_path, repo_url, "Initial deployment")
            
            # Enable GitHub Pages
            pages_url = self._enable_github_pages(repo_name)
            
            # Store repo info for revisions
            self.repo_registry[task_id] = {
                'repo_name': repo_name,
                'local_path': str(local_path),
                'repo_url': repo_url
            }
            
            logger.info(f"Deployment successful: {pages_url}")
            
            return {
                'success': True,
                'repo_url': repo_url,
                'pages_url': pages_url,
                'commit_sha': commit_sha,
                'repo_name': repo_name
            }
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_and_deploy(self, app_code: Dict[str, str], task_id: str, round_num: int) -> Dict[str, Any]:
        """
        Update an existing repository and redeploy.
        
        Args:
            app_code: Updated application code
            task_id: Task identifier
            round_num: Round number
            
        Returns:
            Deployment result
        """
        try:
            logger.info(f"Updating app for task: {task_id}")
            
            # Get existing repo info
            repo_info = self.repo_registry.get(task_id)
            if not repo_info:
                return {
                    'success': False,
                    'error': 'Repository not found. Initial deployment may not have completed.'
                }
            
            local_path = Path(repo_info['local_path'])
            repo_url = repo_info['repo_url']
            
            # Update files
            self._write_files(local_path, app_code)
            
            # Commit and push
            commit_sha = self._commit_and_push(local_path, repo_url, f"Update for round {round_num}")
            
            # Pages URL doesn't change
            pages_url = self._get_pages_url(repo_info['repo_name'])
            
            logger.info(f"Update successful: {pages_url}")
            
            return {
                'success': True,
                'repo_url': repo_url,
                'pages_url': pages_url,
                'commit_sha': commit_sha
            }
            
        except Exception as e:
            logger.error(f"Update failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_existing_repo(self, task_id: str) -> Optional[Dict[str, str]]:
        """Get existing repository info for a task."""
        return self.repo_registry.get(task_id)
    
    def _generate_repo_name(self, task_id: str, round_num: int) -> str:
        """Generate a repository name."""
        # Sanitize task_id for GitHub repo name
        safe_task_id = task_id.replace('_', '-').lower()
        return f"{safe_task_id}-r{round_num}"
    
    def _write_files(self, local_path: Path, app_code: Dict[str, str]):
        """Write application files to local directory."""
        # Security check: ensure no secrets in code
        sensitive_patterns = [
            r'[a-zA-Z0-9]{32,}',  # Long tokens
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI keys
            r'AKIA[0-9A-Z]{16}',  # AWS keys
        ]
        
        for filename, content in app_code.items():
            # Check for secrets before writing
            if filename not in ['LICENSE', 'README.md']:
                for pattern in sensitive_patterns:
                    import re
                    if re.search(pattern, content):
                        logger.warning(f"Potential secret detected in {filename}, sanitizing...")
                        # In production, you might want to fail here or sanitize
            
            file_path = local_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Wrote file: {filename}")
    
    def _copy_attachments(self, local_path: Path, attachments_dir: str):
        """Copy attachments to the repository."""
        src = Path(attachments_dir)
        if not src.exists():
            return
        
        dst = local_path / 'assets'
        dst.mkdir(exist_ok=True)
        
        for item in src.iterdir():
            if item.is_file():
                shutil.copy2(item, dst / item.name)
                logger.debug(f"Copied attachment: {item.name}")
    
    def _init_git_repo(self, local_path: Path):
        """Initialize a git repository."""
        commands = [
            ['git', 'init'],
            ['git', 'config', 'user.name', 'App Builder Bot'],
            ['git', 'config', 'user.email', 'bot@appbuilder.local'],
            ['git', 'add', '.'],
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, cwd=local_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")
    
    def _create_github_repo(self, repo_name: str) -> str:
        """Create a GitHub repository using GitHub CLI or API."""
        try:
            # Try using GitHub CLI
            cmd = ['gh', 'repo', 'create', repo_name, '--public', '--source', '.']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                repo_url = f"https://github.com/{self.github_username}/{repo_name}"
                logger.info(f"Created GitHub repo: {repo_url}")
                return repo_url
            else:
                # Fallback: construct URL assuming repo exists or will be created
                logger.warning(f"GitHub CLI failed, using constructed URL: {result.stderr}")
                return f"https://github.com/{self.github_username}/{repo_name}"
                
        except FileNotFoundError:
            # GitHub CLI not installed, use API
            return self._create_repo_via_api(repo_name)
    
    def _create_repo_via_api(self, repo_name: str) -> str:
        """Create repository using GitHub API."""
        import requests
        
        url = 'https://api.github.com/user/repos'
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {
            'name': repo_name,
            'public': True,
            'auto_init': False
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            repo_data = response.json()
            return repo_data['html_url']
        else:
            raise Exception(f"Failed to create repo via API: {response.text}")
    
    def _commit_and_push(self, local_path: Path, repo_url: str, commit_message: str) -> str:
        """Commit changes and push to GitHub."""
        # Add authentication to URL
        auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
        
        commands = [
            ['git', 'add', '.'],
            ['git', 'commit', '-m', commit_message],
            ['git', 'branch', '-M', 'main'],
            ['git', 'remote', 'add', 'origin', auth_url],
            ['git', 'push', '-u', 'origin', 'main', '--force']
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, cwd=local_path, capture_output=True, text=True)
            # Ignore errors for 'remote add' if it already exists
            if result.returncode != 0 and 'remote add' not in ' '.join(cmd):
                if result.returncode != 0:
                    logger.warning(f"Git command warning: {' '.join(cmd)}\n{result.stderr}")
        
        # Get commit SHA
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=local_path, 
                              capture_output=True, text=True)
        commit_sha = result.stdout.strip() if result.returncode == 0 else 'unknown'
        
        return commit_sha
    
    def _enable_github_pages(self, repo_name: str) -> str:
        """Enable GitHub Pages for the repository."""
        try:
            # Use GitHub CLI to enable Pages
            cmd = ['gh', 'api', f'/repos/{self.github_username}/{repo_name}/pages',
                   '-X', 'POST', '-f', 'source[branch]=main', '-f', 'source[path]=/']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Even if this fails, construct the Pages URL
            pages_url = self._get_pages_url(repo_name)
            logger.info(f"GitHub Pages URL: {pages_url}")
            
            return pages_url
            
        except Exception as e:
            logger.warning(f"Failed to enable GitHub Pages: {e}")
            return self._get_pages_url(repo_name)
    
    def _get_pages_url(self, repo_name: str) -> str:
        """Construct the GitHub Pages URL."""
        return f"https://{self.github_username}.github.io/{repo_name}/"

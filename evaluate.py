"""
Evaluation script for submitted repositories.

For each repository in the repos table:
1. Check if repo was created after task request time
2. Check if repo has MIT LICENSE in root
3. Evaluate README.md quality with LLM
4. Evaluate code quality with LLM
5. Run Playwright checks based on task template
6. Log all results to the results table

Usage:
    python evaluate.py [--round ROUND]

Author: Evaluation System
Date: 2025-10-16
"""

import sys
import logging
import asyncio
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import re

from db import get_db
try:
    from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    async_playwright = None
    Page = None
    Browser = None
    PlaywrightTimeout = Exception
    PLAYWRIGHT_AVAILABLE = False

# LLM integration (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/evaluate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = None  # Set via environment or config


class RepositoryEvaluator:
    """Evaluates student repositories based on various checks."""
    
    def __init__(self, db):
        self.db = db
        self.openai_client = None
        
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    async def evaluate_repo(self, repo: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a single repository.
        
        Returns: List of evaluation results
        """
        email = repo['email']
        task = repo['task']
        round_num = repo['round']
        repo_url = repo['repo_url']
        commit_sha = repo['commit_sha']
        pages_url = repo['pages_url']
        
        logger.info(f"Evaluating {email} - {task} (Round {round_num})")
        
        results = []
        
        # Check 1: Verify repo creation time
        result = await self.check_repo_creation_time(repo)
        if result:
            results.append(result)
        
        # Check 2: Verify MIT LICENSE exists
        result = await self.check_mit_license(repo_url, commit_sha)
        if result:
            results.append(result)
        
        # Check 3: Evaluate README.md quality
        result = await self.evaluate_readme(repo_url, commit_sha)
        if result:
            results.append(result)
        
        # Check 4: Evaluate code quality
        result = await self.evaluate_code_quality(repo_url, commit_sha)
        if result:
            results.append(result)
        
        # Check 5: Run Playwright checks
        playwright_results = await self.run_playwright_checks(repo, pages_url)
        results.extend(playwright_results)
        
        logger.info(f"Completed evaluation for {email}: {len(results)} checks")
        return results
    
    async def check_repo_creation_time(self, repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if repository was created after the task request time."""
        try:
            # Get task from database
            task = self.db.get_task_by_nonce(repo['nonce'])
            if not task:
                return self._create_result(repo, 'repo_creation_time', 0, 'Task not found in database', '')
            
            task_time = datetime.fromisoformat(task['timestamp'].replace('Z', ''))
            repo_time = datetime.fromisoformat(repo['timestamp'].replace('Z', ''))
            
            # Get repo creation time from GitHub API
            repo_name = repo['repo_url'].split('/')[-1]
            owner = repo['repo_url'].split('/')[-2]
            
            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                repo_data = response.json()
                created_at = datetime.strptime(repo_data['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                
                if created_at > task_time:
                    return self._create_result(
                        repo, 'repo_creation_time', 1.0,
                        f'Repo created after task time (task: {task_time}, repo: {created_at})',
                        ''
                    )
                else:
                    return self._create_result(
                        repo, 'repo_creation_time', 0,
                        f'Repo created before task time (task: {task_time}, repo: {created_at})',
                        ''
                    )
            else:
                return self._create_result(
                    repo, 'repo_creation_time', 0,
                    f'Failed to fetch repo metadata: HTTP {response.status_code}',
                    ''
                )
        
        except Exception as e:
            logger.error(f"Error checking repo creation time: {str(e)}")
            return self._create_result(repo, 'repo_creation_time', 0, f'Error: {str(e)}', '')
    
    async def check_mit_license(self, repo_url: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Check if MIT LICENSE file exists in the root folder."""
        try:
            # GitHub raw content URL
            owner_repo = '/'.join(repo_url.split('/')[-2:])
            license_url = f"https://raw.githubusercontent.com/{owner_repo}/{commit_sha}/LICENSE"
            
            response = requests.get(license_url, timeout=30)
            
            if response.status_code == 200:
                content = response.text.lower()
                if 'mit license' in content or 'mit' in content:
                    return {
                        'check': 'mit_license',
                        'score': 1.0,
                        'reason': 'MIT LICENSE file found in root folder',
                        'logs': ''
                    }
                else:
                    return {
                        'check': 'mit_license',
                        'score': 0,
                        'reason': 'LICENSE file exists but is not MIT',
                        'logs': content[:200]
                    }
            else:
                return {
                    'check': 'mit_license',
                    'score': 0,
                    'reason': f'No LICENSE file found: HTTP {response.status_code}',
                    'logs': ''
                }
        
        except Exception as e:
            logger.error(f"Error checking MIT LICENSE: {str(e)}")
            return {
                'check': 'mit_license',
                'score': 0,
                'reason': f'Error: {str(e)}',
                'logs': ''
            }
    
    async def evaluate_readme(self, repo_url: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Evaluate README.md quality using LLM."""
        try:
            # Fetch README
            owner_repo = '/'.join(repo_url.split('/')[-2:])
            readme_url = f"https://raw.githubusercontent.com/{owner_repo}/{commit_sha}/README.md"
            
            response = requests.get(readme_url, timeout=30)
            
            if response.status_code != 200:
                return {
                    'check': 'readme_quality',
                    'score': 0,
                    'reason': f'README.md not found: HTTP {response.status_code}',
                    'logs': ''
                }
            
            readme_content = response.text
            
            # Basic checks without LLM
            score = 0
            reasons = []
            
            if len(readme_content) > 200:
                score += 0.2
                reasons.append('✓ Sufficient length (>200 chars)')
            else:
                reasons.append('✗ Too short')
            
            if any(heading in readme_content.lower() for heading in ['# ', '## ']):
                score += 0.2
                reasons.append('✓ Contains headings')
            else:
                reasons.append('✗ No headings')
            
            if any(section in readme_content.lower() for section in ['usage', 'setup', 'install']):
                score += 0.2
                reasons.append('✓ Has setup/usage section')
            else:
                reasons.append('✗ Missing setup/usage')
            
            if any(section in readme_content.lower() for section in ['description', 'about', 'summary']):
                score += 0.2
                reasons.append('✓ Has description')
            else:
                reasons.append('✗ No description')
            
            if 'license' in readme_content.lower():
                score += 0.2
                reasons.append('✓ Mentions license')
            else:
                reasons.append('✗ No license mention')
            
            # LLM evaluation if available
            if self.openai_client:
                try:
                    llm_score = await self._llm_evaluate_readme(readme_content)
                    score = (score + llm_score) / 2  # Average of basic and LLM scores
                    reasons.append(f'LLM score: {llm_score:.2f}')
                except Exception as e:
                    logger.warning(f"LLM evaluation failed: {str(e)}")
            
            return {
                'check': 'readme_quality',
                'score': score,
                'reason': '; '.join(reasons),
                'logs': readme_content[:500]
            }
        
        except Exception as e:
            logger.error(f"Error evaluating README: {str(e)}")
            return {
                'check': 'readme_quality',
                'score': 0,
                'reason': f'Error: {str(e)}',
                'logs': ''
            }
    
    async def evaluate_code_quality(self, repo_url: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Evaluate code quality using LLM."""
        try:
            # Fetch main code files (index.html, script.js, style.css)
            owner_repo = '/'.join(repo_url.split('/')[-2:])
            files = ['index.html', 'script.js', 'style.css']
            
            code_content = []
            for filename in files:
                url = f"https://raw.githubusercontent.com/{owner_repo}/{commit_sha}/{filename}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    code_content.append(f"// {filename}\n{response.text}")
            
            if not code_content:
                return {
                    'check': 'code_quality',
                    'score': 0,
                    'reason': 'No code files found',
                    'logs': ''
                }
            
            combined_code = '\n\n'.join(code_content)
            
            # Basic code checks
            score = 0
            reasons = []
            
            if len(combined_code) > 100:
                score += 0.2
                reasons.append('✓ Non-trivial code length')
            
            if 'function' in combined_code or 'const' in combined_code or 'let' in combined_code:
                score += 0.2
                reasons.append('✓ Contains functions/variables')
            
            if any(keyword in combined_code for keyword in ['addEventListener', 'onclick', 'querySelector']):
                score += 0.2
                reasons.append('✓ Has interactivity')
            
            if 'style' in combined_code.lower() or '.css' in combined_code:
                score += 0.2
                reasons.append('✓ Has styling')
            
            if '//' in combined_code or '/*' in combined_code:
                score += 0.2
                reasons.append('✓ Contains comments')
            
            # LLM evaluation if available
            if self.openai_client:
                try:
                    llm_score = await self._llm_evaluate_code(combined_code)
                    score = (score + llm_score) / 2
                    reasons.append(f'LLM score: {llm_score:.2f}')
                except Exception as e:
                    logger.warning(f"LLM code evaluation failed: {str(e)}")
            
            return {
                'check': 'code_quality',
                'score': score,
                'reason': '; '.join(reasons),
                'logs': combined_code[:500]
            }
        
        except Exception as e:
            logger.error(f"Error evaluating code quality: {str(e)}")
            return {
                'check': 'code_quality',
                'score': 0,
                'reason': f'Error: {str(e)}',
                'logs': ''
            }
    
    async def run_playwright_checks(self, repo: Dict[str, Any], pages_url: str) -> List[Dict[str, Any]]:
        """Run Playwright checks on the deployed page."""
        results = []
        
        try:
            # Get task checks from database
            task = self.db.get_task_by_nonce(repo['nonce'])
            if not task:
                logger.warning(f"Task not found for nonce: {repo['nonce']}")
                return []
            
            checks = json.loads(task['checks']) if isinstance(task['checks'], str) else task['checks']
            
            # Prefer Playwright if available with browsers; otherwise fall back to
            # a lightweight HTTP-based checker using requests + BeautifulSoup.
            if PLAYWRIGHT_AVAILABLE:
                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        page = await browser.new_page()

                        try:
                            await page.goto(pages_url, wait_until='networkidle', timeout=30000)

                            # Run each check
                            for check in checks:
                                result = await self._run_single_check(page, check, repo)
                                if result:
                                    results.append(result)

                        except PlaywrightTimeout:
                            results.append(self._create_result(
                                repo, 'page_load', 0,
                                f'Page failed to load: timeout',
                                ''
                            ))
                        except Exception as e:
                            results.append(self._create_result(
                                repo, 'page_load', 0,
                                f'Page failed to load: {str(e)}',
                                ''
                            ))
                        finally:
                            try:
                                await browser.close()
                            except Exception:
                                pass
                except Exception as e:
                    # Fall back if Playwright runtime isn't usable (e.g., no browsers)
                    logger.warning(f"Playwright not usable, falling back to HTTP checks: {e}")
                    results.extend(await self._http_fallback_checks(pages_url, checks, repo))
            else:
                # Playwright not installed in the environment; use HTTP fallback
                logger.info("Playwright not available; using HTTP-based fallback checks")
                results.extend(await self._http_fallback_checks(pages_url, checks, repo))
        
        except Exception as e:
            logger.error(f"Playwright error: {str(e)}")
            results.append(self._create_result(
                repo, 'playwright_error', 0,
                f'Error: {str(e)}',
                ''
            ))
        
        return results
    
    async def _run_single_check(self, page: Any, check: Dict, repo: Dict) -> Optional[Dict]:
        """Run a single Playwright check."""
        check_type = check.get('type', '')
        
        try:
            if check_type == 'element_exists':
                return await self._check_element_exists(page, check, repo)
            elif check_type == 'button_exists':
                return await self._check_button_exists(page, check, repo)
            elif check_type == 'click_interaction':
                return await self._check_click_interaction(page, check, repo)
            elif check_type == 'responsive_check':
                return await self._check_responsive(page, check, repo)
            else:
                logger.warning(f"Unknown check type: {check_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error in check {check_type}: {str(e)}")
            return self._create_result(
                repo, f'check_{check_type}', 0,
                f'Error: {str(e)}',
                ''
            )

    async def _http_fallback_checks(self, pages_url: str, checks: List[Dict], repo: Dict) -> List[Dict]:
        """Lightweight fallback: fetch the page HTML and perform non-JS checks using BeautifulSoup."""
        results: List[Dict] = []
        try:
            resp = requests.get(pages_url, timeout=20)
            if resp.status_code != 200:
                results.append(self._create_result(repo, 'page_load', 0, f'HTTP {resp.status_code}', ''))
                return results

            soup = BeautifulSoup(resp.text, 'html.parser')

            for check in checks:
                r = await self._http_run_single_check(soup, check, repo)
                if r:
                    results.append(r)

        except Exception as e:
            logger.error(f"HTTP fallback error: {e}")
            results.append(self._create_result(repo, 'http_fallback', 0, f'Error: {e}', ''))

        return results

    async def _http_run_single_check(self, soup: BeautifulSoup, check: Dict, repo: Dict) -> Optional[Dict]:
        """Run a single check against BeautifulSoup-parsed HTML. Limited to non-JS checks."""
        check_type = check.get('type', '')

        try:
            if check_type == 'element_exists':
                selector = check.get('selector', '')
                # Use simple CSS selector via soup.select
                elements = soup.select(selector)
                count = len(elements)
                min_count = check.get('min_count', 1)
                score = 1.0 if count >= min_count else 0
                return self._create_result(repo, f'element_{selector[:20]}', score, f'Found {count} elements (expected >={min_count})', '')

            elif check_type == 'button_exists':
                text_options = check.get('text', [])
                if isinstance(text_options, str):
                    text_options = [text_options]

                found = False
                for text in text_options:
                    # Find buttons or inputs with matching text
                    btns = soup.find_all(['button', 'input'])
                    for b in btns:
                        # normalize text
                        b_text = (b.get_text() or '')
                        if text.lower() in b_text.lower():
                            found = True
                            break
                    if found:
                        break

                score = 1.0 if found else 0
                reason = f'Button with text {text_options} found' if found else f'No button found with text: {text_options}'
                return self._create_result(repo, 'button_check', score, reason, '')

            elif check_type == 'responsive_check':
                # Cannot fully evaluate responsiveness without rendering; provide a conservative score
                return self._create_result(repo, 'responsive_design', 0.5, 'Responsive check skipped (HTTP fallback)', '')

            elif check_type == 'click_interaction':
                # Click interactions require JS; skip with partial score
                return self._create_result(repo, 'click_interaction', 0.5, 'Click interaction skipped (no JS in HTTP fallback)', '')

            else:
                logger.warning(f"Unknown check type in HTTP fallback: {check_type}")
                return None

        except Exception as e:
            logger.error(f"Error in HTTP check {check_type}: {str(e)}")
            return self._create_result(repo, f'http_check_{check_type}', 0, f'Error: {str(e)}', '')
    
    async def _check_element_exists(self, page: Any, check: Dict, repo: Dict) -> Dict:
        """Check if element(s) exist."""
        selector = check.get('selector', '')
        min_count = check.get('min_count', 1)
        
        try:
            elements = await page.query_selector_all(selector)
            count = len(elements)
            
            if count >= min_count:
                return self._create_result(
                    repo, f'element_{selector[:20]}', 1.0,
                    f'Found {count} elements (expected >={min_count})',
                    ''
                )
            else:
                return self._create_result(
                    repo, f'element_{selector[:20]}', 0,
                    f'Found {count} elements (expected >={min_count})',
                    ''
                )
        except Exception as e:
            return self._create_result(
                repo, f'element_{selector[:20]}', 0,
                f'Error: {str(e)}',
                ''
            )
    
    async def _check_button_exists(self, page: Any, check: Dict, repo: Dict) -> Dict:
        """Check if button with specific text exists."""
        text_options = check.get('text', [])
        if isinstance(text_options, str):
            text_options = [text_options]
        
        try:
            for text in text_options:
                element = await page.query_selector(f'button:has-text("{text}"), [type="button"]:has-text("{text}")')
                if element:
                    return self._create_result(
                        repo, f'button_{text[:20]}', 1.0,
                        f'Button with text "{text}" found',
                        ''
                    )
            
            return self._create_result(
                repo, 'button_check', 0,
                f'No button found with text: {text_options}',
                ''
            )
        except Exception as e:
            return self._create_result(
                repo, 'button_check', 0,
                f'Error: {str(e)}',
                ''
            )
    
    async def _check_click_interaction(self, page: Any, check: Dict, repo: Dict) -> Dict:
        """Check click interaction."""
        selector = check.get('selector', '')
        expected_result = check.get('result', '')
        
        try:
            element = await page.query_selector(selector)
            if not element:
                return self._create_result(
                    repo, 'click_interaction', 0,
                    f'Element not found: {selector}',
                    ''
                )
            
            # Click and wait for potential changes
            await element.click()
            await page.wait_for_timeout(500)
            
            # Check for modal/lightbox
            if 'modal' in expected_result.lower():
                modal = await page.query_selector('.modal, .lightbox, [data-lightbox], [role="dialog"]')
                if modal:
                    is_visible = await modal.is_visible()
                    if is_visible:
                        return self._create_result(
                            repo, 'click_interaction', 1.0,
                            'Modal/lightbox opened on click',
                            ''
                        )
            
            return self._create_result(
                repo, 'click_interaction', 0.5,
                'Click registered but expected result unclear',
                ''
            )
        except Exception as e:
            return self._create_result(
                repo, 'click_interaction', 0,
                f'Error: {str(e)}',
                ''
            )
    
    async def _check_responsive(self, page: Any, check: Dict, repo: Dict) -> Dict:
        """Check responsive design."""
        breakpoints = check.get('breakpoints', [768, 1024])
        
        try:
            scores = []
            for width in breakpoints:
                await page.set_viewport_size({"width": width, "height": 800})
                await page.wait_for_timeout(500)
                
                # Check if content is still visible
                body = await page.query_selector('body')
                if body:
                    box = await body.bounding_box()
                    if box and box['width'] > 0:
                        scores.append(1.0)
                    else:
                        scores.append(0)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            return self._create_result(
                repo, 'responsive_design', avg_score,
                f'Responsive at {len([s for s in scores if s > 0])}/{len(breakpoints)} breakpoints',
                ''
            )
        except Exception as e:
            return self._create_result(
                repo, 'responsive_design', 0,
                f'Error: {str(e)}',
                ''
            )
    
    async def _llm_evaluate_readme(self, readme: str) -> float:
        """Evaluate README with LLM."""
        # Placeholder - implement LLM evaluation
        return 0.8
    
    async def _llm_evaluate_code(self, code: str) -> float:
        """Evaluate code with LLM."""
        # Placeholder - implement LLM evaluation
        return 0.7
    
    def _create_result(self, repo: Dict, check: str, score: float, reason: str, logs: str) -> Dict:
        """Create a result dictionary."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'email': repo['email'],
            'task': repo['task'],
            'round': repo['round'],
            'repo_url': repo['repo_url'],
            'commit_sha': repo['commit_sha'],
            'pages_url': repo['pages_url'],
            'check': check,
            'score': score,
            'reason': reason,
            'logs': logs
        }


async def main():
    """Main evaluation loop."""
    # Parse arguments
    round_filter = None
    if len(sys.argv) > 2 and sys.argv[1] == '--round':
        round_filter = int(sys.argv[2])
    
    logger.info("=" * 60)
    logger.info("Starting Repository Evaluation")
    logger.info("=" * 60)
    
    db = get_db()
    evaluator = RepositoryEvaluator(db)
    
    # Get repos to evaluate
    if round_filter:
        repos = db.get_repos_without_results(round_filter)
        logger.info(f"Evaluating Round {round_filter} repositories")
    else:
        repos = db.get_repos_to_evaluate()
        logger.info(f"Evaluating all repositories")
    
    logger.info(f"Found {len(repos)} repositories to evaluate")
    
    evaluated = 0
    failed = 0
    
    for repo in repos:
        try:
            # Check if already evaluated
            if db.result_exists(repo['email'], repo['task'], repo['round']):
                logger.info(f"Skipping {repo['email']} - already evaluated")
                continue
            
            # Evaluate
            results = await evaluator.evaluate_repo(repo)
            
            # Save results
            for result in results:
                db.insert_result(result)
            
            evaluated += 1
            logger.info(f"✓ Evaluated {repo['email']} - {len(results)} checks")
        
        except Exception as e:
            failed += 1
            logger.error(f"✗ Failed to evaluate {repo.get('email', 'unknown')}: {str(e)}", exc_info=True)
    
    logger.info(f"\nEvaluation Summary:")
    logger.info(f"  Evaluated: {evaluated}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total: {len(repos)}")
    logger.info(f"\nResults saved to database: evaluation.db")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    asyncio.run(main())

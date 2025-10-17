"""
FastAPI server for the app builder system.
Accepts JSON POST requests to build and deploy applications.
"""

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uvicorn
import json
from pathlib import Path

from request_validator import RequestValidator
from app_generator import AppGenerator
from github_deployer import GitHubDeployer
from evaluator import EvaluationNotifier
from utils import setup_logging, save_attachments, load_config
from secret_manager import SecretManager
from db import get_db

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="App Builder API",
    description="Automated app builder and deployer for GitHub Pages",
    version="1.0.0"
)

# Load configuration
config = load_config()

# Initialize components
secret_manager = SecretManager()
request_validator = RequestValidator(secret_manager)
generator = AppGenerator(config)
deployer = GitHubDeployer(config)
notifier = EvaluationNotifier()


# Pydantic models for request validation
class Attachment(BaseModel):
    name: str
    url: str  # Data URI format


class BuildRequest(BaseModel):
    email: EmailStr
    secret: str = Field(..., min_length=8, description="Secret key for verification")
    task: str = Field(..., min_length=3, description="Unique task identifier")
    round: int = Field(..., ge=1, description="Round number (starts at 1)")
    nonce: str = Field(..., min_length=1, description="Unique nonce value")
    brief: str = Field(..., min_length=10, description="Application description")
    checks: List[str] = Field(..., min_items=1, description="Evaluation criteria")
    evaluation_url: str = Field(..., description="URL to send evaluation results")
    attachments: Optional[List[Attachment]] = Field(default=[], description="File attachments")

    @validator('evaluation_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class BuildResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


class EvaluationRequest(BaseModel):
    email: EmailStr
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str


@app.post("/api/build", response_model=BuildResponse)
async def build_app(request: BuildRequest):
    """
    Build and deploy a new application.
    
    This endpoint:
    1. Validates the secret against stored credentials
    2. Generates app code using LLM
    3. Creates a GitHub repository
    4. Deploys to GitHub Pages
    5. Notifies the evaluation API
    """
    request_id = f"{request.task}-r{request.round}"
    logger.info(f"[{request_id}] Received build request from {request.email}")
    
    try:
        # Convert Pydantic model to dict
        request_data = request.dict()
        
        # Step 1: Verify secret from Google Form
        logger.info(f"[{request_id}] Verifying secret...")
        if not secret_manager.verify_secret(request.email, request.secret):
            logger.warning(f"[{request_id}] Secret verification failed for {request.email}")
            raise HTTPException(
                status_code=401,
                detail="Secret verification failed. Ensure you're using the same secret from the Google Form."
            )
        
        # Step 2: Validate request
        logger.info(f"[{request_id}] Validating request...")
        is_valid, error_msg = request_validator.validate_request(request_data)
        if not is_valid:
            logger.error(f"[{request_id}] Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Step 3: Save attachments
        attachments_dir = None
        if request.attachments:
            logger.info(f"[{request_id}] Saving {len(request.attachments)} attachments...")
            attachments_list = [att.dict() for att in request.attachments]
            attachments_dir = save_attachments(
                attachments_list,
                Path(f"workdir/{request.task}/attachments")
            )
        
        # Step 4: Generate app using LLM
        logger.info(f"[{request_id}] Generating app code with LLM...")
        app_code = generator.generate_app(
            brief=request.brief,
            checks=request.checks,
            attachments=[att.dict() for att in request.attachments],
            task_id=request.task
        )
        
        if not app_code:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate application code"
            )
        
        # Step 5: Create repo and deploy to GitHub Pages
        logger.info(f"[{request_id}] Deploying to GitHub Pages...")
        deployment_result = deployer.deploy(
            app_code=app_code,
            task_id=request.task,
            round_num=request.round,
            attachments_dir=attachments_dir
        )
        
        if not deployment_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: {deployment_result.get('error')}"
            )
        
        # Step 6: Notify evaluation API (within 10 minutes requirement)
        logger.info(f"[{request_id}] Notifying evaluation API...")
        notification_start = datetime.utcnow()
        
        notification_result = notifier.notify(
            evaluation_url=request.evaluation_url,
            repo_url=deployment_result['repo_url'],
            commit_sha=deployment_result['commit_sha'],
            pages_url=deployment_result['pages_url'],
            nonce=request.nonce,
            email=request.email,
            task=request.task,
            round_num=request.round
        )
        
        notification_duration = (datetime.utcnow() - notification_start).total_seconds()
        logger.info(f"[{request_id}] Notification completed in {notification_duration:.2f} seconds")
        
        # Build success response
        response_data = {
            "repo_url": deployment_result['repo_url'],
            "pages_url": deployment_result['pages_url'],
            "commit_sha": deployment_result['commit_sha'],
            "notification_sent": notification_result['success'],
            "notification_attempts": notification_result.get('attempts', 1)
        }
        
        # Log warning if notification failed but continue (deployment was successful)
        if not notification_result['success']:
            logger.warning(f"[{request_id}] Notification failed but deployment succeeded")
        
        logger.info(f"[{request_id}] Build completed successfully!")
        
        return BuildResponse(
            success=True,
            message="Application built and deployed successfully",
            data=response_data,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/revise", response_model=BuildResponse)
async def revise_app(request: BuildRequest):
    """
    Revise and redeploy an existing application.
    
    This endpoint:
    1. Validates the secret
    2. Updates the existing app code
    3. Commits and pushes changes
    4. Notifies the evaluation API
    """
    request_id = f"{request.task}-r{request.round}"
    logger.info(f"[{request_id}] Received revision request from {request.email}")
    
    try:
        request_data = request.dict()
        
        # Step 1: Verify secret
        logger.info(f"[{request_id}] Verifying secret...")
        if not secret_manager.verify_secret(request.email, request.secret):
            raise HTTPException(
                status_code=401,
                detail="Secret verification failed"
            )
        
        # Step 2: Validate revision request
        logger.info(f"[{request_id}] Validating revision request...")
        is_valid, error_msg = request_validator.validate_revision_request(request_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Step 3: Get existing repo
        repo_info = deployer.get_existing_repo(request.task)
        if not repo_info:
            raise HTTPException(
                status_code=404,
                detail="Repository not found. Was the initial build completed?"
            )
        
        # Step 4: Generate revised app
        logger.info(f"[{request_id}] Generating revised app code...")
        updated_code = generator.revise_app(
            brief=request.brief,
            checks=request.checks,
            task_id=request.task,
            existing_repo=repo_info['local_path']
        )
        
        if not updated_code:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate revised code"
            )
        
        # Step 5: Update and redeploy
        logger.info(f"[{request_id}] Redeploying updated app...")
        deployment_result = deployer.update_and_deploy(
            app_code=updated_code,
            task_id=request.task,
            round_num=request.round
        )
        
        if not deployment_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Redeployment failed: {deployment_result.get('error')}"
            )
        
            # Step 6: Notify evaluation API (within 10 minutes requirement)
        logger.info(f"[{request_id}] Notifying evaluation API...")
        notification_start = datetime.utcnow()
        
        notification_result = notifier.notify(
            evaluation_url=request.evaluation_url,
            repo_url=deployment_result['repo_url'],
            commit_sha=deployment_result['commit_sha'],
            pages_url=deployment_result['pages_url'],
            nonce=request.nonce,
            email=request.email,
            task=request.task,
            round_num=request.round
        )
        
        notification_duration = (datetime.utcnow() - notification_start).total_seconds()
        logger.info(f"[{request_id}] Notification completed in {notification_duration:.2f} seconds")
        
        response_data = {
            "repo_url": deployment_result['repo_url'],
            "pages_url": deployment_result['pages_url'],
            "commit_sha": deployment_result['commit_sha'],
            "notification_sent": notification_result['success'],
            "notification_attempts": notification_result.get('attempts', 1)
        }
        
        # Log warning if notification failed but continue (deployment was successful)
        if not notification_result['success']:
            logger.warning(f"[{request_id}] Notification failed but deployment succeeded")
        
        logger.info(f"[{request_id}] Revision completed successfully!")
        
        return BuildResponse(
            success=True,
            message="Application revised and redeployed successfully",
            data=response_data,
            timestamp=datetime.utcnow().isoformat() + 'Z'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/api/evaluation")
async def evaluation_endpoint(request: EvaluationRequest):
    """
    Evaluation endpoint for students to submit their repository information.
    
    This endpoint:
    1. Validates the task/nonce combination exists in the tasks table
    2. Inserts the repo information into the repos table
    3. Returns HTTP 200 on success, HTTP 400 with reason on failure
    """
    logger.info(f"Received evaluation submission from {request.email} for task {request.task} (Round {request.round})")
    
    try:
        db = get_db()
        
        # Check if the task exists with matching email, task, round, and nonce
        task = db.get_task_by_nonce(request.nonce)
        
        if not task:
            logger.warning(f"Invalid nonce: {request.nonce}")
            raise HTTPException(
                status_code=400,
                detail="Invalid nonce. Task not found."
            )
        
        # Validate that the task matches the request
        if task['email'] != request.email:
            logger.warning(f"Email mismatch: task has {task['email']}, request has {request.email}")
            raise HTTPException(
                status_code=400,
                detail="Email does not match the task record."
            )
        
        if task['task'] != request.task:
            logger.warning(f"Task mismatch: task has {task['task']}, request has {request.task}")
            raise HTTPException(
                status_code=400,
                detail="Task ID does not match the task record."
            )
        
        if task['round'] != request.round:
            logger.warning(f"Round mismatch: task has {task['round']}, request has {request.round}")
            raise HTTPException(
                status_code=400,
                detail="Round number does not match the task record."
            )
        
        # Check if repo already exists (prevent duplicates)
        if db.repo_exists(request.email, request.task, request.round):
            logger.warning(f"Repo already submitted: {request.email} - {request.task} (Round {request.round})")
            raise HTTPException(
                status_code=400,
                detail="Repository has already been submitted for this task and round."
            )
        
        # Insert into repos table
        repo_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'email': request.email,
            'task': request.task,
            'round': request.round,
            'nonce': request.nonce,
            'repo_url': request.repo_url,
            'commit_sha': request.commit_sha,
            'pages_url': request.pages_url
        }
        
        repo_id = db.insert_repo(repo_data)
        
        logger.info(f"✓ Repo submission recorded: ID {repo_id} for {request.email}")
        
        return {
            "success": True,
            "message": "Repository submission recorded successfully",
            "repo_id": repo_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing evaluation submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "service": "app-builder-api"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "App Builder API",
        "version": "1.0.0",
        "endpoints": {
            "build": "/api/build",
            "revise": "/api/revise",
            "evaluation": "/api/evaluation",
            "health": "/health"
        },
        "documentation": "/docs"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    )


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    logger.info(f"Starting App Builder API on {host}:{port}")
    uvicorn.run("api_server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    start_server(port=port, reload=True)

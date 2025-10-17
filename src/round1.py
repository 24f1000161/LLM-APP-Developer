# Round 1: Build and deploy the initial application
import os
import json
import base64
import requests
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
from src.create_repo import create_github_repo
from src.push_llm_code import generate_app_with_llm, push_code_to_repo
from src.enable_github_pages import enable_github_pages

logger = logging.getLogger(__name__)


def wait_for_pages_deployment(pages_url: str, max_wait: int = 180) -> bool:
    """
    Poll GitHub Pages URL until it returns 200 OK or timeout.
    
    GitHub Pages can take 30-120 seconds to deploy after enabling.
    This ensures the page is accessible before notifying evaluation server.
    
    Args:
        pages_url: GitHub Pages URL to check
        max_wait: Maximum seconds to wait (default: 180)
    
    Returns:
        bool: True if page is accessible, False if timeout
    """
    logger.info(f"Waiting for GitHub Pages deployment: {pages_url}")
    start = time.time()
    attempt = 0
    
    while time.time() - start < max_wait:
        attempt += 1
        try:
            response = requests.get(pages_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                elapsed = int(time.time() - start)
                logger.info(f"✓ Pages deployed successfully after {elapsed}s (attempt {attempt})")
                return True
            else:
                logger.debug(f"Pages returned {response.status_code} (attempt {attempt})")
        except Exception as e:
            logger.debug(f"Pages check failed (attempt {attempt}): {str(e)}")
        
        # Wait 10 seconds between checks
        time.sleep(10)
    
    elapsed = int(time.time() - start)
    logger.error(f"✗ Pages not reachable after {elapsed}s ({attempt} attempts)")
    return False


async def round1(request_data: dict) -> None:
    """
    Handle round 1 requests in background (no return value).
    
    Steps:
    1. Generate app code using LLM
    2. Create GitHub repo
    3. Push code to repo
    4. Enable GitHub Pages
    5. Wait for Pages to be accessible
    6. POST notification to evaluation API
    
    Results are sent via POST to evaluation_url, not returned.
    """
    request_start_time = datetime.now()
    
    try:
        email = request_data.get("email")
        secret = request_data.get("secret")
        task = request_data.get("task")
        round_num = request_data.get("round")
        nonce = request_data.get("nonce")
        brief = request_data.get("brief")
        checks = request_data.get("checks", [])
        evaluation_url = request_data.get("evaluation_url")
        attachments = request_data.get("attachments", [])
        
        logger.info(f"Processing request for {email}, task: {task}")
        
        # Create a temporary working directory for this task
        work_dir = Path(f"/tmp/llm-app-{task}")
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Download attachments
        attachment_files = {}
        for attachment in attachments:
            name = attachment.get("name")
            url = attachment.get("url")
            if url.startswith("data:"):
                # Decode base64 data URI
                attachment_files[name] = _decode_data_uri(url)
            else:
                # Download from URL
                response = requests.get(url)
                attachment_files[name] = response.content
        
        # Generate app code using LLM (async)
        app_code = await generate_app_with_llm(brief, checks, attachment_files)
        
        # Create GitHub repo using same derivation logic as Round 2
        from src.utils import derive_repo_name_from_task
        repo_name = derive_repo_name_from_task(task)
        logger.info(f"Round 1: Derived repo name '{repo_name}' from task '{task}'")
        repo_url, clone_url = create_github_repo(repo_name, email)
        
        # Push code to repository
        commit_sha = push_code_to_repo(clone_url, app_code, attachment_files, task)
        
        # Enable GitHub Pages
        github_token = os.getenv("GITHUB_TOKEN")
        owner = repo_url.split("/")[-2]
        repo = repo_url.split("/")[-1]
        pages_url = enable_github_pages(owner, repo, github_token)
        
        # Wait for Pages deployment to be accessible (max 2 minutes to stay within 10-min deadline)
        # LLM generation: ~60s, Repo creation: ~10s, Pages wait: ~120s, Notification: ~5s = ~195s total
        if not wait_for_pages_deployment(pages_url, max_wait=120):
            logger.warning(f"Pages not reachable after 120s, notifying anyway: {pages_url}")
        
        # Check deadline (10 minutes)
        elapsed_seconds = (datetime.now() - request_start_time).total_seconds()
        if elapsed_seconds > 600:
            logger.error(f"⚠️  DEADLINE EXCEEDED: {elapsed_seconds:.1f}s > 600s for {email}")
        else:
            logger.info(f"✓ Completed within deadline: {elapsed_seconds:.1f}s for {email}")
        
        # Notify the evaluation API
        notification = {
            "email": email,
            "task": task,
            "round": round_num,
            "nonce": nonce,
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url,
        }
        
        # Try to notify evaluation API with exponential backoff retries (1s, 2s, 4s, 8s)
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    evaluation_url,
                    json=notification,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Evaluation API notified successfully")
                    break
                else:
                    logger.warning(f"Evaluation API returned {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Evaluation API timeout (attempt {attempt + 1}/{max_retries})")
                
            except Exception as e:
                logger.error(f"Error notifying evaluation API: {str(e)}")
            
            # Exponential backoff: 1s, 2s, 4s, 8s (per spec)
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                logger.info(f"Retrying after {delay}s delay...")
                time.sleep(delay)
        else:
            logger.error("Failed to notify evaluation API after all retries")
        
        # Background task complete - no return value
        logger.info(f"Round 1 completed for {email}: {repo_url}")
        
    except Exception as e:
        logger.error(f"Round 1 failed for {email}: {str(e)}", exc_info=True)
        
        # Try to notify evaluation server of failure
        try:
            error_notification = {
                "email": request_data.get("email"),
                "task": request_data.get("task"),
                "round": request_data.get("round"),
                "nonce": request_data.get("nonce"),
                "status": "error",
                "error": str(e),
            }
            
            requests.post(
                request_data.get("evaluation_url"),
                json=error_notification,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            logger.info("Notified evaluation server of error")
        except Exception as notify_error:
            logger.error(f"Failed to notify evaluation server of error: {str(notify_error)}")


def _decode_data_uri(data_uri: str) -> bytes:
    """Decode a base64 data URI and return the binary content."""
    try:
        # Format: data:mime/type;base64,<content>
        _, content = data_uri.split(",", 1)
        return base64.b64decode(content)
    except Exception as e:
        logger.error(f"Error decoding data URI: {e}")
        return b""
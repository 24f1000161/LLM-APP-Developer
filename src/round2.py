# Round 2: Revise and update the application
import os
import json
import base64
import requests
import logging
from pathlib import Path
from src.push_llm_code import generate_app_with_llm, push_code_to_repo
from src.create_repo import clone_existing_repo

logger = logging.getLogger(__name__)


async def round2(request_data: dict) -> dict:
    """
    Handle round 2 requests:
    1. Validate the request
    2. Generate updated app code based on revisions
    3. Update the existing GitHub repo
    4. Push code changes to repo
    5. Notify the evaluation API
    """
    try:
        email = request_data.get("email")
        secret = request_data.get("secret")
        task = request_data.get("task")
        round_num = request_data.get("round")
        nonce = request_data.get("nonce")
        brief = request_data.get("brief")  # Revised brief
        checks = request_data.get("checks", [])
        evaluation_url = request_data.get("evaluation_url")
        attachments = request_data.get("attachments", [])
        repo_url = request_data.get("repo_url")  # From round 1 submission
        
        logger.info(f"Processing revision request for {email}, task: {task}")
        
        # Create a temporary working directory for this task
        work_dir = Path(f"/tmp/llm-app-{task}-r2")
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
        
        # Clone the existing repo
        clone_dir = clone_existing_repo(repo_url, task)
        
        # Generate updated app code using LLM (with context of previous round) (async)
        app_code = await generate_app_with_llm(
            brief,
            checks,
            attachment_files,
            existing_repo_path=clone_dir,
            is_revision=True
        )
        
        # Push updated code to repository
        commit_sha = push_code_to_repo(repo_url, app_code, attachment_files, task, is_update=True)
        
        # Get pages URL (should already exist from round 1)
        owner = repo_url.split("/")[-2]
        repo = repo_url.split("/")[-1]
        pages_url = f"https://{owner}.github.io/{repo}/"
        
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
        
        # Try to notify evaluation API with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    evaluation_url,
                    json=notification,
                    headers={"Content-Type": "application/json"},
                    timeout=30,  # Increased from 10 to 30 seconds
                )
                
                if response.status_code != 200:
                    logger.warning(f"Evaluation API returned {response.status_code}")
                else:
                    logger.info(f"Successfully notified evaluation API")
                    break
            except requests.exceptions.Timeout:
                logger.warning(f"Evaluation API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error("Failed to notify evaluation API after all retries")
                    # Don't fail the entire request just because notification failed
                    # The repo and pages were created successfully
            except Exception as e:
                logger.error(f"Error notifying evaluation API: {str(e)}")
                break
        
        # Return success even if notification failed - the important work is done
        return {
            "status": "success",
            "message": "Repository updated and redeployed successfully",
            "repo_url": repo_url,
            "pages_url": pages_url,
            "commit_sha": commit_sha,
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


def _decode_data_uri(data_uri: str) -> bytes:
    """Decode a base64 data URI and return the binary content."""
    try:
        # Format: data:mime/type;base64,<content>
        _, content = data_uri.split(",", 1)
        return base64.b64decode(content)
    except Exception as e:
        logger.error(f"Error decoding data URI: {e}")
        return b""

# Round 1: Build and deploy the initial application
import os
import json
import base64
import requests
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from src.create_repo import create_github_repo
from src.push_llm_code import generate_app_with_llm, push_code_to_repo
from src.enable_github_pages import enable_github_pages

logger = logging.getLogger(__name__)


async def round1(request_data: dict) -> dict:
    """
    Handle round 1 requests:
    1. Validate the request
    2. Generate app code using LLM
    3. Create GitHub repo
    4. Push code to repo
    5. Enable GitHub Pages
    6. Notify the evaluation API
    """
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
        
        # Create GitHub repo
        repo_name = f"{task[:20]}"  # Use first 20 chars of task as repo name
        repo_url, clone_url = create_github_repo(repo_name, email)
        
        # Push code to repository
        commit_sha = push_code_to_repo(clone_url, app_code, attachment_files, task)
        
        # Enable GitHub Pages
        github_token = os.getenv("GITHUB_TOKEN")
        owner = repo_url.split("/")[-2]
        repo = repo_url.split("/")[-1]
        pages_url = enable_github_pages(owner, repo, github_token)
        
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
        
        response = requests.post(
            evaluation_url,
            json=notification,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        
        if response.status_code != 200:
            logger.warning(f"Evaluation API returned {response.status_code}")
            return {"status": "error", "message": "Evaluation API notification failed"}
        
        return {
            "status": "success",
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
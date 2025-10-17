# Create and manage GitHub repositories
import os
import requests
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_github_repo(repo_name: str, email: str) -> tuple:
    """
    Create a new GitHub repository using the GitHub API.
    
    Args:
        repo_name: Name for the new repository
        email: Student email (for reference/documentation)
    
    Returns:
        tuple: (repo_url, clone_url)
    """
    github_token = os.getenv("GITHUB_TOKEN")
    github_user = os.getenv("GITHUB_USER")
    
    if not github_token or not github_user:
        raise ValueError("GITHUB_TOKEN and GITHUB_USER environment variables are required")
    
    # Ensure repo name is lowercase and contains only alphanumeric and hyphens
    repo_name = repo_name.lower().replace("_", "-")
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    payload = {
        "name": repo_name,
        "description": f"Auto-generated app for {email}",
        "public": True,
        "auto_init": True,  # Initialize with README
    }
    
    response = requests.post(
        "https://api.github.com/user/repos",
        json=payload,
        headers=headers,
        timeout=10,
    )
    
    # If repo already exists, fetch its details instead
    if response.status_code == 422:
        response_data = response.json()
        if "errors" in response_data and any(
            err.get("message") == "name already exists on this account"
            for err in response_data["errors"]
        ):
            logger.warning(f"Repository {repo_name} already exists, fetching details...")
            
            # Get existing repo details
            get_response = requests.get(
                f"https://api.github.com/repos/{github_user}/{repo_name}",
                headers=headers,
                timeout=10,
            )
            
            if get_response.status_code == 200:
                repo_data = get_response.json()
                repo_url = repo_data["html_url"]
                clone_url = repo_data["clone_url"]
                logger.info(f"Using existing repository: {repo_url}")
                return repo_url, clone_url
            else:
                raise Exception(f"Repo exists but could not fetch details: {get_response.status_code}")
        else:
            raise Exception(f"Failed to create repo: {response.status_code} - {response.text}")
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create repo: {response.status_code} - {response.text}")
    
    repo_data = response.json()
    repo_url = repo_data["html_url"]
    clone_url = repo_data["clone_url"]
    
    logger.info(f"Created repository: {repo_url}")
    return repo_url, clone_url


def clone_existing_repo(repo_url: str, task_id: str) -> Path:
    """
    Clone an existing GitHub repository locally for updates.
    
    Args:
        repo_url: Full URL to the GitHub repository
        task_id: Task identifier for naming the local directory
    
    Returns:
        Path: Local directory path where the repo was cloned
    """
    github_token = os.getenv("GITHUB_TOKEN")
    
    # Create clone URL with token for authentication
    if "https://" in repo_url:
        clone_url = repo_url.replace(
            "https://",
            f"https://{github_token}@"
        )
    else:
        raise ValueError("Only HTTPS repo URLs are supported")
    
    # Clone directory
    clone_dir = Path(f"/tmp/repo-{task_id}")
    if clone_dir.exists():
        import shutil
        shutil.rmtree(clone_dir)
    
    clone_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        subprocess.run(
            ["git", "clone", clone_url, str(clone_dir)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        logger.info(f"Cloned repository to {clone_dir}")
        return clone_dir
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to clone repo: {e.stderr.decode()}")


def setup_git_config(repo_path: Path, email: str) -> None:
    """
    Configure git settings in a repository.
    
    Args:
        repo_path: Path to the repository
        email: Email for git commits
    """
    try:
        subprocess.run(
            ["git", "config", "user.email", email],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "LLM App Builder"],
            cwd=str(repo_path),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to configure git: {e.stderr.decode()}")


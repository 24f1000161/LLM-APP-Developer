# Enable GitHub Pages for a repository
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def enable_github_pages(
    owner: str,
    repo: str,
    github_token: str,
    branch: str = "main",
    path: str = "/",
) -> str:
    """
    Enable GitHub Pages for a repository and set it to deploy from the main branch.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        github_token: GitHub personal access token
        branch: Branch to deploy from (default: main)
        path: Path to deploy from (default: / for root)
    
    Returns:
        str: GitHub Pages URL
    """
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    # Update repository settings to enable Pages
    url = f"https://api.github.com/repos/{owner}/{repo}/pages"
    
    payload = {
        "source": {
            "branch": branch,
            "path": path,
        }
    }
    
    # First, check if Pages is already configured
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 404:
        # Pages not yet enabled, create it
        response = requests.post(url, json=payload, headers=headers, timeout=10)
    elif response.status_code == 200:
        # Pages already exists, update it
        response = requests.put(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code not in [200, 201]:
        raise Exception(
            f"Failed to enable GitHub Pages: {response.status_code} - {response.text}"
        )
    
    pages_data = response.json()
    pages_url = pages_data.get("html_url")
    
    if not pages_url:
        # Construct the URL manually if not returned
        pages_url = f"https://{owner}.github.io/{repo}/"
    
    logger.info(f"GitHub Pages enabled at: {pages_url}")
    return pages_url

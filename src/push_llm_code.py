# Generate code with LLM and push to GitHub
import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

logger = logging.getLogger(__name__)


def generate_app_with_llm(
    brief: str,
    checks: list,
    attachments: Dict[str, bytes],
    existing_repo_path: Optional[Path] = None,
    is_revision: bool = False,
) -> Dict[str, str]:
    """
    Use Pydantic AI with OpenAI (primary) or Gemini (fallback) to generate code.
    
    Args:
        brief: Task brief describing what to build
        checks: List of checks/requirements
        attachments: Dict of attachment names to content
        existing_repo_path: Path to existing repo for revisions
        is_revision: Whether this is a Round 2 revision
    
    Returns:
        dict: Generated files {filename: content}
    """
    
    # Try OpenAI first
    try:
        logger.info("Attempting to generate code with OpenAI GPT-5-nano...")
        files = _generate_with_openai(brief, checks, attachments, is_revision)
        logger.info("Successfully generated code with OpenAI")
        return files
    except Exception as e:
        logger.warning(f"OpenAI generation failed: {str(e)}. Attempting fallback to Gemini...")
    
    # Fallback to Gemini
    try:
        logger.info("Attempting to generate code with Gemini...")
        files = _generate_with_gemini(brief, checks, attachments, is_revision)
        logger.info("Successfully generated code with Gemini (fallback)")
        return files
    except Exception as e:
        logger.error(f"Both OpenAI and Gemini generation failed: {str(e)}")
        raise Exception(f"Code generation failed with both providers: {str(e)}")


def _generate_with_openai(
    brief: str,
    checks: list,
    attachments: Dict[str, bytes],
    is_revision: bool,
) -> Dict[str, str]:
    """Generate code using OpenAI GPT-5-nano."""
    from pydantic_ai.models.openai import OpenAIModel
    
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Initialize the model
    model = OpenAIModel(
        model_name="gpt-5-nano",
        api_key=api_key
    )
    
    # Create an agent for code generation
    agent = Agent(
        model=model,
        system_prompt=_get_system_prompt(is_revision),
    )
    
    # Build the user prompt
    prompt = _build_user_prompt(brief, checks, attachments, is_revision)
    
    # Call the agent
    result = agent.run_sync(prompt)
    response_text = result.data
    
    # Parse the response to extract generated files
    files = _parse_llm_response(response_text)
    
    return files


def _generate_with_gemini(
    brief: str,
    checks: list,
    attachments: Dict[str, bytes],
    is_revision: bool,
) -> Dict[str, str]:
    """Generate code using Google Gemini as fallback."""
    from pydantic_ai.models.gemini import GeminiModel
    
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")
    
    # Initialize the model
    model = GeminiModel(
        model_name="gemini-2.0-flash",
        api_key=api_key
    )
    
    # Create an agent for code generation
    agent = Agent(
        model=model,
        system_prompt=_get_system_prompt(is_revision),
    )
    
    # Build the user prompt
    prompt = _build_user_prompt(brief, checks, attachments, is_revision)
    
    # Call the agent
    result = agent.run_sync(prompt)
    response_text = result.data
    
    # Parse the response to extract generated files
    files = _parse_llm_response(response_text)
    
    return files


def _get_system_prompt(is_revision: bool = False) -> str:
    """Get the system prompt for the code generation agent."""
    if is_revision:
        return """You are an expert web developer specializing in revising and improving web applications.
Your task is to take existing application requirements and generate updated HTML, CSS, and JavaScript code.

IMPORTANT REQUIREMENTS:
1. Always generate code in the exact XML format specified
2. Keep existing functionality and enhance it
3. Ensure code is minimal, clean, and well-commented
4. Use Bootstrap 5 from CDN for professional styling
5. Include proper error handling and user feedback
6. Write a comprehensive README.md file
7. Include a complete MIT LICENSE

OUTPUT FORMAT:
Return your response EXACTLY in this format with no additional text:

<FILE name="index.html">
[HTML content here]
</FILE>

<FILE name="style.css">
[CSS content here]
</FILE>

<FILE name="script.js">
[JavaScript content here]
</FILE>

<FILE name="README.md">
[Markdown content here]
</FILE>

<FILE name="LICENSE">
[MIT License text]
</FILE>"""
    else:
        return """You are an expert full-stack web developer specializing in building single-page applications.
Your task is to generate complete, production-ready HTML, CSS, and JavaScript code based on requirements.

IMPORTANT REQUIREMENTS:
1. Always generate code in the exact XML format specified
2. Create minimal but fully functional applications
3. Use professional design with Bootstrap 5 from CDN
4. Include comprehensive error handling
5. Write clean, well-commented code
6. Generate a professional README.md file
7. Include a complete MIT LICENSE

OUTPUT FORMAT:
Return your response EXACTLY in this format with no additional text:

<FILE name="index.html">
[HTML content here]
</FILE>

<FILE name="style.css">
[CSS content here]
</FILE>

<FILE name="script.js">
[JavaScript content here]
</FILE>

<FILE name="README.md">
[Markdown content with: Overview, Setup, Usage, Features, License]
</FILE>

<FILE name="LICENSE">
[MIT License text]
</FILE>"""


def _build_user_prompt(
    brief: str,
    checks: list,
    attachments: Dict[str, bytes],
    is_revision: bool = False,
) -> str:
    """Build the user prompt for the agent."""
    
    checks_str = "\n".join([f"  • {check}" for check in checks])
    
    attachment_info = ""
    if attachments:
        attachment_names = ", ".join(attachments.keys())
        attachment_info = f"\n\nAttachments provided: {attachment_names}"
    
    if is_revision:
        return f"""Please revise and enhance the web application based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_str}
{attachment_info}

Update the code to meet all requirements while maintaining existing functionality.
Generate updated index.html, style.css, script.js, README.md, and LICENSE files.
Return ONLY the XML formatted response as specified."""
    else:
        return f"""Please create a new web application based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_str}
{attachment_info}

Generate a complete, production-ready single-page application that meets ALL requirements.
Create index.html, style.css, script.js, README.md, and LICENSE files.
Return ONLY the XML formatted response as specified."""


def _parse_llm_response(response_text: str) -> Dict[str, str]:
    """Extract files from LLM response."""
    files = {}
    
    # Parse <FILE name="..."> blocks
    import re
    pattern = r'<FILE name="([^"]+)">\n(.*?)\n</FILE>'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    for filename, content in matches:
        files[filename] = content.strip()
    
    # If no files found using the above pattern, try a simpler extraction
    if not files:
        lines = response_text.split('\n')
        current_file = None
        current_content = []
        
        for line in lines:
            if line.startswith('<FILE name="'):
                if current_file:
                    files[current_file] = '\n'.join(current_content).strip()
                    current_content = []
                match = re.search(r'<FILE name="([^"]+)">', line)
                if match:
                    current_file = match.group(1)
            elif line.startswith('</FILE>'):
                if current_file:
                    files[current_file] = '\n'.join(current_content).strip()
                    current_file = None
                    current_content = []
            elif current_file:
                current_content.append(line)
    
    return files


def push_code_to_repo(
    repo_url: str,
    generated_files: Dict[str, str],
    attachments: Dict[str, bytes],
    task_id: str,
    is_update: bool = False,
) -> str:
    """
    Push generated code and attachments to GitHub repository.
    
    Args:
        repo_url: GitHub repository URL or clone URL
        generated_files: Dict of filenames to content
        attachments: Dict of attachment names to content
        task_id: Task identifier
        is_update: Whether this is an update (Round 2)
    
    Returns:
        str: Commit SHA
    """
    from src.create_repo import setup_git_config, clone_existing_repo
    
    # Clone or get repo directory
    if is_update:
        repo_dir = clone_existing_repo(repo_url, f"{task_id}-update")
    else:
        repo_dir = Path(f"/tmp/repo-{task_id}")
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize repo
        subprocess.run(
            ["git", "init"],
            cwd=str(repo_dir),
            check=True,
            capture_output=True,
        )
        
        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=str(repo_dir),
            check=True,
            capture_output=True,
        )
    
    # Setup git config
    setup_git_config(repo_dir, "builder@llm-app.local")
    
    # Write generated files
    for filename, content in generated_files.items():
        file_path = repo_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, str):
            file_path.write_text(content, encoding='utf-8')
        else:
            file_path.write_bytes(content)
    
    # Write attachment files
    for filename, content in attachments.items():
        file_path = repo_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(str(content), encoding='utf-8')
    
    # Add all files
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
    )
    
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    if result.returncode == 0:
        # No changes
        logger.info("No changes to commit")
        # Get the current HEAD SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    
    # Commit changes
    commit_msg = "Auto-generated code" if not is_update else "Revised code"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
    )
    
    # Push to remote
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=str(repo_dir),
        check=True,
        capture_output=True,
        timeout=30,
    )
    
    # Get commit SHA
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    
    commit_sha = result.stdout.strip()
    logger.info(f"Pushed code to {repo_url} with commit {commit_sha}")
    
    return commit_sha

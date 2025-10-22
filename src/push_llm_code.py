# Generate code with LLM and push to GitHub
import os
import json
import subprocess
import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

logger = logging.getLogger(__name__)


async def generate_app_with_llm(
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
        logger.info("Attempting to generate code with OpenAI GPT-5-mini...")
        files = await _generate_with_openai(brief, checks, attachments, is_revision)
        logger.info("Successfully generated code with OpenAI")
        return files
    except Exception as e:
        logger.warning(f"OpenAI generation failed: {str(e)}. Attempting fallback to Gemini...")
    
    # Fallback to Gemini
    try:
        logger.info("Attempting to generate code with Gemini...")
        files = await _generate_with_gemini(brief, checks, attachments, is_revision)
        logger.info("Successfully generated code with Gemini (fallback)")
        return files
    except Exception as e:
        logger.error(f"Both OpenAI and Gemini generation failed: {str(e)}")
        raise Exception(f"Code generation failed with both providers: {str(e)}")


async def _generate_with_openai(
    brief: str,
    checks: list,
    attachments: Dict[str, bytes],
    is_revision: bool,
) -> Dict[str, str]:
    """Generate code using OpenAI GPT-5-mini."""
    from pydantic_ai.models.openai import OpenAIModel
    
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # pydantic-ai uses OPENAI_API_KEY from environment
    # Initialize the model without api_key parameter
    model = OpenAIModel(
        model_name="gpt-5-mini"
    )
    
    # Create an agent for code generation
    agent = Agent(
        model=model,
        system_prompt=_get_system_prompt(is_revision),
    )
    
    # Build the user prompt
    prompt = _build_user_prompt(brief, checks, attachments, is_revision)
    
    # Call the agent asynchronously
    result = await agent.run(prompt)
    # Access the response text - try different attributes
    if hasattr(result, 'data'):
        response_text = str(result.data)
    elif hasattr(result, 'output'):
        response_text = str(result.output)
    elif hasattr(result, 'content'):
        response_text = str(result.content)
    else:
        # Fallback: convert entire result to string
        response_text = str(result)
    
    # Parse the response to extract generated files
    files = _parse_llm_response(response_text)
    
    return files


async def _generate_with_gemini(
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
    
    # pydantic-ai uses GEMINI_API_KEY from environment
    # Initialize the model without api_key parameter
    model = GeminiModel(
        model_name="gemini-2.5-flash"
    )
    
    # Create an agent for code generation
    agent = Agent(
        model=model,
        system_prompt=_get_system_prompt(is_revision),
    )
    
    # Build the user prompt
    prompt = _build_user_prompt(brief, checks, attachments, is_revision)
    
    # Call the agent asynchronously
    result = await agent.run(prompt)
    # Access the response text - try different attributes
    if hasattr(result, 'data'):
        response_text = str(result.data)
    elif hasattr(result, 'output'):
        response_text = str(result.output)
    elif hasattr(result, 'content'):
        response_text = str(result.content)
    else:
        # Fallback: convert entire result to string
        response_text = str(result)
    
    # Parse the response to extract generated files
    files = _parse_llm_response(response_text)
    
    return files


def _get_system_prompt(is_revision: bool = False) -> str:
    """Get the system prompt for the code generation agent."""
    if is_revision:
        return """You are an expert developer specializing in revising and improving web applications.
Your task is to take existing application requirements and generate updated files for a GitHub Pages website.

CRITICAL OUTPUT REQUIREMENTS:
1. Generate ALL files specified in the brief or requirements
2. ALWAYS include README.md and LICENSE files
3. Each file MUST be wrapped in <FILE name="filename"></FILE> tags
4. ALWAYS close every <FILE> tag properly with </FILE>
5. Put each file's content between the opening and closing tags
6. Do NOT include any text outside the FILE tags
7. Update the README.md to reflect ALL changes made in this revision
8. Keep the existing MIT LICENSE unchanged

GITHUB PAGES REQUIREMENTS:
- Ensure index.html exists at the root for GitHub Pages to serve it
- All assets must use relative paths that work in the GitHub Pages URL structure (username.github.io/repo-name/)
- Include proper meta tags and viewport settings for web display
- Preserve any attachments exactly as provided

CODE REQUIREMENTS:
- Maintain existing functionality and enhance it
- For web applications, use Bootstrap 5 from CDN for professional styling
- Include proper error handling and user feedback
- Write clean, well-commented code
- Generate EXACTLY the file types specified in the brief (txt, json, svg, html, md, etc.)
- Ensure content types (json, svg, etc.) use correct syntax and are valid

README REQUIREMENTS FOR REVISIONS:
- Document all files created and their purpose
- Update the usage section with new functionality
- Include a link to the published GitHub Pages site
- Keep professional structure: Overview, Files, Setup, Usage, License

OUTPUT FORMAT (FOLLOW EXACTLY):
<FILE name="filename.ext">
[Complete file content]
</FILE>

<FILE name="README.md">
# [App Title]

## Overview
[Brief description and what's new in this revision]

## Files
- [List and describe all files]

## Setup
This project is hosted on GitHub Pages at `https://[username].github.io/[repo-name]/`

## Usage
[How to use the app]

## License
MIT License - see LICENSE file for details.
</FILE>

<FILE name="LICENSE">
MIT License

Copyright (c) 2025 LLM App Developer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</FILE>"""
    else:
        return """You are an expert developer specializing in building web content and applications.
Your task is to generate complete, production-ready files for a GitHub Pages website.

CRITICAL OUTPUT REQUIREMENTS:
1. Generate ALL files specified in the brief or requirements
2. ALWAYS include README.md and LICENSE files
3. Each file MUST be wrapped in <FILE name="filename"></FILE> tags
4. ALWAYS close every <FILE> tag properly with </FILE>
5. Put each file's content between the opening and closing tags
6. Do NOT include any text outside the FILE tags
7. Generate EXACTLY the file types specified in the brief (txt, json, svg, html, md, etc.)
8. Preserve any attachments exactly as provided without modification

GITHUB PAGES REQUIREMENTS:
- Ensure index.html exists at the root level for GitHub Pages to serve it properly
- All assets must use relative paths that work in GitHub Pages URL structure
- Include proper meta tags and viewport settings for responsive web display
- For SVG files, ensure they are valid and well-formed
- For JSON files, ensure they are valid and properly formatted

CODE REQUIREMENTS:
- Create fully functional content that meets all requirements
- For web applications, use Bootstrap 5 from CDN for professional styling
- Write clean, well-commented code
- Follow best practices for each file type

README REQUIREMENTS:
- Professional and comprehensive
- Document all files created and their purpose
- Include GitHub Pages deployment information
- Follow the exact structure provided below

OUTPUT FORMAT (FOLLOW EXACTLY):
<FILE name="filename.ext">
[Complete file content]
</FILE>

<FILE name="README.md">
# [Project Title]

## Overview
[Brief description of what the project does]

## Files
- [filename.ext]: [Brief description]
- [filename2.ext]: [Brief description]
- [List all generated files with descriptions]

## Setup
This project is published on GitHub Pages and can be accessed at `https://[username].github.io/[repo-name]/`

## Usage
[Step-by-step usage instructions]

## License
MIT License - see LICENSE file for details.
</FILE>

<FILE name="LICENSE">
MIT License

Copyright (c) 2025 LLM App Developer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
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
        return f"""Please revise and enhance the content based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_str}
{attachment_info}

Update all files to meet all requirements while maintaining existing functionality.
Generate EXACTLY the file types specified in the brief.
Return ONLY the XML formatted response as specified."""
    else:
        return f"""Please create content based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_str}
{attachment_info}

Generate complete, production-ready content that meets ALL requirements.
Create EXACTLY the file types specified in the brief.
Return ONLY the XML formatted response as specified."""
    
def _parse_llm_response(response_text: str) -> Dict[str, str]:
    """Extract files from LLM response."""
    files = {}
    import re
    
    # More flexible pattern that handles various edge cases
    # Try multiple parsing strategies
    
    # Strategy 1: Standard XML-style tags with closing tags
    pattern = r'<FILE name="([^"]+)"[^>]*>(.*?)</FILE>'
    matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    for filename, content in matches:
        # Clean up content - remove leading/trailing whitespace and newlines
        cleaned = content.strip()
        if cleaned:
            files[filename] = cleaned
            logger.info(f"Parsed file: {filename} ({len(cleaned)} chars)")
    
    # Strategy 2: If no files found, try parsing without closing tags
    # (LLM might not properly close tags)
    if not files:
        logger.warning("Standard parsing failed, trying alternative parsing...")
        lines = response_text.split('\n')
        current_file = None
        current_content = []
        
        for i, line in enumerate(lines):
            # Check for opening tag
            if '<FILE name="' in line or '<file name="' in line:
                # Save previous file if exists
                if current_file and current_content:
                    content = '\n'.join(current_content).strip()
                    if content:
                        files[current_file] = content
                        logger.info(f"Parsed file (alt): {current_file} ({len(content)} chars)")
                    current_content = []
                
                # Extract filename
                match = re.search(r'<FILE name="([^"]+)"[^>]*>', line, re.IGNORECASE)
                if match:
                    current_file = match.group(1)
                    # If there's content after the tag on the same line, include it
                    rest_of_line = line[match.end():].strip()
                    if rest_of_line and not rest_of_line.startswith('<'):
                        current_content.append(rest_of_line)
            # Check for closing tag
            elif '</FILE>' in line or '</file>' in line:
                if current_file and current_content:
                    content = '\n'.join(current_content).strip()
                    if content:
                        files[current_file] = content
                        logger.info(f"Parsed file (closed): {current_file} ({len(content)} chars)")
                current_file = None
                current_content = []
            # Regular content line
            elif current_file:
                current_content.append(line)
        
        # Don't forget the last file if parsing ended without </FILE>
        if current_file and current_content:
            content = '\n'.join(current_content).strip()
            if content:
                files[current_file] = content
                logger.info(f"Parsed file (last): {current_file} ({len(content)} chars)")
    
    # Ensure LICENSE file exists
    if "LICENSE" not in files:
        files["LICENSE"] = """MIT License

Copyright (c) 2025 LLM App Developer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        logger.info("Added MIT LICENSE (not generated by LLM)")
    
    # Ensure README.md exists with basic content
    if "README.md" not in files:
        # Extract app name from the first file if available
        app_name = "Web Application"
        if "index.html" in files:
            # Try to extract title from HTML
            import re
            title_match = re.search(r'<title>([^<]+)</title>', files["index.html"], re.IGNORECASE)
            if title_match:
                app_name = title_match.group(1)
        
        files["README.md"] = f"""# {app_name}

Auto-generated web application.

## Features

- Modern, responsive design
- Clean and intuitive interface
- Production-ready code

## Usage

Open `index.html` in a web browser or visit the GitHub Pages deployment.

## License

MIT License - see LICENSE file for details.
"""
        logger.info("Added default README.md (not generated by LLM)")
    
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
    import os
    
    # Clone or get repo directory
    if is_update:
        repo_dir = clone_existing_repo(repo_url, f"{task_id}-update")
    else:
        # For Round 1, check if repo already exists on GitHub (e.g., from previous failed run)
        # If it exists, clone it; otherwise, initialize a new repo
        github_token = os.getenv("GITHUB_TOKEN")
        
        # Extract owner and repo name from URL
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[-1].split("/")
            owner = parts[0]
            repo_name = parts[1].replace(".git", "")
            
            # Check if repo exists on GitHub
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            check_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo_name}",
                headers=headers,
                timeout=10,
            )
            
            if check_response.status_code == 200:
                # Repo exists, clone it
                logger.info(f"Repository {repo_name} exists, cloning...")
                repo_dir = clone_existing_repo(repo_url, task_id)
            else:
                # Repo doesn't exist, initialize new
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
        else:
            # If not a GitHub URL, just initialize
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

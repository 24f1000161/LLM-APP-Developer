# Utility functions for the LLM App Developer
import os
import time
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for exponential backoff retries."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )
        return delay


def retry_with_backoff(
    func,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        *args: Positional arguments
        config: RetryConfig instance
        **kwargs: Keyword arguments
    
    Returns:
        Function return value
    
    Raises:
        Exception: If all retries exhausted
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < config.max_retries - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}"
                )
                time.sleep(delay)
            else:
                logger.error(f"All {config.max_retries} attempts exhausted")
    
    raise last_exception


def post_with_retry(
    url: str,
    json_data: Dict[str, Any],
    config: Optional[RetryConfig] = None,
    **kwargs
) -> requests.Response:
    """
    POST request with exponential backoff retry.
    
    Args:
        url: Target URL
        json_data: JSON payload
        config: RetryConfig instance
        **kwargs: Additional arguments to requests.post()
    
    Returns:
        requests.Response object
    """
    def _post():
        return requests.post(url, json=json_data, **kwargs)
    
    return retry_with_backoff(_post, config=config)


def load_attachment(attachment_data: Dict[str, str]) -> bytes:
    """
    Load attachment data from data URI or remote URL.
    
    Args:
        attachment_data: Dict with 'name' and 'url' keys
    
    Returns:
        Binary content of the attachment
    """
    url = attachment_data.get("url", "")
    name = attachment_data.get("name", "attachment")
    
    if url.startswith("data:"):
        return _decode_data_uri(url)
    else:
        return _download_file(url, name)


def _decode_data_uri(data_uri: str) -> bytes:
    """Decode base64 data URI."""
    import base64
    try:
        # Format: data:mime/type;base64,<content>
        parts = data_uri.split(",", 1)
        if len(parts) != 2:
            raise ValueError("Invalid data URI format")
        content = parts[1]
        return base64.b64decode(content)
    except Exception as e:
        logger.error(f"Failed to decode data URI: {e}")
        return b""


def _download_file(url: str, name: str) -> bytes:
    """Download file from URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to download {name} from {url}: {e}")
        return b""


def ensure_env_var(var_name: str, description: str = "") -> str:
    """
    Ensure an environment variable is set.
    
    Args:
        var_name: Name of the environment variable
        description: Human-readable description
    
    Returns:
        Value of the environment variable
    
    Raises:
        ValueError: If not set
    """
    value = os.getenv(var_name)
    if not value:
        msg = f"Environment variable {var_name} is not set"
        if description:
            msg += f" ({description})"
        raise ValueError(msg)
    return value


def create_temp_dir(base_name: str) -> Path:
    """Create a temporary directory for working with repos."""
    import tempfile
    
    temp_dir = Path(tempfile.gettempdir()) / f"llm-app-{base_name}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def safe_filename(text: str, max_length: int = 50) -> str:
    """
    Convert text to a safe filename.
    
    Args:
        text: Text to convert
        max_length: Maximum filename length
    
    Returns:
        Safe filename
    """
    import re
    
    # Replace non-alphanumeric with hyphens
    safe = re.sub(r"[^\w\-]", "-", text.lower())
    # Remove multiple consecutive hyphens
    safe = re.sub(r"-+", "-", safe)
    # Remove leading/trailing hyphens
    safe = safe.strip("-")
    # Limit length
    safe = safe[:max_length]
    
    return safe or "unnamed"

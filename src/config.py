# Configuration management
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """Application configuration from environment variables."""
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Secrets and Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USER: str = os.getenv("GITHUB_USER", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # GitHub Configuration
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_REPO_PREFIX: str = os.getenv("GITHUB_REPO_PREFIX", "llm-app")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-5-nano")
    LLM_FALLBACK_MODEL: str = os.getenv("LLM_FALLBACK_MODEL", "gemini-2.0-flash")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 4096))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0.7))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", 1.0))
    RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", 300.0))
    
    # Timeouts
    GITHUB_API_TIMEOUT: int = int(os.getenv("GITHUB_API_TIMEOUT", 10))
    GITHUB_PUSH_TIMEOUT: int = int(os.getenv("GITHUB_PUSH_TIMEOUT", 30))
    API_NOTIFICATION_TIMEOUT: int = int(os.getenv("API_NOTIFICATION_TIMEOUT", 10))
    
    # Directories
    TEMP_BASE_DIR: str = os.getenv("TEMP_BASE_DIR", "/tmp")
    
    @classmethod
    def validate(cls) -> list:
        """
        Validate required configuration.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        required = {
            "SECRET_KEY": "Student secret for verification",
            "GITHUB_TOKEN": "GitHub personal access token",
            "GITHUB_USER": "GitHub username",
            "OPENAI_API_KEY": "OpenAI API key for GPT-5-nano (primary)",
            "GEMINI_API_KEY": "Google Gemini API key (fallback)",
        }
        
        for key, description in required.items():
            if not getattr(cls, key, None):
                errors.append(f"Missing {key}: {description}")
        
        return errors
    
    @classmethod
    def get_required_scopes(cls) -> list:
        """List required GitHub token scopes."""
        return [
            "repo",              # Full control of repositories
            "delete_repo",       # Delete repositories if needed
            "write:packages",    # For Pages deployment
        ]
    
    @classmethod
    def print_config(cls) -> None:
        """Print configuration (without sensitive values)."""
        config_items = {
            "host": cls.HOST,
            "port": cls.PORT,
            "log_level": cls.LOG_LEVEL,
            "github_user": cls.GITHUB_USER,
            "github_api_base": cls.GITHUB_API_BASE,
            "llm_model": cls.LLM_MODEL,
            "temp_dir": cls.TEMP_BASE_DIR,
            "max_retries": cls.MAX_RETRIES,
        }
        
        print("\n" + "=" * 50)
        print("Configuration Loaded:")
        for key, value in config_items.items():
            print(f"  {key}: {value}")
        print("=" * 50 + "\n")

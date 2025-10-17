import os
import logging

logger = logging.getLogger(__name__)


def validate_secret(provided_secret: str) -> bool:
    """
    Validate that the provided secret matches the expected secret.
    
    The expected secret is stored in the STUDENT_SECRET environment variable.
    This should be configured in a .env file or as an environment variable.
    
    Args:
        provided_secret: The secret provided in the request
    
    Returns:
        bool: True if the secret is valid, False otherwise
    """
    expected_secret = os.getenv("STUDENT_SECRET", "")
    
    if not expected_secret:
        logger.warning("STUDENT_SECRET environment variable is not set")
        return False
    
    # Use constant-time comparison to prevent timing attacks
    from hmac import compare_digest
    
    is_valid = compare_digest(provided_secret, expected_secret)
    
    if not is_valid:
        logger.warning("Invalid secret provided in request")
    
    return is_valid


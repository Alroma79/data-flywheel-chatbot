"""
Utility functions and helpers for the Data Flywheel Chatbot application.
"""

import logging
import sys
from typing import Optional
from .config import get_settings

settings = get_settings()


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up application logging configuration.
    
    Args:
        log_level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    level = log_level or settings.log_level
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create application logger
    logger = logging.getLogger("data_flywheel_chatbot")
    
    return logger


def validate_openai_response(response) -> bool:
    """
    Validate OpenAI API response structure.
    
    Args:
        response: OpenAI API response object
        
    Returns:
        True if response is valid, False otherwise
    """
    try:
        return (
            hasattr(response, 'choices') and 
            len(response.choices) > 0 and
            hasattr(response.choices[0], 'message') and
            hasattr(response.choices[0].message, 'content')
        )
    except Exception:
        return False


def sanitize_user_input(user_input: str, max_length: int = 4000) -> str:
    """
    Sanitize user input for safety and length constraints.
    
    Args:
        user_input: Raw user input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized input string
    """
    if not user_input:
        return ""
    
    # Remove potential harmful characters and limit length
    sanitized = user_input.strip()[:max_length]
    
    # Remove null bytes and other control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
    
    return sanitized


def format_error_response(error: Exception, include_details: bool = False) -> dict:
    """
    Format error response for API endpoints.
    
    Args:
        error: Exception instance
        include_details: Whether to include detailed error information
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": True,
        "message": "An error occurred while processing your request"
    }
    
    if include_details or settings.debug:
        response["details"] = str(error)
        response["type"] = type(error).__name__
    
    return response

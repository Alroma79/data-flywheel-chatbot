"""
Pydantic schemas for request/response validation in the Data Flywheel Chatbot API.

This module defines the data validation schemas used for API endpoints,
ensuring proper data types and validation for all requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ChatRequest(BaseModel):
    """
    Schema for chat message requests.

    Attributes:
        message: The user's chat message (1-4000 characters)
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's chat message",
        example="Hello, how can you help me today?"
    )

    @validator('message')
    def validate_message(cls, v):
        """Validate message is not just whitespace."""
        if not v.strip():
            raise ValueError('Message cannot be empty or just whitespace')
        return v.strip()


class FeedbackType(str, Enum):
    """
    Enumeration for feedback types.

    Values:
        thumbs_up: Positive feedback
        thumbs_down: Negative feedback
    """
    thumbs_up = "thumbs_up"
    thumbs_down = "thumbs_down"


class FeedbackCreate(BaseModel):
    """
    Schema for creating feedback entries.

    Attributes:
        message: The original message being rated
        user_feedback: The user's rating (thumbs_up/thumbs_down)
        comment: Optional additional comment
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Original message being rated"
    )
    user_feedback: FeedbackType = Field(
        ...,
        description="User's rating for the message"
    )
    comment: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional additional comment"
    )


class ChatbotConfigBase(BaseModel):
    """
    Base schema for chatbot configuration.

    Attributes:
        name: Configuration name/identifier
        config_json: JSON configuration data
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Configuration name",
        example="production_config"
    )
    config_json: Dict[str, Any] = Field(
        ...,
        description="JSON configuration data",
        example={
            "system_prompt": "You are a helpful assistant.",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )

    @validator('config_json')
    def validate_config_json(cls, v):
        """Validate required configuration fields."""
        required_fields = ['system_prompt', 'model', 'temperature']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')

        # Validate temperature range
        if not 0 <= v.get('temperature', 0.7) <= 2:
            raise ValueError('Temperature must be between 0 and 2')

        return v


class ChatbotConfigCreate(ChatbotConfigBase):
    """Schema for creating new chatbot configurations."""
    pass


class ChatbotConfigOut(ChatbotConfigBase):
    """
    Schema for chatbot configuration responses.

    Attributes:
        id: Configuration ID
        updated_at: Last update timestamp
    """
    id: int = Field(..., description="Configuration ID")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        orm_mode = True

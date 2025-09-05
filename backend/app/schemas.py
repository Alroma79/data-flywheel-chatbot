"""
Pydantic schemas for request/response validation in the Data Flywheel Chatbot API.

This module defines the data validation schemas used for API endpoints,
ensuring proper data types and validation for all requests and responses.
"""

from pydantic import BaseModel, Field
from pydantic import field_validator 
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class ChatRequest(BaseModel):
    """
    Schema for chat message requests.

    Attributes:
        message: The user's chat message (1-4000 characters)
        session_id: Optional session identifier for multi-turn conversations
        user_id: Optional user identifier
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's chat message",
        example="Hello, how can you help me today?"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for continuing conversations",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier",
        example="user123"
    )

    @field_validator('message', mode='before')
    @classmethod
    def validate_message(cls, v):
        if not isinstance(v, str):
            raise ValueError('Message must be a string')
        s = v.strip()
        if not s:
            raise ValueError('Message cannot be empty or just whitespace')
        return s


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
        is_active: Whether the configuration is active
        tags: Optional tags for categorizing configurations
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
    is_active: bool = Field(
        True,
        description="Whether the configuration is active"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Optional tags for categorizing configurations",
        example=["production", "customer-service"]
    )

    @field_validator('config_json')
    @classmethod
    def validate_config_json(cls, v):
        """Validate required configuration fields."""
        required_fields = ['system_prompt', 'model', 'temperature']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')
        if not 0 <= v.get('temperature', 0.7) <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        if not str(v.get('system_prompt', '')).strip():
            raise ValueError('system_prompt cannot be empty')
        if not str(v.get('model', '')).strip():
            raise ValueError('model cannot be empty')
        return v


class ChatbotConfigCreate(ChatbotConfigBase):
    """Schema for creating new chatbot configurations."""
    pass


class ChatbotConfigUpdate(BaseModel):
    """Schema for updating chatbot configurations."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Configuration name"
    )
    config_json: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON configuration data"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the configuration is active"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Optional tags for categorizing configurations"
    )

    @field_validator('config_json')
    @classmethod
    def validate_config_json_update(cls, v):
        """Validate configuration fields if provided."""
        if v is None:
            return v
        if 'temperature' in v and not 0 <= v['temperature'] <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        if 'system_prompt' in v and not str(v['system_prompt']).strip():
            raise ValueError('system_prompt cannot be empty')
        if 'model' in v and not str(v['model']).strip():
            raise ValueError('model cannot be empty')
        return v


class ChatbotConfigOut(ChatbotConfigBase):
    """
    Schema for chatbot configuration responses.

    Attributes:
        id: Configuration ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: int = Field(..., description="Configuration ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


# -------------------------------
# Knowledge File Schemas
# -------------------------------
class KnowledgeFileOut(BaseModel):
    """
    Schema for knowledge file responses.

    Attributes:
        id: File ID
        filename: Original filename
        content_type: MIME type of the file
        size: File size in bytes
        sha256: SHA256 hash of file content
        created_at: File upload timestamp
    """
    id: int = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    sha256: str = Field(..., description="SHA256 hash of file content")
    created_at: datetime = Field(..., description="File upload timestamp")

    model_config = {"from_attributes": True}


class KnowledgeFileUploadResponse(BaseModel):
    """
    Schema for file upload responses.

    Attributes:
        id: File ID
        filename: Original filename
        size: File size in bytes
        message: Success message
    """
    id: int = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Success message")


# -------------------------------
# Pagination Schemas
# -------------------------------
class PaginatedResponse(BaseModel):
    """
    Schema for paginated responses.

    Attributes:
        items: List of items
        total: Total number of items
        page: Current page number
        size: Items per page
        pages: Total number of pages
    """
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")

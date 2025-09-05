"""
SQLAlchemy ORM models for the Data Flywheel Chatbot application.

This module defines the database schema and models for storing
chat history, user feedback, and chatbot configuration.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
from .db import Base


class Feedback(Base):
    """
    Model for storing user feedback on chat interactions.

    Attributes:
        id: Primary key identifier
        message: The original message that was rated
        user_feedback: User rating (thumbs_up/thumbs_down)
        comment: Optional user comment
        timestamp: When the feedback was submitted
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False, comment="Original message that was rated")
    user_feedback = Column(String(50), nullable=True, comment="User rating (thumbs_up/thumbs_down)")
    comment = Column(Text, nullable=True, comment="Optional user comment")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="Feedback submission time")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, feedback={self.user_feedback})>"


class ChatHistory(Base):
    """
    Model for storing chat conversation history.

    Attributes:
        id: Primary key identifier
        session_id: Unique session identifier
        role: Message role (user/assistant)
        content: Message content
        created_at: Timestamp of message
        user_id: Optional user identifier
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False, default='', comment="Session identifier")
    role = Column(String(20), nullable=False, comment="Message role: 'user' or 'assistant'")
    content = Column(Text, nullable=False, comment="Message content")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Message timestamp")
    user_id = Column(String(100), nullable=True, comment="Optional user identifier")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, role={self.role}, session_id={self.session_id})>"


class ChatbotConfig(Base):
    """
    Model for storing dynamic chatbot configuration.

    Attributes:
        id: Primary key identifier
        name: Configuration name/identifier
        config_json: JSON configuration data (model, temperature, system_prompt, etc.)
        is_active: Whether the configuration is active
        tags: Optional tags for categorizing configurations
        updated_at: When the configuration was last updated
        created_at: When the configuration was created
    """
    __tablename__ = "chatbot_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="default", comment="Configuration name")
    config_json = Column(JSON, nullable=False, comment="JSON configuration data")
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether the configuration is active")
    tags = Column(JSON, nullable=True, comment="Optional tags for categorizing configurations")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Configuration creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update timestamp")

    def __repr__(self) -> str:
        return f"<ChatbotConfig(id={self.id}, name={self.name}, is_active={self.is_active})>"


class KnowledgeFile(Base):
    """
    Model for storing knowledge file metadata.

    Attributes:
        id: Primary key identifier
        filename: Original filename
        content_type: MIME type of the file
        size: File size in bytes
        sha256: SHA256 hash of the file content
        created_at: When the file was uploaded
    """
    __tablename__ = "knowledge_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="Original filename")
    content_type = Column(String(100), nullable=False, comment="MIME type of the file")
    size = Column(Integer, nullable=False, comment="File size in bytes")
    sha256 = Column(String(64), nullable=False, unique=True, comment="SHA256 hash of file content")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="File upload time")

    def __repr__(self) -> str:
        return f"<KnowledgeFile(id={self.id}, filename={self.filename}, size={self.size})>"
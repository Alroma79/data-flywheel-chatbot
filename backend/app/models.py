"""
SQLAlchemy ORM models for the Data Flywheel Chatbot application.

This module defines the database schema and models for storing
chat history, user feedback, and chatbot configuration.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
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
        user_message: The user's input message
        bot_reply: The chatbot's response
        timestamp: When the conversation occurred
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text, nullable=False, comment="User's input message")
    bot_reply = Column(Text, nullable=False, comment="Chatbot's response")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="Conversation timestamp")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, timestamp={self.timestamp})>"


class ChatbotConfig(Base):
    """
    Model for storing dynamic chatbot configuration.

    Attributes:
        id: Primary key identifier
        name: Configuration name/identifier
        config_json: JSON configuration data (model, temperature, system_prompt, etc.)
        updated_at: When the configuration was last updated
    """
    __tablename__ = "chatbot_config"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="default", comment="Configuration name")
    config_json = Column(JSON, nullable=False, comment="JSON configuration data")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update timestamp")

    def __repr__(self) -> str:
        return f"<ChatbotConfig(id={self.id}, name={self.name})>"
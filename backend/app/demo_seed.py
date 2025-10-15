# backend/app/demo_seed.py
"""
Demo seeding utilities.

Provides optional bootstrap data (chatbot configuration, etc.) when
`DEMO_MODE` is enabled. Keeps CI environments clean and idempotent.
"""

import os
from typing import Any
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .db import SessionLocal
from .models import ChatbotConfig
from .utils import setup_logging

settings = get_settings()
logger = setup_logging()


def _default_config_payload() -> dict:
    """Return a baseline chatbot configuration."""
    return {
        "system_prompt": "You are a helpful assistant for the Data Flywheel Chatbot.",
        "model": settings.default_model,
        "temperature": settings.default_temperature,
        "max_tokens": settings.max_tokens,
    }


async def seed_demo(app: Any) -> bool:
    """
    Optionally seed default configuration data.

    Returns:
        True if new demo data was inserted, False otherwise.
    """
    if os.getenv("CI") == "true":
        return False

    if not settings.demo_mode:
        return False

    session = SessionLocal()
    try:
        existing = session.query(ChatbotConfig).count()
        if existing > 0:
            logger.info("Demo seed skipped: chatbot configuration already present.")
            return False

        config = ChatbotConfig(
            name="default",
            config_json=_default_config_payload(),
            is_active=True,
            tags=["demo", "default"],
        )
        session.add(config)
        session.commit()
        logger.info("Demo seed inserted default chatbot configuration.")
        return True
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error(f"Demo seed failed: {exc}")
        raise
    finally:
        session.close()

"""Configuration experiment selection and validation helpers."""

import hashlib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import ChatHistory, ChatbotConfig, Experiment


def validate_experiment_configs(db: Session, variants: list[dict]) -> None:
    """Require every experiment variant to reference an active configuration."""
    config_ids = {variant["config_id"] for variant in variants}
    active_ids = {
        config.id
        for config in db.query(ChatbotConfig)
        .filter(
            ChatbotConfig.id.in_(config_ids),
            ChatbotConfig.is_active.is_(True),
        )
        .all()
    }
    missing = sorted(config_ids - active_ids)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Experiment variants must reference active configurations: {missing}",
        )


def choose_weighted_variant(experiment: Experiment, session_id: str) -> int:
    """Choose a deterministic weighted variant for a session."""
    digest = hashlib.sha256(
        f"{experiment.id}:{session_id}".encode("utf-8")
    ).digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    cumulative = 0
    for variant in experiment.variants:
        cumulative += int(variant["weight"])
        if bucket < cumulative:
            return int(variant["config_id"])
    return int(experiment.variants[-1]["config_id"])


def select_chat_configuration(
    db: Session,
    session_id: str,
    is_new_session: bool = False,
) -> tuple[ChatbotConfig | None, Experiment | None]:
    """Return the sticky session variant or assign the active experiment."""
    previous = None
    if not is_new_session:
        previous = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id == session_id,
                ChatHistory.config_id.is_not(None),
            )
            .order_by(ChatHistory.id.asc())
            .first()
        )
    if previous:
        config = db.query(ChatbotConfig).filter(ChatbotConfig.id == previous.config_id).first()
        experiment = (
            db.query(Experiment).filter(Experiment.id == previous.experiment_id).first()
            if previous.experiment_id
            else None
        )
        if config:
            return config, experiment

    experiment = (
        db.query(Experiment)
        .filter(Experiment.status == "active")
        .order_by(Experiment.updated_at.desc(), Experiment.id.desc())
        .first()
    )
    if experiment:
        config_id = choose_weighted_variant(experiment, session_id)
        config = (
            db.query(ChatbotConfig)
            .filter(
                ChatbotConfig.id == config_id,
                ChatbotConfig.is_active.is_(True),
            )
            .first()
        )
        if config:
            return config, experiment

    config = (
        db.query(ChatbotConfig)
        .filter(ChatbotConfig.is_active.is_(True))
        .order_by(ChatbotConfig.updated_at.desc())
        .first()
    )
    return config, None

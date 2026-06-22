"""Internal analytics for the feedback-driven data flywheel."""

from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from .auth import verify_bearer_token
from .db import SessionLocal
from .models import ChatHistory, ChatbotConfig, Experiment, Feedback

router = APIRouter(prefix="/analytics", tags=["flywheel-analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/experiments")
async def experiment_performance(
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    """Return experiment lifecycle and outcome metrics by variant."""
    experiments = db.query(Experiment).order_by(Experiment.updated_at.desc()).all()
    configs = {config.id: config for config in db.query(ChatbotConfig).all()}

    response_rows = (
        db.query(
            ChatHistory.experiment_id,
            ChatHistory.config_id,
            func.count(ChatHistory.id).label("total_responses"),
            func.count(func.distinct(ChatHistory.session_id)).label("sessions"),
            func.avg(ChatHistory.latency_ms).label("average_latency_ms"),
        )
        .filter(
            ChatHistory.role == "assistant",
            ChatHistory.experiment_id.is_not(None),
        )
        .group_by(ChatHistory.experiment_id, ChatHistory.config_id)
        .all()
    )
    feedback_rows = (
        db.query(
            Feedback.experiment_id,
            Feedback.config_id,
            func.count(Feedback.id).label("rated_responses"),
            func.sum(
                case((Feedback.user_feedback == "thumbs_up", 1), else_=0)
            ).label("positive_feedback"),
            func.sum(
                case((Feedback.user_feedback == "thumbs_down", 1), else_=0)
            ).label("negative_feedback"),
        )
        .filter(Feedback.experiment_id.is_not(None))
        .group_by(Feedback.experiment_id, Feedback.config_id)
        .all()
    )

    responses = {
        (row.experiment_id, row.config_id): row for row in response_rows
    }
    feedback = {
        (row.experiment_id, row.config_id): row for row in feedback_rows
    }
    results = []
    for experiment in experiments:
        variants = []
        for configured_variant in experiment.variants:
            config_id = int(configured_variant["config_id"])
            response = responses.get((experiment.id, config_id))
            rating = feedback.get((experiment.id, config_id))
            total = int(response.total_responses or 0) if response else 0
            sessions = int(response.sessions or 0) if response else 0
            rated = int(rating.rated_responses or 0) if rating else 0
            positive = int(rating.positive_feedback or 0) if rating else 0
            variants.append(
                {
                    "config_id": config_id,
                    "config_name": (
                        configs[config_id].name
                        if config_id in configs
                        else f"Config {config_id}"
                    ),
                    "weight": int(configured_variant["weight"]),
                    "sessions": sessions,
                    "total_responses": total,
                    "rated_responses": rated,
                    "positive_feedback": positive,
                    "negative_feedback": (
                        int(rating.negative_feedback or 0) if rating else 0
                    ),
                    "approval_rate": round(positive / rated, 4) if rated else None,
                    "feedback_coverage": round(rated / total, 4) if total else 0,
                    "average_latency_ms": (
                        round(float(response.average_latency_ms), 1)
                        if response and response.average_latency_ms is not None
                        else None
                    ),
                }
            )
        total_sessions = sum(variant["sessions"] for variant in variants)
        for variant in variants:
            variant["actual_allocation"] = (
                round(variant["sessions"] / total_sessions, 4)
                if total_sessions
                else 0
            )
        results.append(
            {
                "experiment_id": experiment.id,
                "name": experiment.name,
                "status": experiment.status,
                "total_sessions": total_sessions,
                "variants": variants,
                "created_at": experiment.created_at.isoformat(),
                "updated_at": experiment.updated_at.isoformat(),
            }
        )
    return results


@router.get("/configurations")
async def configuration_performance(
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    """Return response volume and approval metrics by chatbot configuration."""
    response_rows = (
        db.query(
            ChatHistory.config_id,
            func.max(ChatHistory.model_name).label("model_name"),
            func.count(ChatHistory.id).label("total_responses"),
            func.avg(ChatHistory.latency_ms).label("average_latency_ms"),
        )
        .filter(ChatHistory.role == "assistant")
        .group_by(ChatHistory.config_id)
        .all()
    )

    feedback_rows = (
        db.query(
            Feedback.config_id,
            func.count(Feedback.id).label("rated_responses"),
            func.sum(
                case((Feedback.user_feedback == "thumbs_up", 1), else_=0)
            ).label("positive_feedback"),
            func.sum(
                case((Feedback.user_feedback == "thumbs_down", 1), else_=0)
            ).label("negative_feedback"),
        )
        .group_by(Feedback.config_id)
        .all()
    )

    configs = {config.id: config for config in db.query(ChatbotConfig).all()}
    feedback_by_config = {row.config_id: row for row in feedback_rows}
    results = []

    for row in response_rows:
        feedback = feedback_by_config.get(row.config_id)
        rated = int(feedback.rated_responses or 0) if feedback else 0
        positive = int(feedback.positive_feedback or 0) if feedback else 0
        negative = int(feedback.negative_feedback or 0) if feedback else 0
        config = configs.get(row.config_id)

        results.append(
            {
                "config_id": row.config_id,
                "config_name": config.name if config else "Unattributed",
                "model": row.model_name,
                "total_responses": int(row.total_responses or 0),
                "rated_responses": rated,
                "positive_feedback": positive,
                "negative_feedback": negative,
                "approval_rate": round(positive / rated, 4) if rated else None,
                "feedback_coverage": (
                    round(rated / row.total_responses, 4)
                    if row.total_responses
                    else 0
                ),
                "average_latency_ms": (
                    round(float(row.average_latency_ms), 1)
                    if row.average_latency_ms is not None
                    else None
                ),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            item["approval_rate"] is not None,
            item["approval_rate"] or 0,
            item["rated_responses"],
        ),
        reverse=True,
    )


@router.get("/negative-feedback")
async def negative_feedback_examples(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    """Return recent poorly rated responses with their originating prompt."""
    rows = (
        db.query(Feedback, ChatHistory, ChatbotConfig)
        .outerjoin(ChatHistory, Feedback.response_id == ChatHistory.id)
        .outerjoin(ChatbotConfig, Feedback.config_id == ChatbotConfig.id)
        .filter(Feedback.user_feedback == "thumbs_down")
        .order_by(Feedback.timestamp.desc())
        .limit(limit)
        .all()
    )

    session_ids = {
        response.session_id
        for _, response, _ in rows
        if response is not None and response.session_id
    }
    prompts_by_session = defaultdict(list)
    if session_ids:
        user_messages = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.session_id.in_(session_ids),
                ChatHistory.role == "user",
            )
            .order_by(ChatHistory.session_id, ChatHistory.id.desc())
            .all()
        )
        for message in user_messages:
            prompts_by_session[message.session_id].append(message)

    results = []
    for feedback, response, config in rows:
        prompt = None
        if response is not None:
            prompt_message = next(
                (
                    message
                    for message in prompts_by_session.get(response.session_id, [])
                    if message.id < response.id
                ),
                None,
            )
            prompt = prompt_message.content if prompt_message else None

        results.append(
            {
                "feedback_id": feedback.id,
                "response_id": feedback.response_id,
                "prompt": prompt,
                "response": response.content if response else feedback.message,
                "comment": feedback.comment,
                "config_id": feedback.config_id,
                "config_name": config.name if config else "Unattributed",
                "experiment_id": feedback.experiment_id,
                "model": response.model_name if response else None,
                "timestamp": feedback.timestamp.isoformat(),
            }
        )

    return results

"""Human-reviewed recommendations generated from recurring negative feedback."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import verify_bearer_token
from .db import SessionLocal
from .models import ChatbotConfig, FeedbackRecommendation
from .recommendations import collect_negative_feedback_clusters, proposed_configuration
from .schemas import (
    FeedbackRecommendationOut,
    RecommendationApproval,
    RecommendationStatus,
)

router = APIRouter(prefix="/recommendations", tags=["flywheel-recommendations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _recommendation_or_404(
    db: Session,
    recommendation_id: int,
) -> FeedbackRecommendation:
    recommendation = (
        db.query(FeedbackRecommendation)
        .filter(FeedbackRecommendation.id == recommendation_id)
        .first()
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return recommendation


@router.get("", response_model=list[FeedbackRecommendationOut])
async def list_recommendations(
    recommendation_status: RecommendationStatus | None = Query(
        None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    query = db.query(FeedbackRecommendation)
    if recommendation_status is not None:
        query = query.filter(
            FeedbackRecommendation.status == recommendation_status.value
        )
    return query.order_by(FeedbackRecommendation.updated_at.desc()).all()


@router.post("/generate", response_model=list[FeedbackRecommendationOut])
async def generate_recommendations(
    min_count: int = Query(2, ge=1, le=100),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    """Upsert pending recommendations for recurring negative-feedback themes."""
    clusters = collect_negative_feedback_clusters(db, limit=limit)
    generated = []
    try:
        for cluster in clusters:
            theme = cluster["theme"]
            pending = (
                db.query(FeedbackRecommendation)
                .filter(
                    FeedbackRecommendation.source_config_id == cluster["config_id"],
                    FeedbackRecommendation.theme_key == theme["key"],
                    FeedbackRecommendation.status == "pending",
                )
                .first()
            )
            prior = (
                db.query(FeedbackRecommendation)
                .filter(
                    FeedbackRecommendation.source_config_id == cluster["config_id"],
                    FeedbackRecommendation.theme_key == theme["key"],
                )
                .all()
            )
            consumed_ids = {
                feedback_id
                for recommendation in prior
                if recommendation.id != (pending.id if pending else None)
                for feedback_id in recommendation.source_feedback_ids
            }
            feedback_ids = (
                cluster["feedback_ids"]
                if pending
                else [
                    feedback_id
                    for feedback_id in cluster["feedback_ids"]
                    if feedback_id not in consumed_ids
                ]
            )
            if len(feedback_ids) < min_count:
                continue
            evidence_examples = [
                example
                for example in cluster["examples"]
                if example["feedback_id"] in feedback_ids
            ]
            source = (
                db.query(ChatbotConfig)
                .filter(ChatbotConfig.id == cluster["config_id"])
                .first()
                if cluster["config_id"] is not None
                else db.query(ChatbotConfig)
                .filter(ChatbotConfig.is_active.is_(True))
                .order_by(ChatbotConfig.updated_at.desc())
                .first()
            )
            evidence_count = len(feedback_ids)
            summary = (
                f"{evidence_count} negative feedback item(s) for "
                f"{cluster['config_name']} match the '{theme['title']}' theme."
            )
            values = {
                "title": theme["title"],
                "summary": summary,
                "source_feedback_ids": feedback_ids,
                "evidence_examples": evidence_examples,
                "proposed_config_json": proposed_configuration(source, theme),
            }
            if pending:
                for field, value in values.items():
                    setattr(pending, field, value)
                recommendation = pending
            else:
                recommendation = FeedbackRecommendation(
                    theme_key=theme["key"],
                    status="pending",
                    source_config_id=cluster["config_id"],
                    **values,
                )
                db.add(recommendation)
            generated.append(recommendation)
        db.commit()
        for recommendation in generated:
            db.refresh(recommendation)
        return generated
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations",
        )


@router.post(
    "/{recommendation_id}/approve",
    response_model=FeedbackRecommendationOut,
)
async def approve_recommendation(
    recommendation_id: int,
    request: RecommendationApproval,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    """Create an inactive configuration draft after explicit human approval."""
    recommendation = _recommendation_or_404(db, recommendation_id)
    if recommendation.status != "pending":
        raise HTTPException(status_code=409, detail="Recommendation is not pending")
    name = request.configuration_name or (
        f"Draft - {recommendation.title} - {recommendation.id}"
    )
    if db.query(ChatbotConfig).filter(ChatbotConfig.name == name).first():
        raise HTTPException(status_code=400, detail="Configuration name already exists")

    try:
        draft = ChatbotConfig(
            name=name,
            config_json=recommendation.proposed_config_json,
            is_active=False,
            tags=[
                "recommendation-draft",
                f"theme:{recommendation.theme_key}",
                f"recommendation:{recommendation.id}",
            ],
        )
        db.add(draft)
        db.flush()
        recommendation.status = "approved"
        recommendation.resulting_config_id = draft.id
        recommendation.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(recommendation)
        return recommendation
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to approve recommendation")


@router.post(
    "/{recommendation_id}/dismiss",
    response_model=FeedbackRecommendationOut,
)
async def dismiss_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    recommendation = _recommendation_or_404(db, recommendation_id)
    if recommendation.status != "pending":
        raise HTTPException(status_code=409, detail="Recommendation is not pending")
    try:
        recommendation.status = "dismissed"
        recommendation.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(recommendation)
        return recommendation
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to dismiss recommendation")

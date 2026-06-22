"""CRUD and lifecycle routes for weighted configuration experiments."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import verify_bearer_token
from .db import SessionLocal
from .experiments import validate_experiment_configs
from .models import Experiment
from .schemas import ExperimentCreate, ExperimentOut, ExperimentUpdate

router = APIRouter(prefix="/experiments", tags=["configuration-experiments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _experiment_or_404(db: Session, experiment_id: int) -> Experiment:
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.get("", response_model=list[ExperimentOut])
async def list_experiments(
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    return db.query(Experiment).order_by(Experiment.updated_at.desc()).all()


@router.post("", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: ExperimentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    variants = [variant.model_dump() for variant in request.variants]
    validate_experiment_configs(db, variants)
    if db.query(Experiment).filter(Experiment.name == request.name).first():
        raise HTTPException(status_code=400, detail="Experiment name already exists")
    experiment = Experiment(name=request.name, variants=variants, status="draft")
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentOut)
async def update_experiment(
    experiment_id: int,
    request: ExperimentUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    experiment = _experiment_or_404(db, experiment_id)
    if experiment.status == "active":
        raise HTTPException(status_code=409, detail="Pause the experiment before editing it")
    if request.name is not None:
        duplicate = (
            db.query(Experiment)
            .filter(Experiment.name == request.name, Experiment.id != experiment_id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=400, detail="Experiment name already exists")
        experiment.name = request.name
    if request.variants is not None:
        variants = [variant.model_dump() for variant in request.variants]
        validate_experiment_configs(db, variants)
        experiment.variants = variants
    db.commit()
    db.refresh(experiment)
    return experiment


@router.post("/{experiment_id}/activate", response_model=ExperimentOut)
async def activate_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    try:
        experiment = _experiment_or_404(db, experiment_id)
        validate_experiment_configs(db, experiment.variants)
        db.query(Experiment).filter(
            Experiment.status == "active",
            Experiment.id != experiment_id,
        ).update({"status": "paused"}, synchronize_session=False)
        experiment.status = "active"
        db.commit()
        db.refresh(experiment)
        return experiment
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate experiment")


@router.post("/{experiment_id}/pause", response_model=ExperimentOut)
async def pause_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    experiment = _experiment_or_404(db, experiment_id)
    experiment.status = "paused"
    db.commit()
    db.refresh(experiment)
    return experiment


@router.post("/{experiment_id}/complete", response_model=ExperimentOut)
async def complete_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token),
):
    experiment = _experiment_or_404(db, experiment_id)
    experiment.status = "completed"
    db.commit()
    db.refresh(experiment)
    return experiment

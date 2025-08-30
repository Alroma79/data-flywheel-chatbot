"""
API routes for chatbot configuration CRUD operations.

This module contains all the CRUD endpoints for managing chatbot configurations
under the /api/v1/configs path.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from math import ceil

from .utils import setup_logging
from .db import SessionLocal
from .models import ChatbotConfig
from .schemas import (
    ChatbotConfigCreate, 
    ChatbotConfigUpdate, 
    ChatbotConfigOut, 
    PaginatedResponse
)

# Initialize logging
logger = setup_logging()

router = APIRouter(prefix="/configs", tags=["chatbot-configs"])

def get_db() -> Session:
    """
    Dependency to get database session.

    Yields:
        Database session instance

    Raises:
        HTTPException: If database connection fails
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
    finally:
        db.close()


@router.get("", response_model=PaginatedResponse)
async def list_configs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(False, description="Filter only active configurations"),
    db: Session = Depends(get_db)
):
    """
    List all chatbot configurations with pagination.

    Args:
        page: Page number (starts from 1)
        size: Number of items per page (1-100)
        active_only: Filter only active configurations
        db: Database session dependency

    Returns:
        Paginated list of chatbot configurations

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Listing configs - page: {page}, size: {size}, active_only: {active_only}")

        # Build query
        query = db.query(ChatbotConfig)
        if active_only:
            query = query.filter(ChatbotConfig.is_active == True)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * size
        configs = query.order_by(desc(ChatbotConfig.updated_at)).offset(offset).limit(size).all()

        # Calculate pagination info
        pages = ceil(total / size) if total > 0 else 1

        response_data = {
            "items": [ChatbotConfigOut.from_orm(config) for config in configs],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

        logger.info(f"Retrieved {len(configs)} configs (total: {total})")
        return JSONResponse(content=response_data)

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configurations"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing configs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{config_id}", response_model=ChatbotConfigOut)
async def get_config(config_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific chatbot configuration by ID.

    Args:
        config_id: Configuration ID
        db: Database session dependency

    Returns:
        Chatbot configuration details

    Raises:
        HTTPException: If configuration not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving config with ID: {config_id}")

        config = db.query(ChatbotConfig).filter(ChatbotConfig.id == config_id).first()

        if not config:
            logger.warning(f"Config with ID {config_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with ID {config_id} not found"
            )

        logger.info(f"Retrieved config: {config.name}")
        return config

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("", response_model=ChatbotConfigOut, status_code=status.HTTP_201_CREATED)
async def create_config(new_config: ChatbotConfigCreate, db: Session = Depends(get_db)):
    """
    Create a new chatbot configuration.

    Args:
        new_config: Configuration data
        db: Database session dependency

    Returns:
        Created configuration

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating new config: {new_config.name}")

        # Check if name already exists
        existing = db.query(ChatbotConfig).filter(ChatbotConfig.name == new_config.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration with name '{new_config.name}' already exists"
            )

        config = ChatbotConfig(
            name=new_config.name,
            config_json=new_config.config_json,
            is_active=new_config.is_active,
            tags=new_config.tags
        )

        db.add(config)
        db.commit()
        db.refresh(config)

        logger.info(f"Config created successfully with ID: {config.id}")
        return config

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating config: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while creating config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.put("/{config_id}", response_model=ChatbotConfigOut)
async def update_config(
    config_id: int,
    config_update: ChatbotConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing chatbot configuration.

    Args:
        config_id: Configuration ID
        config_update: Updated configuration data
        db: Database session dependency

    Returns:
        Updated configuration

    Raises:
        HTTPException: If configuration not found or update fails
    """
    try:
        logger.info(f"Updating config with ID: {config_id}")

        config = db.query(ChatbotConfig).filter(ChatbotConfig.id == config_id).first()

        if not config:
            logger.warning(f"Config with ID {config_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with ID {config_id} not found"
            )

        # Check if name already exists (if name is being updated)
        if config_update.name and config_update.name != config.name:
            existing = db.query(ChatbotConfig).filter(
                ChatbotConfig.name == config_update.name,
                ChatbotConfig.id != config_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuration with name '{config_update.name}' already exists"
                )

        # Update fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        db.commit()
        db.refresh(config)

        logger.info(f"Config updated successfully: {config.name}")
        return config

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating config {config_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """
    Soft delete a chatbot configuration (set is_active=false).

    Args:
        config_id: Configuration ID
        db: Database session dependency

    Returns:
        Success message

    Raises:
        HTTPException: If configuration not found or deletion fails
    """
    try:
        logger.info(f"Soft deleting config with ID: {config_id}")

        config = db.query(ChatbotConfig).filter(ChatbotConfig.id == config_id).first()

        if not config:
            logger.warning(f"Config with ID {config_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration with ID {config_id} not found"
            )

        # Soft delete by setting is_active to False
        config.is_active = False
        db.commit()

        logger.info(f"Config soft deleted successfully: {config.name}")
        return {"message": f"Configuration '{config.name}' has been deactivated"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting config {config_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting config {config_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

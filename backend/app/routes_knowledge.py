"""
API routes for knowledge file management.

This module contains all the endpoints for managing knowledge files
under the /api/v1/knowledge path.
"""

import os
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from .utils import setup_logging
from .db import SessionLocal
from .models import KnowledgeFile
from .schemas import KnowledgeFileOut, KnowledgeFileUploadResponse

# Initialize logging
logger = setup_logging()

router = APIRouter(prefix="/knowledge", tags=["knowledge-files"])

# Allowed file types and max size
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def ensure_uploads_directory():
    """Ensure uploads directory exists."""
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        logger.info(f"Created uploads directory: {uploads_dir}")
    return uploads_dir


@router.post("/files", response_model=KnowledgeFileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="File to upload (PDF, DOCX, or TXT)"),
    db: Session = Depends(get_db)
):
    """
    Upload a knowledge file (PDF, DOCX, or TXT).

    Args:
        file: File to upload
        db: Database session dependency

    Returns:
        Upload response with file metadata

    Raises:
        HTTPException: If upload fails or file type not supported
    """
    try:
        logger.info(f"Uploading file: {file.filename}")

        # Validate file type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not supported. Allowed types: {list(ALLOWED_CONTENT_TYPES.keys())}"
            )

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_size} bytes exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Calculate SHA256 hash
        sha256_hash = calculate_sha256(content)

        # Check if file with same hash already exists
        existing_file = db.query(KnowledgeFile).filter(KnowledgeFile.sha256 == sha256_hash).first()
        if existing_file:
            logger.warning(f"File with same content already exists: {existing_file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File with identical content already exists: {existing_file.filename}"
            )

        # Ensure uploads directory exists
        uploads_dir = ensure_uploads_directory()

        # Generate unique filename to avoid conflicts
        file_extension = ALLOWED_CONTENT_TYPES[file.content_type]
        safe_filename = f"{sha256_hash[:16]}_{file.filename}"
        file_path = os.path.join(uploads_dir, safe_filename)

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        # Save metadata to database
        knowledge_file = KnowledgeFile(
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            sha256=sha256_hash
        )

        db.add(knowledge_file)
        db.commit()
        db.refresh(knowledge_file)

        logger.info(f"File uploaded successfully with ID: {knowledge_file.id}")
        return KnowledgeFileUploadResponse(
            id=knowledge_file.id,
            filename=knowledge_file.filename,
            size=knowledge_file.size,
            message="File uploaded successfully"
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while uploading file: {str(e)}")
        db.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )
    except Exception as e:
        logger.error(f"Unexpected error while uploading file: {str(e)}")
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/files", response_model=List[KnowledgeFileOut])
async def list_files(
    limit: int = Query(50, ge=1, le=100, description="Number of files to retrieve"),
    db: Session = Depends(get_db)
):
    """
    List all uploaded knowledge files.

    Args:
        limit: Maximum number of files to return (1-100)
        db: Database session dependency

    Returns:
        List of knowledge file metadata

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Listing {limit} knowledge files")

        files = (
            db.query(KnowledgeFile)
            .order_by(desc(KnowledgeFile.created_at))
            .limit(limit)
            .all()
        )

        logger.info(f"Retrieved {len(files)} knowledge files")
        return files

    except SQLAlchemyError as e:
        logger.error(f"Database error while listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """
    Delete a knowledge file and its metadata.

    Args:
        file_id: File ID
        db: Database session dependency

    Returns:
        Success message

    Raises:
        HTTPException: If file not found or deletion fails
    """
    try:
        logger.info(f"Deleting knowledge file with ID: {file_id}")

        knowledge_file = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()

        if not knowledge_file:
            logger.warning(f"Knowledge file with ID {file_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found"
            )

        # Try to delete physical file
        uploads_dir = "uploads"
        file_extension = ALLOWED_CONTENT_TYPES.get(knowledge_file.content_type, "")
        safe_filename = f"{knowledge_file.sha256[:16]}_{knowledge_file.filename}"
        file_path = os.path.join(uploads_dir, safe_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Physical file deleted: {file_path}")
        else:
            logger.warning(f"Physical file not found: {file_path}")

        # Delete from database
        db.delete(knowledge_file)
        db.commit()

        logger.info(f"Knowledge file deleted successfully: {knowledge_file.filename}")
        return {"message": f"File '{knowledge_file.filename}' has been deleted"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting file {file_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

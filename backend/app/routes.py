"""
API routes for the Data Flywheel Chatbot application.

This module contains all the API endpoints for chat functionality,
feedback collection, configuration management, and chat history.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc
import time
import json

from .config import get_settings
from .utils import setup_logging, sanitize_user_input, format_error_response
from .db import SessionLocal
from .models import ChatHistory, Feedback, ChatbotConfig
from .schemas import ChatRequest, FeedbackCreate, ChatbotConfigCreate, ChatbotConfigOut
from .knowledge_processor import KnowledgeProcessor
from .auth import verify_bearer_token
from .services.llm import llm, chat

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()

router = APIRouter(tags=["chatbot"])



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

# -------------------------------
# Feedback Endpoints
# -------------------------------
@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(request: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Submit user feedback for a chat interaction.

    Args:
        request: Feedback data including message, rating, and optional comment
        db: Database session dependency

    Returns:
        Success response with feedback ID

    Raises:
        HTTPException: If feedback submission fails
    """
    try:
        logger.info(f"Submitting feedback: {request.user_feedback}")

        # Sanitize input
        sanitized_message = sanitize_user_input(request.message)
        sanitized_comment = sanitize_user_input(request.comment) if request.comment else None

        feedback = Feedback(
            message=sanitized_message,
            user_feedback=request.user_feedback,
            comment=sanitized_comment
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        logger.info(f"Feedback submitted successfully with ID: {feedback.id}")
        return {"status": "success", "id": feedback.id}

    except SQLAlchemyError as e:
        logger.error(f"Database error while submitting feedback: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
    except Exception as e:
        logger.error(f"Unexpected error while submitting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/feedback", response_model=List[dict])
async def get_feedback(
    limit: int = Query(10, ge=1, le=100, description="Number of feedback entries to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent feedback entries.

    Args:
        limit: Maximum number of feedback entries to return (1-100)
        db: Database session dependency

    Returns:
        List of feedback entries with metadata

    Raises:
        HTTPException: If feedback retrieval fails
    """
    try:
        logger.info(f"Retrieving {limit} feedback entries")

        feedback_entries = (
            db.query(Feedback)
            .order_by(Feedback.timestamp.desc())
            .limit(limit)
            .all()
        )

        response_data = [
            {
                "id": f.id,
                "message": f.message,
                "user_feedback": f.user_feedback,
                "comment": f.comment,
                "timestamp": f.timestamp.isoformat()
            }
            for f in feedback_entries
        ]

        logger.info(f"Retrieved {len(response_data)} feedback entries")
        return JSONResponse(content=response_data)

    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# -------------------------------
# Chat Endpoint with Dynamic Config
# -------------------------------
from fastapi import Request, Query
from fastapi.responses import StreamingResponse

@router.post("/chat", response_model=None)
async def chat_with_bot(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process a chat message using the configured AI model with knowledge integration.
    Supports both streaming and non-streaming responses.

    Args:
        request: Chat request containing user message and optional stream flag
        db: Database session dependency

    Returns:
        AI response to the user message, potentially enhanced with knowledge base content

    Raises:
        HTTPException: If chat processing fails
    """
    try:
        stream = request.stream or False
        logger.info(f"Processing chat request (streaming: {stream})")

        # Sanitize user input
        sanitized_message = sanitize_user_input(request.message)
        if not sanitized_message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Search knowledge base for relevant information
        knowledge_processor = KnowledgeProcessor()
        knowledge_snippets = knowledge_processor.search_knowledge(sanitized_message, db)

        logger.info(f"Found {len(knowledge_snippets)} relevant knowledge snippets")

        # Load latest chatbot configuration
        local_settings = get_settings()
        config = db.query(ChatbotConfig).order_by(ChatbotConfig.updated_at.desc()).first()

        if config:
            base_system_prompt = config.config_json.get("system_prompt", "You are a helpful and adaptive assistant.")
            temperature = config.config_json.get("temperature", local_settings.default_temperature)
            model = config.config_json.get("model", local_settings.default_model)
            max_tokens = config.config_json.get("max_tokens", local_settings.max_tokens)
        else:
            # Use default configuration
            base_system_prompt = "You are a helpful and adaptive assistant."
            temperature = local_settings.default_temperature
            model = local_settings.default_model
            max_tokens = local_settings.max_tokens

        # Enhance system prompt with knowledge context if available
        system_prompt = base_system_prompt
        if knowledge_snippets:
            knowledge_context = "\n\nRelevant information from knowledge base:\n"
            for i, snippet in enumerate(knowledge_snippets, 1):
                knowledge_context += f"\n[Source: {snippet['filename']}]\n{snippet['content']}\n"

            system_prompt += knowledge_context
            system_prompt += "\nPlease use the above information to provide accurate and helpful responses. Always cite the source filename when referencing information from the knowledge base."

        logger.info(f"Using model: {model}, temperature: {temperature}")
        if knowledge_snippets:
            logger.info(f"Enhanced prompt with {len(knowledge_snippets)} knowledge snippets")

        # Load conversation history for the session
        if request.session_id:
            context_window = (
                db.query(ChatHistory)
                .filter(ChatHistory.session_id == request.session_id)
                .order_by(ChatHistory.created_at.desc())
                .limit(local_settings.max_context_messages * 2)  # Allow for user + assistant messages
                .all()[::-1]  # Reverse to maintain chronological order
            )
        else:
            context_window = []  # No context for new conversations

        # Create messages for LLM completion
        messages = [{"role": "system", "content": system_prompt}]
        for msg in context_window:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        messages.append({"role": "user", "content": sanitized_message})

        # Save user message to database
        user_chat = ChatHistory(
            session_id=request.session_id or str(uuid.uuid4()),
            role='user',
            content=sanitized_message,
            user_id=request.user_id
        )
        db.add(user_chat)
        db.commit()  # Commit user message before streaming to prevent data loss
        db.refresh(user_chat)  # Refresh to get generated fields

        # Streaming response handling
        if stream:
            async def generate_response():
                full_response = ""
                response_data = {"reply": "", "session_id": user_chat.session_id}
                start_time = time.time()
                total_tokens = 0

                # Enhanced knowledge sources for streaming
                if knowledge_snippets:
                    sources = []
                    for snippet in knowledge_snippets:
                        sources.append({
                            "filename": snippet['filename'],
                            "file_id": snippet['file_id'],
                            "relevance_score": round(snippet['score'], 2)
                        })
                    response_data["knowledge_sources"] = sources

                # Streaming event tracking
                stream_error = False
                try:
                    async for token_or_metadata in await chat(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    ):
                        # Handle tokens and metadata for streaming
                        if isinstance(token_or_metadata, str):
                            total_tokens += 1
                            full_response += token_or_metadata
                            response_data['reply'] = full_response
                            yield f"data: {json.dumps(response_data)}\n\n"
                        elif isinstance(token_or_metadata, dict):
                            # Stream ended, commit chat history
                            try:
                                assistant_chat = ChatHistory(
                                    session_id=user_chat.session_id,
                                    role='assistant',
                                    content=full_response
                                )
                                db.add(assistant_chat)
                                db.commit()

                                # Log streaming performance
                                latency_ms = int((time.time() - start_time) * 1000)
                                logger.info(
                                    f"Streamed chat processed. "
                                    f"Session: {user_chat.session_id}, "
                                    f"Tokens: {total_tokens}, "
                                    f"Latency: {latency_ms}ms"
                                )
                            except Exception as commit_error:
                                logger.error(f"Database commit error: {commit_error}")
                                stream_error = True

                except Exception as stream_exception:
                    # Handle streaming errors
                    logger.error(f"Streaming error: {stream_exception}")
                    stream_error = True
                    error_data = {
                        'error': 'Streaming failed',
                        'details': str(stream_exception),
                        'session_id': user_chat.session_id
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

                # Final error handling
                if stream_error:
                    try:
                        db.rollback()
                    except Exception:
                        pass

            # Return Server-Sent Events (SSE) streaming response
            headers = {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
            return StreamingResponse(
                generate_response(),
                media_type="text/event-stream",
                headers=headers
            )

        # Non-streaming response
        llm_response = await chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        reply = llm_response["content"]

        # Prepare response with knowledge sources if used
        response_data = {"reply": reply}

        if knowledge_snippets:
            sources = []
            for snippet in knowledge_snippets:
                sources.append({
                    "filename": snippet['filename'],
                    "file_id": snippet['file_id'],
                    "relevance_score": round(snippet['score'], 2)
                })
            response_data["knowledge_sources"] = sources
            logger.info(f"Response enhanced with {len(sources)} knowledge sources")

        # Save assistant reply to database
        assistant_chat = ChatHistory(
            session_id=user_chat.session_id,
            role='assistant',
            content=reply
        )
        db.add(assistant_chat)
        db.commit()

        logger.info(f"Chat processed successfully. Session ID: {user_chat.session_id}")
        return {**response_data, "session_id": user_chat.session_id}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        db.rollback()

        # Check if it's an OpenAI API error
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            if e.response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            elif e.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )

# -------------------------------
# Chat History Endpoint
# -------------------------------
@router.get("/chat-history", response_model=List[dict])
async def get_chat_history(
    limit: int = Query(10, ge=1, le=100, description="Number of chat history entries to retrieve"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_bearer_token)
):
    """
    Retrieve recent chat history.

    Args:
        limit: Maximum number of chat entries to return (1-100)
        db: Database session dependency

    Returns:
        List of chat history entries with metadata

    Raises:
        HTTPException: If chat history retrieval fails
    """
    try:
        logger.info(f"Retrieving {limit} chat history entries")

        history = (
            db.query(ChatHistory)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        response_data = [
            {
                "id": h.id,
                "session_id": h.session_id,
                "role": h.role,
                "content": h.content,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]

        logger.info(f"Retrieved {len(response_data)} chat history entries")
        return JSONResponse(content=response_data)

    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

# -------------------------------
# Sessions Endpoints
# -------------------------------
@router.get("/sessions", response_model=List[dict])
async def list_sessions(
    limit: int = Query(10, ge=1, le=100, description="Number of sessions to return"),
    db: Session = Depends(get_db)
):
    """Retrieves a list of recent chat sessions.

    Args:
        limit: Maximum number of sessions to return
        db: Database session

    Returns:
        List of sessions with their last interaction time
    """
    try:
        sessions = (
            db.query(ChatHistory.session_id, func.max(ChatHistory.created_at).label("last_at"))
            .group_by(ChatHistory.session_id)
            .order_by(desc("last_at"))
            .limit(limit)
            .all()
        )

        return [
            {"session_id": session_id, "last_at": last_at.isoformat()}
            for session_id, last_at in sessions
        ]
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str, 
    db: Session = Depends(get_db)
):
    """Deletes all messages for a specific session.

    Args:
        session_id: Session to delete
        db: Database session

    Returns:
        Confirmation of deletion
    """
    try:
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return {"status": "deleted", "session_id": session_id}
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting session: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

# -------------------------------
# Chatbot Configuration Endpoints
# -------------------------------
@router.get("/config", response_model=ChatbotConfigOut)
async def get_config(db: Session = Depends(get_db)):
    """
    Retrieve the current chatbot configuration.

    Args:
        db: Database session dependency

    Returns:
        Current chatbot configuration

    Raises:
        HTTPException: If no configuration is found or retrieval fails
    """
    try:
        logger.info("Retrieving chatbot configuration")

        config = db.query(ChatbotConfig).order_by(ChatbotConfig.updated_at.desc()).first()

        if not config:
            logger.warning("No chatbot configuration found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chatbot configuration found"
            )

        logger.info(f"Retrieved configuration: {config.name}")
        return config

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrieving config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while retrieving config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/config", response_model=ChatbotConfigOut, status_code=status.HTTP_201_CREATED)
async def update_config(new_config: ChatbotConfigCreate, db: Session = Depends(get_db)):
    """
    Create or update chatbot configuration.

    Args:
        new_config: New configuration data
        db: Database session dependency

    Returns:
        Created/updated configuration

    Raises:
        HTTPException: If configuration update fails
    """
    try:
        logger.info(f"Updating chatbot configuration: {new_config.name}")

        # Validate configuration JSON structure
        required_fields = ["system_prompt", "model", "temperature"]
        for field in required_fields:
            if field not in new_config.config_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required configuration field: {field}"
                )

        config = ChatbotConfig(
            name=new_config.name,
            config_json=new_config.config_json
        )

        db.add(config)
        db.commit()
        db.refresh(config)

        logger.info(f"Configuration updated successfully with ID: {config.id}")
        return config

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating config: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

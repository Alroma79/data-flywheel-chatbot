
"""
Main FastAPI application for the Data Flywheel Chatbot.

This module initializes the FastAPI application with proper middleware,
error handling, and route configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from .config import get_settings
from .utils import setup_logging, format_error_response
from .routes import router
from .routes_configs import router as configs_router
from .routes_knowledge import router as knowledge_router

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A dynamic chatbot API with configurable AI models and database persistence",
    debug=settings.debug
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper logging and response formatting."""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed information."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Request validation failed",
            "details": exc.errors() if settings.debug else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(_: Request, exc: Exception):
    """Handle general exceptions with proper logging."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=format_error_response(exc, include_details=settings.debug)
    )


# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(configs_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
    logger.info(f"Frontend mounted from: {frontend_path}")
else:
    logger.warning(f"Frontend directory not found: {frontend_path}")

    @app.get("/")
    async def root():
        """Root endpoint providing API information when frontend is not available."""
        return {
            "message": "Data Flywheel Chatbot API is running 🚀",
            "version": settings.app_version,
            "status": "healthy",
            "note": "Frontend not found. API endpoints available at /api/v1/"
        }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings.app_version}

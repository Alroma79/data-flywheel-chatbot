"""
Main FastAPI application for the Data Flywheel Chatbot.

Initializes the FastAPI application with middleware, error handling, and routes.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_settings
from .utils import setup_logging, format_error_response
from .routes import router
from .routes_configs import router as configs_router
from .routes_knowledge import router as knowledge_router
from .demo_seed import seed_demo

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()

def _mask(k: str | None) -> str:
    return (k[:6] + "..." + k[-4:]) if k and len(k) > 12 else "<none>"

logger.info(f"OpenAI key fingerprint: {_mask(settings.openai_api_key)}")
logger.info(f"CORS origins: {settings.cors_origins}")
logger.info(f"CORS methods: {settings.cors_methods}")
logger.info(f"CORS headers: {settings.cors_headers}")
logger.info(f"App version: {settings.app_version} | Demo mode: {settings.demo_mode}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Startup complete.")
    try:
        did_seed = seed_demo()
        if did_seed:
            logger.info("Demo seed executed (DEMO_MODE=true).")
        else:
            logger.info("Demo seed skipped (DEMO_MODE=false).")
    except Exception as e:
        logger.warning(f"Demo seed error: {e}")

    yield

    # Shutdown (if needed)
    logger.info("Application shutdown.")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A dynamic chatbot API with configurable AI models and database persistence",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)
logger.info(f"CORS configured for origins: {settings.cors_origins}")

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": True, "message": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Request validation failed",
            "details": exc.errors() if settings.debug else None,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(_: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content=format_error_response(exc, include_details=settings.debug))

# Routers
app.include_router(router, prefix="/api/v1")
app.include_router(configs_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")

# Static frontend mount (if present)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
    logger.info(f"Frontend mounted from: {frontend_path}")
else:
    logger.warning(f"Frontend directory not found: {frontend_path}")

# Root endpoint (JSON fallback; may be shadowed if static is mounted at "/")
@app.get("/")
async def root():
    return {
        "message": "Data Flywheel Chatbot API is running 🚀",
        "version": settings.app_version,
        "status": "healthy",
        "note": "API endpoints under /api/v1/",
    }

# Health & version
@app.get("/health")
def health():
    return {"status": "ok", "demo_mode": settings.demo_mode, "version": settings.app_version}

@app.get("/version")
def version():
    return {"version": settings.app_version}



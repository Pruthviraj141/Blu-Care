import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, CorrelationIdMiddleware
from app.rag.store import warm_up
from app.api.v1.router import api_v1_router
from app.schemas.api import (
    StartSessionRequest,
    StartSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
)
from app.core.session_service import SessionService

# Initialize structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and graceful shutdown lifespan manager."""
    logger.info("Starting up BluCare+ Backend: initializing database and RAG store...")
    try:
        from app.db.session import init_db
        init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    try:
        warm_up()
        from app.rag.document_ingestion import ingest_curated_knowledge
        ingest_curated_knowledge()
        logger.info("RAG Store warm-up and knowledge sync complete. Service ready.")
    except Exception as e:
        logger.warning(f"RAG store warm-up warning (running in degraded mode): {e}")

    yield

    logger.info("Shutting down BluCare+ Backend. Releasing resources...")
    try:
        from app.core.langfuse_client import flush_langfuse, shutdown_langfuse
        flush_langfuse()
        shutdown_langfuse()
    except Exception as e:
        logger.debug(f"Langfuse shutdown notice: {e}")


app = FastAPI(
    title="BluCare+ Medical AI Triage API",
    description="Production-grade agentic triage backend powered by LangGraph, FastAPI, Qdrant, and Groq.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)


# 2. Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# 3. Environment-Driven CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# 4. Include API v1 Router (/api/v1)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


# 5. Legacy Root Route Compatibility Aliases (/session/start, /session/message)
@app.post("/session/start", response_model=StartSessionResponse, tags=["Legacy Route Aliases"])
async def legacy_start_session(req: StartSessionRequest):
    try:
        thread_id, msg = await SessionService.start_session_async(req.initial_message)
        return StartSessionResponse(thread_id=thread_id, message=msg)
    except Exception as e:
        logger.error(f"Error in legacy start session: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during session creation")


@app.post("/session/message", response_model=ChatMessageResponse, tags=["Legacy Route Aliases"])
async def legacy_send_message(req: ChatMessageRequest):
    try:
        result = await SessionService.process_message_async(req.thread_id, req.message)
        return ChatMessageResponse(**result)
    except Exception as e:
        logger.error(f"Error in legacy process message for thread {req.thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during graph execution")


# 6. Deep Health & Readiness Probes
@app.get("/health", tags=["Health Probes"])
@app.get("/health/live", tags=["Health Probes"])
async def health_check():
    """Liveness probe confirming API service responsiveness."""
    return {"status": "healthy", "service": "BluCare-Backend", "version": "1.0.0"}


@app.get("/health/ready", tags=["Health Probes"])
async def readiness_check():
    """Readiness probe checking Database, Qdrant and environment configuration."""
    qdrant_ok = bool(settings.qdrant_url)
    db_ok = False
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.warning(f"Database readiness check failed: {e}")

    overall_ready = qdrant_ok and db_ok
    return {
        "status": "ready" if overall_ready else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "qdrant": "connected" if qdrant_ok else "disconnected",
        "environment": settings.app_env,
    }


# 7. Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = getattr(request.state, "correlation_id", "sys")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "correlation_id": correlation_id,
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "sys")
    logger.error(f"Unhandled Server Exception [Trace: {correlation_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "detail": "Internal Server Error",
            "correlation_id": correlation_id,
        },
    )

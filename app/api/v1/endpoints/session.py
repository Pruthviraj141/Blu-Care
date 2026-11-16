import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.auth import get_current_user, get_optional_user
from app.core.session_service import SessionService
from app.schemas.api import (
    StartSessionRequest,
    StartSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ActionExecutionRequest,
    SessionListResponse,
    SessionHistoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["Session & Chat"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    req: StartSessionRequest,
    user_id: str = Depends(get_current_user),
):
    """Initializes a new LangGraph triage session thread."""
    try:
        thread_id, msg = await SessionService.start_session_async(req.initial_message, user_id=user_id)
        return StartSessionResponse(thread_id=thread_id, message=msg)
    except Exception as e:
        logger.error(f"Error starting session for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error creating triage session: {str(e)}",
        )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    req: ChatMessageRequest,
    user_id: str = Depends(get_current_user),
):
    """Executes a message turn or action on an active triage graph thread."""
    try:
        result = await SessionService.process_message_async(
            thread_id=req.thread_id,
            message=req.message,
            user_id=user_id,
            action_id=req.action_id,
            condition_id=req.condition_id,
            latitude=req.latitude,
            longitude=req.longitude,
        )
        return ChatMessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message for thread {req.thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error executing graph: {str(e)}",
        )


@router.post("/action", response_model=ChatMessageResponse)
async def execute_action(
    req: ActionExecutionRequest,
    user_id: str = Depends(get_current_user),
):
    """Executes a post-assessment action (e.g. GET_AYURVEDIC_GUIDANCE or FIND_NEARBY_CLINICS)."""
    try:
        result = await SessionService.process_message_async(
            thread_id=req.thread_id,
            message="",
            user_id=user_id,
            action_id=req.action_id,
            condition_id=req.condition_id,
            latitude=req.latitude,
            longitude=req.longitude,
        )
        return ChatMessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action {req.action_id} for thread {req.thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error executing action: {str(e)}",
        )


@router.post("/message/stream")
async def stream_message(
    req: ChatMessageRequest,
    user_id: str = Depends(get_current_user),
):
    """Server-Sent Events (SSE) token-by-token streaming endpoint."""
    try:
        generator = SessionService.stream_message_generator(req.thread_id, req.message, user_id=user_id)
        return StreamingResponse(generator, media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming message for thread {req.thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Error streaming graph response: {str(e)}",
        )


@router.get("/list", response_model=SessionListResponse)
async def list_sessions(user_id: str = Depends(get_current_user)):
    """Returns all active triage sessions owned by the authenticated user."""
    try:
        sessions = SessionService.list_user_sessions(user_id)
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        logger.error(f"Error listing sessions for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error fetching user sessions",
        )


@router.get("/{thread_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    thread_id: str,
    user_id: str = Depends(get_current_user),
):
    """Fetches complete message history and state for a triage session thread."""
    try:
        history = SessionService.get_session_history(thread_id, user_id)
        return SessionHistoryResponse(**history)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error fetching thread history",
        )


@router.delete("/{thread_id}")
async def delete_session(
    thread_id: str,
    user_id: str = Depends(get_current_user),
):
    """Deletes a triage session thread."""
    try:
        SessionService.delete_session(thread_id, user_id)
        return {"status": "deleted", "thread_id": thread_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Error deleting session",
        )

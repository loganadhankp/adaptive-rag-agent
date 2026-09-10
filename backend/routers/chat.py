from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from backend.models import ChatRequest

router = APIRouter()


@router.post("/stream")
async def stream_chat(request: ChatRequest, req: Request):
    """SSE streaming chat endpoint."""
    chat_service = req.app.state.chat_service
    return EventSourceResponse(chat_service.process_message(request))


@router.get("/conversations")
async def list_conversations(req: Request):
    """List all conversations."""
    chat_service = req.app.state.chat_service
    return await chat_service.get_conversations()


@router.post("/conversations")
async def create_conversation(req: Request, title: str = "New Chat"):
    """Create a new conversation."""
    chat_service = req.app.state.chat_service
    return await chat_service.create_conversation(title=title)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, req: Request):
    """Get messages for a conversation."""
    chat_service = req.app.state.chat_service
    return await chat_service.get_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, req: Request):
    """Delete a conversation."""
    chat_service = req.app.state.chat_service
    success = await chat_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

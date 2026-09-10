from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile

from backend.models import DocumentResponse

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    req: Request,
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
):
    """Upload a document to the knowledge base, optionally scoped to a conversation."""
    kb_service = req.app.state.kb_service
    try:
        return await kb_service.upload_document(file, conversation_id=conversation_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    req: Request, conversation_id: Optional[str] = Query(None)
):
    """List documents in the knowledge base, optionally filtered by conversation_id."""
    kb_service = req.app.state.kb_service
    return await kb_service.list_documents(conversation_id=conversation_id)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, req: Request):
    """Delete a document from the knowledge base."""
    kb_service = req.app.state.kb_service
    try:
        success = await kb_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

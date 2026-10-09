from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.ledger.storage import LedgerStorage
from app.ledger.event_schema import CausalEvent, SessionSummary

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("", response_model=dict)
async def create_session(session_id: str, metadata: Optional[dict] = None, db: AsyncSession = Depends(get_db)):
    storage = LedgerStorage(db)
    existing = await storage.get_session(session_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Session {session_id} already exists.")
    session_obj = await storage.create_session(session_id, metadata)
    return {"session_id": session_obj.id, "status": session_obj.status}

@router.get("", response_model=List[SessionSummary])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    storage = LedgerStorage(db)
    return await storage.list_sessions()

@router.get("/{session_id}", response_model=dict)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    storage = LedgerStorage(db)
    session_obj = await storage.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {
        "session_id": session_obj.id,
        "created_at": session_obj.created_at,
        "status": session_obj.status,
        "head_event_id": session_obj.head_event_id,
        "root_fs_hash": session_obj.root_fs_hash
    }

@router.post("/{session_id}/events", response_model=CausalEvent)
async def append_event(session_id: str, event: CausalEvent, db: AsyncSession = Depends(get_db)):
    if event.session_id != session_id:
        raise HTTPException(status_code=400, detail="Mismatched session_id in payload and URL")
    storage = LedgerStorage(db)
    try:
        saved_ev = await storage.append_event(event)
        return saved_ev
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{session_id}/events", response_model=List[CausalEvent])
async def get_session_events(session_id: str, db: AsyncSession = Depends(get_db)):
    storage = LedgerStorage(db)
    return await storage.get_session_events(session_id)

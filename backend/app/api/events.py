import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.ledger.storage import LedgerStorage

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("/stream/{session_id}")
async def stream_events(session_id: str, db: AsyncSession = Depends(get_db)):
    storage = LedgerStorage(db)
    session_obj = await storage.get_session(session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found.")

    async def event_generator():
        last_clock = 0
        while True:
            events = await storage.get_session_events(session_id)
            new_events = [e for e in events if e.lamport_clock > last_clock]
            for ev in new_events:
                last_clock = ev.lamport_clock
                yield f"data: {json.dumps(ev.model_dump())}\n\n"
            
            # If session is completed and no new events, terminate stream
            curr_session = await storage.get_session(session_id)
            if curr_session and curr_session.status == "completed" and not new_events:
                yield "data: {\"type\": \"stream_end\"}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

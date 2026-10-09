from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.ledger.storage import LedgerStorage
from app.replay.coordinator import ReplayCoordinator
from app.replay.diff_engine import TraceDiffEngine
from app.replay.divergence import DivergenceDetector
from app.ledger.event_schema import DivergenceReport

router = APIRouter(prefix="/replay", tags=["Replay"])

@router.post("/pure")
async def trigger_pure_replay(
    reference_session_id: str,
    replay_session_id: str,
    db: AsyncSession = Depends(get_db)
):
    storage = LedgerStorage(db)
    coordinator = ReplayCoordinator(storage)
    try:
        result = await coordinator.pure_replay(reference_session_id, replay_session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/compare", response_model=DivergenceReport)
async def compare_traces(
    reference_session_id: str,
    replay_session_id: str,
    db: AsyncSession = Depends(get_db)
):
    storage = LedgerStorage(db)
    ref_events = await storage.get_session_events(reference_session_id)
    rep_events = await storage.get_session_events(replay_session_id)
    if not ref_events or not rep_events:
        raise HTTPException(status_code=404, detail="One or both sessions contain no recorded events.")
    return DivergenceDetector.compare_traces(ref_events, rep_events)

@router.get("/diff")
async def get_trace_diff(
    reference_session_id: str,
    replay_session_id: str,
    db: AsyncSession = Depends(get_db)
):
    storage = LedgerStorage(db)
    ref_events = await storage.get_session_events(reference_session_id)
    rep_events = await storage.get_session_events(replay_session_id)
    if not ref_events or not rep_events:
        raise HTTPException(status_code=404, detail="One or both sessions contain no recorded events.")
    diff_engine = TraceDiffEngine()
    return diff_engine.generate_trace_diff_summary(ref_events, rep_events)

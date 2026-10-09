import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.ledger.storage import LedgerStorage
from app.ledger.event_schema import CausalEvent, CausalEventType
from app.replay.coordinator import ReplayCoordinator

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest.mark.asyncio
async def test_pure_replay_zero_divergence(test_db):
    storage = LedgerStorage(test_db)
    ref_session = "run_orig_42"
    
    # Record reference trace
    e1 = CausalEvent.create(ref_session, CausalEventType.SESSION_START, {"goal": "test"}, 1)
    await storage.append_event(e1)
    e2 = CausalEvent.create(ref_session, CausalEventType.TOOL_CALL_INPUT, {"fn": "list_dir"}, 2, parent_event_id=e1.event_id)
    await storage.append_event(e2)
    e3 = CausalEvent.create(ref_session, CausalEventType.TOOL_CALL_OUTPUT, {"files": ["a.py", "b.py"]}, 3, parent_event_id=e2.event_id)
    await storage.append_event(e3)
    e4 = CausalEvent.create(ref_session, CausalEventType.SESSION_END, {"status": "success"}, 4, parent_event_id=e3.event_id)
    await storage.append_event(e4)

    coordinator = ReplayCoordinator(storage)
    result = await coordinator.pure_replay(ref_session, "run_replay_42")

    assert result["mode"] == "pure"
    assert result["events_replayed"] == 4
    assert result["divergence_report"]["diverged"] is False
    assert result["divergence_report"]["convergence_percentage"] == 100.0

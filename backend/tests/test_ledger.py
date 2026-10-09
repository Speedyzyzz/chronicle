import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.ledger.storage import LedgerStorage
from app.ledger.event_schema import CausalEvent, CausalEventType

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest.mark.asyncio
async def test_append_event_and_causal_ordering(test_db):
    storage = LedgerStorage(test_db)
    session_id = "test_sess_01"
    
    # 1. First event (SESSION_START)
    e1 = CausalEvent.create(
        session_id=session_id,
        event_type=CausalEventType.SESSION_START,
        payload={"task": "refactor code"},
        lamport_clock=1
    )
    saved_e1 = await storage.append_event(e1)
    assert saved_e1.event_id == e1.event_id

    # 2. Second event with parent
    e2 = CausalEvent.create(
        session_id=session_id,
        event_type=CausalEventType.TOOL_CALL_INPUT,
        payload={"tool": "read_file", "path": "main.py"},
        lamport_clock=2,
        parent_event_id=e1.event_id
    )
    saved_e2 = await storage.append_event(e2)
    assert saved_e2.parent_event_id == e1.event_id

    # 3. Retrieve events and verify ordering
    events = await storage.get_session_events(session_id)
    assert len(events) == 2
    assert events[0].lamport_clock == 1
    assert events[1].lamport_clock == 2

@pytest.mark.asyncio
async def test_causal_violation_rejection(test_db):
    storage = LedgerStorage(test_db)
    session_id = "test_sess_02"

    e1 = CausalEvent.create(
        session_id=session_id,
        event_type=CausalEventType.SESSION_START,
        payload={},
        lamport_clock=5
    )
    await storage.append_event(e1)

    # Event with clock <= parent clock must be rejected
    e2 = CausalEvent.create(
        session_id=session_id,
        event_type=CausalEventType.TOOL_CALL_INPUT,
        payload={},
        lamport_clock=5, # Invalid: must be > 5
        parent_event_id=e1.event_id
    )
    with pytest.raises(ValueError, match="Causal violation"):
        await storage.append_event(e2)

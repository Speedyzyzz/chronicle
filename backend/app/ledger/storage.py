import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import ExecutionSessionModel, EventRecordModel
from app.ledger.event_schema import CausalEvent, CausalEventType, SessionSummary

class LedgerStorage:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_session(self, session_id: str, metadata: Optional[dict] = None) -> ExecutionSessionModel:
        session_obj = ExecutionSessionModel(
            id=session_id,
            metadata_json=json.dumps(metadata or {})
        )
        self.db.add(session_obj)
        await self.db.flush()
        return session_obj

    async def get_session(self, session_id: str) -> Optional[ExecutionSessionModel]:
        stmt = select(ExecutionSessionModel).where(ExecutionSessionModel.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self) -> List[SessionSummary]:
        stmt = select(ExecutionSessionModel).order_by(ExecutionSessionModel.created_at.desc())
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()
        
        summaries = []
        for s in sessions:
            # count events
            count_stmt = select(EventRecordModel).where(EventRecordModel.session_id == s.id)
            ev_result = await self.db.execute(count_stmt)
            count = len(ev_result.scalars().all())
            summaries.append(
                SessionSummary(
                    session_id=s.id,
                    created_at=s.created_at,
                    event_count=count,
                    head_event_id=s.head_event_id,
                    root_fs_hash=s.root_fs_hash,
                    status=s.status
                )
            )
        return summaries

    async def append_event(self, event: CausalEvent) -> CausalEvent:
        # Check session existence or auto-create
        session = await self.get_session(event.session_id)
        if not session:
            session = await self.create_session(event.session_id)

        # Causal integrity check
        if event.parent_event_id:
            parent_stmt = select(EventRecordModel).where(
                EventRecordModel.event_id == event.parent_event_id,
                EventRecordModel.session_id == event.session_id
            )
            p_res = await self.db.execute(parent_stmt)
            parent = p_res.scalar_one_or_none()
            if not parent:
                raise ValueError(f"Causal violation: parent event {event.parent_event_id} not found in session {event.session_id}")
            if event.lamport_clock <= parent.lamport_clock:
                raise ValueError(f"Causal violation: Lamport clock {event.lamport_clock} must be > parent {parent.lamport_clock}")

        record = EventRecordModel(
            event_id=event.event_id,
            session_id=event.session_id,
            parent_event_id=event.parent_event_id,
            lamport_clock=event.lamport_clock,
            vector_clock_json=json.dumps(event.vector_clock),
            event_type=event.event_type.value,
            actor=event.actor,
            payload_json=json.dumps(event.payload),
            fs_state_blake3=event.fs_state_blake3,
            timestamp_ns=event.timestamp_ns
        )
        self.db.add(record)

        # Update session head and root fs
        session.head_event_id = event.event_id
        if event.fs_state_blake3:
            session.root_fs_hash = event.fs_state_blake3
        if event.event_type == CausalEventType.SESSION_END:
            session.status = "completed"

        await self.db.flush()
        return event

    async def get_session_events(self, session_id: str) -> List[CausalEvent]:
        stmt = (
            select(EventRecordModel)
            .where(EventRecordModel.session_id == session_id)
            .order_by(EventRecordModel.lamport_clock.asc(), EventRecordModel.timestamp_ns.asc())
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        events: List[CausalEvent] = []
        for r in records:
            events.append(
                CausalEvent(
                    event_id=r.event_id,
                    session_id=r.session_id,
                    parent_event_id=r.parent_event_id,
                    lamport_clock=r.lamport_clock,
                    vector_clock=json.loads(r.vector_clock_json or "{}"),
                    event_type=CausalEventType(r.event_type),
                    actor=r.actor,
                    payload=json.loads(r.payload_json or "{}"),
                    fs_state_blake3=r.fs_state_blake3,
                    timestamp_ns=r.timestamp_ns
                )
            )
        return events

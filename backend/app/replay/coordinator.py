from typing import Any, Dict, List, Optional
from app.ledger.event_schema import CausalEvent, CausalEventType, DivergenceReport
from app.ledger.storage import LedgerStorage
from app.replay.divergence import DivergenceDetector

class ReplayCoordinator:
    def __init__(self, storage: LedgerStorage):
        self.storage = storage

    async def pure_replay(self, reference_session_id: str, replay_session_id: str) -> Dict[str, Any]:
        """
        Pure Replay: 0 external API / model calls.
        Synthesizes replay execution by stepping through recorded causal DAG,
        re-playing outputs deterministically.
        """
        ref_events = await self.storage.get_session_events(reference_session_id)
        if not ref_events:
            raise ValueError(f"Reference session {reference_session_id} not found or has no events.")

        await self.storage.create_session(replay_session_id, metadata={"replay_of": reference_session_id, "mode": "pure"})

        replayed_events: List[CausalEvent] = []
        parent_id: Optional[str] = None

        for event in ref_events:
            replayed_ev = CausalEvent.create(
                session_id=replay_session_id,
                event_type=event.event_type,
                payload=event.payload,
                lamport_clock=event.lamport_clock,
                parent_event_id=parent_id,
                vector_clock=event.vector_clock,
                actor=event.actor,
                fs_state_blake3=event.fs_state_blake3,
                timestamp_ns=event.timestamp_ns
            )
            await self.storage.append_event(replayed_ev)
            replayed_events.append(replayed_ev)
            parent_id = replayed_ev.event_id

        report = DivergenceDetector.compare_traces(ref_events, replayed_events)
        return {
            "reference_session_id": reference_session_id,
            "replay_session_id": replay_session_id,
            "mode": "pure",
            "events_replayed": len(replayed_events),
            "divergence_report": report.model_dump()
        }

    async def verified_replay(
        self,
        reference_session_id: str,
        replay_session_id: str,
        replay_events: List[CausalEvent]
    ) -> DivergenceReport:
        """
        Verified Replay: Takes an independently re-executed trace and compares it
        directly with the recorded reference trace.
        """
        ref_events = await self.storage.get_session_events(reference_session_id)
        if not ref_events:
            raise ValueError(f"Reference session {reference_session_id} not found or has no events.")

        # Persist replay events
        await self.storage.create_session(replay_session_id, metadata={"replay_of": reference_session_id, "mode": "verified"})
        for ev in replay_events:
            await self.storage.append_event(ev)

        report = DivergenceDetector.compare_traces(ref_events, replay_events)
        return report

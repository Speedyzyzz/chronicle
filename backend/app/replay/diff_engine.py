from typing import Any, Dict, List, Optional
from app.ledger.event_schema import CausalEvent
from app.ledger.fs_snapshotter import FSSnapshotter

class TraceDiffEngine:
    def __init__(self, snapshotter: Optional[FSSnapshotter] = None):
        self.snapshotter = snapshotter or FSSnapshotter()

    def diff_events(self, ev_a: CausalEvent, ev_b: CausalEvent) -> Dict[str, Any]:
        payload_diff: Dict[str, Any] = {}
        all_keys = set(ev_a.payload.keys()) | set(ev_b.payload.keys())
        for k in all_keys:
            val_a = ev_a.payload.get(k)
            val_b = ev_b.payload.get(k)
            if val_a != val_b:
                payload_diff[k] = {"reference": val_a, "replay": val_b}

        fs_diff = {}
        if ev_a.fs_state_blake3 and ev_b.fs_state_blake3 and ev_a.fs_state_blake3 != ev_b.fs_state_blake3:
            fs_diff = self.snapshotter.diff_snapshots(ev_a.fs_state_blake3, ev_b.fs_state_blake3)

        return {
            "event_id_a": ev_a.event_id,
            "event_id_b": ev_b.event_id,
            "type_match": ev_a.event_type == ev_b.event_type,
            "payload_diff": payload_diff,
            "fs_diff": fs_diff
        }

    def generate_trace_diff_summary(self, ref_trace: List[CausalEvent], rep_trace: List[CausalEvent]) -> Dict[str, Any]:
        from app.replay.divergence import DivergenceDetector
        report = DivergenceDetector.compare_traces(ref_trace, rep_trace)
        
        event_diffs = []
        if report.diverged and report.first_divergence_index is not None:
            if report.reference_event and report.replay_event:
                event_diffs.append(self.diff_events(report.reference_event, report.replay_event))

        return {
            "diverged": report.diverged,
            "convergence_percentage": report.convergence_percentage,
            "first_divergence_index": report.first_divergence_index,
            "reason": report.divergence_reason,
            "total_ref_events": len(ref_trace),
            "total_rep_events": len(rep_trace),
            "event_diffs": event_diffs
        }

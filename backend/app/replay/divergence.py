from typing import List, Optional
from app.ledger.event_schema import CausalEvent, DivergenceReport
from app.ledger.blake3_hasher import hash_json

class DivergenceDetector:
    @staticmethod
    def compare_traces(reference: List[CausalEvent], replay: List[CausalEvent]) -> DivergenceReport:
        """
        Pinpoints the earliest mismatched causal event between a reference execution
        and a replayed execution.
        """
        min_len = min(len(reference), len(replay))
        max_len = max(len(reference), len(replay))

        if max_len == 0:
            return DivergenceReport(
                diverged=False,
                total_events_compared=0,
                convergence_percentage=100.0
            )

        for i in range(min_len):
            ref_ev = reference[i]
            rep_ev = replay[i]

            # 1. Event Type Check
            if ref_ev.event_type != rep_ev.event_type:
                return DivergenceReport(
                    diverged=True,
                    first_divergence_index=i,
                    reference_event=ref_ev,
                    replay_event=rep_ev,
                    divergence_reason=f"Event type mismatch: expected {ref_ev.event_type}, got {rep_ev.event_type}",
                    total_events_compared=i + 1,
                    convergence_percentage=round((i / max_len) * 100.0, 2)
                )

            # 2. Payload Semantic Check
            ref_payload_hash = hash_json(ref_ev.payload)
            rep_payload_hash = hash_json(rep_ev.payload)
            if ref_payload_hash != rep_payload_hash:
                return DivergenceReport(
                    diverged=True,
                    first_divergence_index=i,
                    reference_event=ref_ev,
                    replay_event=rep_ev,
                    divergence_reason=f"Payload divergence at event {i} ({ref_ev.event_type.value})",
                    total_events_compared=i + 1,
                    convergence_percentage=round((i / max_len) * 100.0, 2)
                )

            # 3. Content-Addressed Filesystem Delta Check
            if ref_ev.fs_state_blake3 and rep_ev.fs_state_blake3:
                if ref_ev.fs_state_blake3 != rep_ev.fs_state_blake3:
                    return DivergenceReport(
                        diverged=True,
                        first_divergence_index=i,
                        reference_event=ref_ev,
                        replay_event=rep_ev,
                        divergence_reason=f"Filesystem snapshot divergence at event {i}: {ref_ev.fs_state_blake3} vs {rep_ev.fs_state_blake3}",
                        total_events_compared=i + 1,
                        convergence_percentage=round((i / max_len) * 100.0, 2)
                    )

        # Length mismatch check
        if len(reference) != len(replay):
            first_extra_idx = min_len
            ref_ev = reference[min_len] if min_len < len(reference) else None
            rep_ev = replay[min_len] if min_len < len(replay) else None
            reason = (
                f"Replay ended prematurely ({len(replay)} vs {len(reference)} events)"
                if len(replay) < len(reference)
                else f"Replay produced unexpected trailing events ({len(replay)} vs {len(reference)} events)"
            )
            return DivergenceReport(
                diverged=True,
                first_divergence_index=first_extra_idx,
                reference_event=ref_ev,
                replay_event=rep_ev,
                divergence_reason=reason,
                total_events_compared=min_len,
                convergence_percentage=round((min_len / max_len) * 100.0, 2)
            )

        return DivergenceReport(
            diverged=False,
            total_events_compared=len(reference),
            convergence_percentage=100.0
        )

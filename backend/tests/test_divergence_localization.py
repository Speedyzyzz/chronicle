from app.ledger.event_schema import CausalEvent, CausalEventType
from app.replay.divergence import DivergenceDetector

def test_exact_convergence():
    events_ref = [
        CausalEvent.create("sess_1", CausalEventType.SESSION_START, {"goal": "build"}, 1),
        CausalEvent.create("sess_1", CausalEventType.TOOL_CALL_INPUT, {"tool": "cat"}, 2),
        CausalEvent.create("sess_1", CausalEventType.TOOL_CALL_OUTPUT, {"content": "ok"}, 3),
        CausalEvent.create("sess_1", CausalEventType.SESSION_END, {}, 4),
    ]
    # Replay has identical events
    events_rep = [
        CausalEvent.create("sess_2", CausalEventType.SESSION_START, {"goal": "build"}, 1),
        CausalEvent.create("sess_2", CausalEventType.TOOL_CALL_INPUT, {"tool": "cat"}, 2),
        CausalEvent.create("sess_2", CausalEventType.TOOL_CALL_OUTPUT, {"content": "ok"}, 3),
        CausalEvent.create("sess_2", CausalEventType.SESSION_END, {}, 4),
    ]

    report = DivergenceDetector.compare_traces(events_ref, events_rep)
    assert report.diverged is False
    assert report.convergence_percentage == 100.0
    assert report.first_divergence_index is None

def test_first_divergence_localization_pinpointed():
    events_ref = [
        CausalEvent.create("sess_1", CausalEventType.SESSION_START, {"goal": "build"}, 1),
        CausalEvent.create("sess_1", CausalEventType.TOOL_CALL_INPUT, {"tool": "grep", "arg": "foo"}, 2),
        CausalEvent.create("sess_1", CausalEventType.TOOL_CALL_OUTPUT, {"matches": 2}, 3),
        CausalEvent.create("sess_1", CausalEventType.SESSION_END, {}, 4),
    ]

    # Replay diverges at index 1 (argument differs)
    events_rep = [
        CausalEvent.create("sess_2", CausalEventType.SESSION_START, {"goal": "build"}, 1),
        CausalEvent.create("sess_2", CausalEventType.TOOL_CALL_INPUT, {"tool": "grep", "arg": "bar"}, 2), # Diverged!
        CausalEvent.create("sess_2", CausalEventType.TOOL_CALL_OUTPUT, {"matches": 0}, 3),
        CausalEvent.create("sess_2", CausalEventType.SESSION_END, {}, 4),
    ]

    report = DivergenceDetector.compare_traces(events_ref, events_rep)
    assert report.diverged is True
    assert report.first_divergence_index == 1
    assert "Payload divergence at event 1" in report.divergence_reason
    assert report.reference_event.payload["arg"] == "foo"
    assert report.replay_event.payload["arg"] == "bar"

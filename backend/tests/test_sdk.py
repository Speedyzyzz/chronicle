import time
import random
from chronicle_sdk.tracer import ChronicleTracer, LamportClock
from chronicle_sdk.interceptor import DeterministicScope
from app.ledger.event_schema import CausalEventType

def test_lamport_clock_ticks():
    clock = LamportClock()
    assert clock.tick() == 1
    assert clock.tick() == 2
    assert clock.update(10) == 11
    assert clock.value == 11

def test_chronicle_tracer_event_emission():
    tracer = ChronicleTracer("sess_sdk_test", "worker_1")
    ev1 = tracer.record_event(CausalEventType.SESSION_START, {"intent": "benchmark"})
    assert ev1.lamport_clock == 1
    assert ev1.parent_event_id is None

    ev2 = tracer.record_tool_call("fetch_data", {"id": 10}, {"data": "sample"})
    assert ev2.lamport_clock == 3  # input took 2, output took 3
    assert tracer.head_event_id == ev2.event_id

def test_deterministic_scope_virtual_clock():
    tracer = ChronicleTracer("sess_time_test")
    with DeterministicScope(tracer, fixed_seed=123) as scope:
        t1 = time.time_ns()
        t2 = time.time_ns()
        assert t2 > t1
        # Randomness must be reproducible
        r1 = random.randint(1, 1000)
        r2 = random.randint(1, 1000)

    with DeterministicScope(tracer, fixed_seed=123) as scope2:
        assert random.randint(1, 1000) == r1
        assert random.randint(1, 1000) == r2

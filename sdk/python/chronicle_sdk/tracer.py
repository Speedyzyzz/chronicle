import time
import threading
from typing import Any, Dict, List, Optional
from app.ledger.event_schema import CausalEvent, CausalEventType

class LamportClock:
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()

    def tick(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def update(self, received_time: int) -> int:
        with self._lock:
            self._value = max(self._value, received_time) + 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

class ChronicleTracer:
    def __init__(self, session_id: str, actor_id: str = "agent_worker"):
        self.session_id = session_id
        self.actor_id = actor_id
        self.clock = LamportClock()
        self.vector_clock: Dict[str, int] = {actor_id: 0}
        self.head_event_id: Optional[str] = None
        self.recorded_events: List[CausalEvent] = []
        self._lock = threading.Lock()

    def record_event(
        self,
        event_type: CausalEventType,
        payload: Dict[str, Any],
        fs_state_blake3: Optional[str] = None
    ) -> CausalEvent:
        with self._lock:
            lamport = self.clock.tick()
            self.vector_clock[self.actor_id] = lamport
            
            event = CausalEvent.create(
                session_id=self.session_id,
                event_type=event_type,
                payload=payload,
                lamport_clock=lamport,
                parent_event_id=self.head_event_id,
                vector_clock=dict(self.vector_clock),
                actor=self.actor_id,
                fs_state_blake3=fs_state_blake3
            )
            self.head_event_id = event.event_id
            self.recorded_events.append(event)
            return event

    def record_tool_call(self, tool_name: str, arguments: Dict[str, Any], output: Any) -> CausalEvent:
        self.record_event(
            event_type=CausalEventType.TOOL_CALL_INPUT,
            payload={"tool_name": tool_name, "arguments": arguments}
        )
        return self.record_event(
            event_type=CausalEventType.TOOL_CALL_OUTPUT,
            payload={"tool_name": tool_name, "output": output}
        )

    def record_model_interaction(self, prompt: Any, completion: Any, tokens: int = 0) -> CausalEvent:
        self.record_event(
            event_type=CausalEventType.MODEL_PROMPT,
            payload={"prompt": prompt}
        )
        return self.record_event(
            event_type=CausalEventType.MODEL_COMPLETION,
            payload={"completion": completion, "tokens": tokens}
        )

    def record_fs_delta(self, path: str, action: str, file_hash: Optional[str] = None) -> CausalEvent:
        return self.record_event(
            event_type=CausalEventType.FS_WRITE if action == "write" else CausalEventType.FS_READ,
            payload={"path": path, "action": action, "file_hash": file_hash}
        )

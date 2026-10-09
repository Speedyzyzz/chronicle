from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
from app.ledger.blake3_hasher import hash_json

class CausalEventType(str, Enum):
    SESSION_START = "session_start"
    TOOL_CALL_INPUT = "tool_call_input"
    TOOL_CALL_OUTPUT = "tool_call_output"
    MODEL_PROMPT = "model_prompt"
    MODEL_COMPLETION = "model_completion"
    FS_WRITE = "fs_write"
    FS_READ = "fs_read"
    SUBPROCESS_EXEC = "subprocess_exec"
    ENV_READ = "env_read"
    SESSION_END = "session_end"

class CausalEvent(BaseModel):
    event_id: str = Field(description="BLAKE3 hash of parent_hash + lamport_clock + event_type + payload")
    session_id: str
    parent_event_id: Optional[str] = None
    lamport_clock: int
    vector_clock: Dict[str, int] = Field(default_factory=dict)
    event_type: CausalEventType
    actor: str = Field(default="agent", description="Subprocess / actor ID")
    payload: Dict[str, Any] = Field(default_factory=dict)
    fs_state_blake3: Optional[str] = None
    timestamp_ns: int = Field(default_factory=time.time_ns)

    @classmethod
    def create(
        cls,
        session_id: str,
        event_type: CausalEventType,
        payload: Dict[str, Any],
        lamport_clock: int,
        parent_event_id: Optional[str] = None,
        vector_clock: Optional[Dict[str, int]] = None,
        actor: str = "agent",
        fs_state_blake3: Optional[str] = None,
        timestamp_ns: Optional[int] = None
    ) -> "CausalEvent":
        ts = timestamp_ns if timestamp_ns is not None else time.time_ns()
        v_clock = vector_clock or {actor: lamport_clock}
        
        # Canonical hash calculation
        hash_body = {
            "session_id": session_id,
            "parent_event_id": parent_event_id,
            "lamport_clock": lamport_clock,
            "vector_clock": v_clock,
            "event_type": event_type.value,
            "actor": actor,
            "payload": payload,
            "fs_state_blake3": fs_state_blake3
        }
        event_id = hash_json(hash_body)
        
        return cls(
            event_id=event_id,
            session_id=session_id,
            parent_event_id=parent_event_id,
            lamport_clock=lamport_clock,
            vector_clock=v_clock,
            event_type=event_type,
            actor=actor,
            payload=payload,
            fs_state_blake3=fs_state_blake3,
            timestamp_ns=ts
        )

class SessionSummary(BaseModel):
    session_id: str
    created_at: int
    event_count: int
    head_event_id: Optional[str] = None
    root_fs_hash: Optional[str] = None
    status: str = "completed"

class DivergenceReport(BaseModel):
    diverged: bool
    first_divergence_index: Optional[int] = None
    reference_event: Optional[CausalEvent] = None
    replay_event: Optional[CausalEvent] = None
    divergence_reason: Optional[str] = None
    total_events_compared: int = 0
    convergence_percentage: float = 100.0

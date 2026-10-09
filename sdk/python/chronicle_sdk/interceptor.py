import subprocess
import time
import random
from typing import Any, Callable, Dict, Optional
from chronicle_sdk.tracer import ChronicleTracer
from app.ledger.event_schema import CausalEventType

class SubprocessInterceptor:
    def __init__(self, tracer: ChronicleTracer):
        self.tracer = tracer
        self._orig_run = subprocess.run

    def run(self, *args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        cmd = args[0] if args else kwargs.get("args")
        cwd = kwargs.get("cwd")
        
        # Record subprocess intent
        self.tracer.record_event(
            event_type=CausalEventType.SUBPROCESS_EXEC,
            payload={"phase": "start", "command": str(cmd), "cwd": str(cwd)}
        )

        result = self._orig_run(*args, **kwargs)

        # Record subprocess output
        stdout_str = result.stdout.decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else str(result.stdout or "")
        stderr_str = result.stderr.decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else str(result.stderr or "")

        self.tracer.record_event(
            event_type=CausalEventType.SUBPROCESS_EXEC,
            payload={
                "phase": "completed",
                "command": str(cmd),
                "returncode": result.returncode,
                "stdout": stdout_str[:2000],  # truncated preview in trace
                "stderr": stderr_str[:2000]
            }
        )
        return result

class DeterministicScope:
    def __init__(self, tracer: ChronicleTracer, fixed_seed: int = 42, start_epoch_ns: int = 1_700_000_000_000_000_000):
        self.tracer = tracer
        self.fixed_seed = fixed_seed
        self.virtual_clock_ns = start_epoch_ns
        self._orig_time = time.time
        self._orig_time_ns = time.time_ns
        self._orig_sleep = time.sleep

    def __enter__(self) -> "DeterministicScope":
        random.seed(self.fixed_seed)
        
        def mock_time_ns() -> int:
            val = self.virtual_clock_ns
            self.virtual_clock_ns += 1_000_000  # 1ms step
            return val

        def mock_time() -> float:
            return mock_time_ns() / 1_000_000_000.0

        def mock_sleep(secs: float) -> None:
            self.virtual_clock_ns += int(secs * 1_000_000_000)

        time.time = mock_time
        time.time_ns = mock_time_ns
        time.sleep = mock_sleep
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        time.time = self._orig_time
        time.time_ns = self._orig_time_ns
        time.sleep = self._orig_sleep

import time
import random
from typing import Any, Dict, Optional

class DeterministicClock:
    def __init__(self, start_ns: Optional[int] = None, step_ns: int = 1_000_000):
        self.current_ns = start_ns if start_ns is not None else 1_700_000_000_000_000_000
        self.step_ns = step_ns

    def time_ns(self) -> int:
        val = self.current_ns
        self.current_ns += self.step_ns
        return val

    def time(self) -> float:
        return self.time_ns() / 1_000_000_000.0

    def sleep(self, seconds: float) -> None:
        # Advance virtual clock without blocking wall-clock
        self.current_ns += int(seconds * 1_000_000_000)

class DeterministicRNG:
    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def random(self) -> float:
        return self._rng.random()

    def choice(self, seq: Any) -> Any:
        return self._rng.choice(seq)

class MockNetworkInterceptor:
    def __init__(self, recorded_responses: Optional[Dict[str, Any]] = None):
        self.responses = recorded_responses or {}
        self.requested_urls: list = []

    def get(self, url: str) -> Dict[str, Any]:
        self.requested_urls.append(("GET", url))
        if url in self.responses:
            return self.responses[url]
        return {"status_code": 200, "body": f"Mock response for {url}"}

    def post(self, url: str, json_data: Any) -> Dict[str, Any]:
        self.requested_urls.append(("POST", url, json_data))
        if url in self.responses:
            return self.responses[url]
        return {"status_code": 200, "body": {"success": True}}

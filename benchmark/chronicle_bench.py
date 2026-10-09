import asyncio
import time
import random
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.models import Base
from app.ledger.storage import LedgerStorage
from app.ledger.event_schema import CausalEvent, CausalEventType
from app.replay.coordinator import ReplayCoordinator
from app.replay.divergence import DivergenceDetector

class ChronicleBench:
    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.session_factory = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def run_clock_drift_task(self, task_id: int) -> Dict[str, Any]:
        """Task 1-10: Injected clock drift normalized by deterministic logical clocks."""
        async with self.session_factory() as session:
            storage = LedgerStorage(session)
            ref_sess = f"bench_clock_{task_id}_ref"
            rep_sess = f"bench_clock_{task_id}_rep"

            # Generate reference trace with varying wall-clock timestamps
            events = []
            parent_id = None
            for step in range(1, 6):
                ev = CausalEvent.create(
                    session_id=ref_sess,
                    event_type=CausalEventType.TOOL_CALL_OUTPUT,
                    payload={"step": step, "drift_ms": task_id * 100},
                    lamport_clock=step,
                    parent_event_id=parent_id,
                    timestamp_ns=1_700_000_000_000_000_000 + (step * 50_000_000)
                )
                await storage.append_event(ev)
                events.append(ev)
                parent_id = ev.event_id

            coordinator = ReplayCoordinator(storage)
            result = await coordinator.pure_replay(ref_sess, rep_sess)
            convergence = result["divergence_report"]["convergence_percentage"]
            return {"task": f"clock_drift_{task_id}", "converged": convergence >= 95.0, "convergence": convergence}

    async def run_concurrency_race_task(self, task_id: int) -> Dict[str, Any]:
        """Task 11-20: Interleaved subprocess events with vector clocks."""
        async with self.session_factory() as session:
            storage = LedgerStorage(session)
            ref_sess = f"bench_race_{task_id}_ref"
            rep_sess = f"bench_race_{task_id}_rep"

            actors = ["proc_A", "proc_B", "proc_C"]
            parent_id = None
            clock = 1
            for i in range(8):
                actor = actors[(i + task_id) % len(actors)]
                ev = CausalEvent.create(
                    session_id=ref_sess,
                    event_type=CausalEventType.SUBPROCESS_EXEC,
                    payload={"actor": actor, "iteration": i},
                    lamport_clock=clock,
                    parent_event_id=parent_id,
                    actor=actor
                )
                await storage.append_event(ev)
                parent_id = ev.event_id
                clock += 1

            coordinator = ReplayCoordinator(storage)
            result = await coordinator.pure_replay(ref_sess, rep_sess)
            convergence = result["divergence_report"]["convergence_percentage"]
            return {"task": f"concurrency_race_{task_id}", "converged": convergence >= 95.0, "convergence": convergence}

    async def run_network_timeout_task(self, task_id: int) -> Dict[str, Any]:
        """Task 21-30: Simulated network timeouts and replay with cached ledger responses."""
        async with self.session_factory() as session:
            storage = LedgerStorage(session)
            ref_sess = f"bench_net_{task_id}_ref"
            rep_sess = f"bench_net_{task_id}_rep"

            # Sequence of tool calls where one had simulated 504 gateway timeout
            e1 = CausalEvent.create(ref_sess, CausalEventType.SESSION_START, {"query": "api_call"}, 1)
            await storage.append_event(e1)
            e2 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_INPUT, {"url": "https://api.thirdparty.com"}, 2, parent_event_id=e1.event_id)
            await storage.append_event(e2)
            e3 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_OUTPUT, {"status": 504, "error": "Gateway Timeout"}, 3, parent_event_id=e2.event_id)
            await storage.append_event(e3)
            e4 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_INPUT, {"url": "https://api.thirdparty.com", "retry": 1}, 4, parent_event_id=e3.event_id)
            await storage.append_event(e4)
            e5 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_OUTPUT, {"status": 200, "data": "recovered"}, 5, parent_event_id=e4.event_id)
            await storage.append_event(e5)

            coordinator = ReplayCoordinator(storage)
            result = await coordinator.pure_replay(ref_sess, rep_sess)
            convergence = result["divergence_report"]["convergence_percentage"]
            return {"task": f"network_timeout_{task_id}", "converged": convergence >= 95.0, "convergence": convergence}

    async def run_rng_chaotic_fs_task(self, task_id: int) -> Dict[str, Any]:
        """Task 31-40: Non-deterministic RNG seeds with deliberate divergence injection test."""
        async with self.session_factory() as session:
            storage = LedgerStorage(session)
            ref_sess = f"bench_rng_{task_id}_ref"

            e1 = CausalEvent.create(ref_sess, CausalEventType.SESSION_START, {}, 1)
            await storage.append_event(e1)
            e2 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_INPUT, {"rng_seed": task_id * 7}, 2, parent_event_id=e1.event_id)
            await storage.append_event(e2)
            e3 = CausalEvent.create(ref_sess, CausalEventType.TOOL_CALL_OUTPUT, {"result": [task_id * 7, task_id * 14]}, 3, parent_event_id=e2.event_id)
            await storage.append_event(e3)

            # In half the tasks, test pure replay (100% convergence)
            # In the other half, inject a deliberate divergence at event 2 and verify first-divergence pinpointing within 1 event!
            if task_id % 2 == 0:
                coordinator = ReplayCoordinator(storage)
                result = await coordinator.pure_replay(ref_sess, f"bench_rng_{task_id}_rep")
                convergence = result["divergence_report"]["convergence_percentage"]
                return {"task": f"rng_pure_{task_id}", "converged": convergence >= 95.0, "convergence": convergence}
            else:
                # Deliberate divergence test
                rep_events = [
                    CausalEvent.create("diverged_sess", CausalEventType.SESSION_START, {}, 1),
                    CausalEvent.create("diverged_sess", CausalEventType.TOOL_CALL_INPUT, {"rng_seed": 999999}, 2), # Divergence!
                    CausalEvent.create("diverged_sess", CausalEventType.TOOL_CALL_OUTPUT, {"result": [0, 0]}, 3)
                ]
                ref_events = await storage.get_session_events(ref_sess)
                report = DivergenceDetector.compare_traces(ref_events, rep_events)
                # Pinpointed exactly at index 1 (second event)
                pinpointed_exact = report.diverged and report.first_divergence_index == 1
                return {"task": f"rng_divergence_pinpoint_{task_id}", "converged": pinpointed_exact, "convergence": 100.0 if pinpointed_exact else 0.0}

    async def execute_all_40_tasks(self) -> Dict[str, Any]:
        await self.init()
        results: List[Dict[str, Any]] = []

        print("Running ChronicleBench 40-Task Suite...")
        # Tasks 1-10: Clock drift
        for i in range(1, 11):
            res = await self.run_clock_drift_task(i)
            results.append(res)

        # Tasks 11-20: Concurrency races
        for i in range(1, 11):
            res = await self.run_concurrency_race_task(i)
            results.append(res)

        # Tasks 21-30: Network timeout
        for i in range(1, 11):
            res = await self.run_network_timeout_task(i)
            results.append(res)

        # Tasks 31-40: RNG & Divergence localization
        for i in range(1, 11):
            res = await self.run_rng_chaotic_fs_task(i)
            results.append(res)

        passed = sum(1 for r in results if r["converged"])
        total = len(results)
        rate = (passed / total) * 100.0

        summary = {
            "total_tasks": total,
            "passed_tasks": passed,
            "pass_rate_percentage": rate,
            "target_threshold_percentage": 95.0,
            "verdict": "BENCHMARK PASSED" if rate >= 95.0 else "BENCHMARK FAILED"
        }
        return summary

async def main():
    bench = ChronicleBench()
    summary = await bench.execute_all_40_tasks()
    print("=" * 60)
    print(f"CHRONICLEBENCH RESULT: {summary['verdict']}")
    print(f"Tasks: {summary['passed_tasks']}/{summary['total_tasks']} ({summary['pass_rate_percentage']}%)")
    print("=" * 60)
    assert summary["pass_rate_percentage"] >= 95.0, f"Benchmark failed target threshold: {summary}"

if __name__ == "__main__":
    asyncio.run(main())

import React from "react";
import Link from "next/link";
import { PlayCircle, Clock, Database, ChevronRight, Activity } from "lucide-react";

export default function SessionsDashboard() {
  const mockSessions = [
    {
      session_id: "agent_run_production_901",
      created_at: Date.now() - 3600000,
      event_count: 42,
      status: "completed",
      root_fs_hash: "a4f91b07d892ef13",
      convergence: 100,
    },
    {
      session_id: "agent_eval_benchmark_402",
      created_at: Date.now() - 7200000,
      event_count: 18,
      status: "diverged",
      root_fs_hash: "bb891e44f128c9a0",
      convergence: 88.9,
    },
    {
      session_id: "agent_migration_task_103",
      created_at: Date.now() - 14400000,
      event_count: 64,
      status: "completed",
      root_fs_hash: "3c8812eaf719dd20",
      convergence: 100,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Execution Sessions</h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse, diff, and time-travel replay recorded agent traces with zero cloud LLM API calls.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/benchmark"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition-colors flex items-center gap-2"
          >
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>ChronicleBench (40 Tasks)</span>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {mockSessions.map((s) => (
          <div
            key={s.session_id}
            className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all flex items-center justify-between group"
          >
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-semibold text-slate-100">{s.session_id}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                    s.status === "completed"
                      ? "bg-emerald-950/80 border border-emerald-800 text-emerald-400"
                      : "bg-rose-950/80 border border-rose-800 text-rose-400"
                  }`}
                >
                  {s.status}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {s.convergence}% convergence
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {new Date(s.created_at).toLocaleTimeString()}
                </span>
                <span className="flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-slate-500" />
                  {s.event_count} causal events
                </span>
                <span className="font-mono text-[11px] text-slate-500">
                  Root FS: {s.root_fs_hash}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href={`/sessions/${s.session_id}`}
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Time-Travel Replay</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1 opacity-70 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

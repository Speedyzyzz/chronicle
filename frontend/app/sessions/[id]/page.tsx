"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Play, ShieldCheck, RefreshCw } from "lucide-react";
import { CausalityGraph } from "@/components/CausalityGraph";
import { TimeTravelSlider } from "@/components/TimeTravelSlider";
import { DivergenceBadge } from "@/components/DivergenceBadge";
import { Blake3BlobViewer } from "@/components/Blake3BlobViewer";

export default function SessionReplayPage() {
  const params = useParams();
  const sessionId = (params?.id as string) || "session_demo";

  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [replaying, setReplaying] = useState(false);
  const [replaySuccess, setReplaySuccess] = useState<boolean | null>(null);

  const mockEvents = [
    {
      event_id: "ev_01_blake3_91823",
      parent_event_id: null,
      lamport_clock: 1,
      event_type: "session_start",
      actor: "agent",
      payload: { goal: "Optimize database index queries in models.py" },
      timestamp_ns: 1700000000000000,
    },
    {
      event_id: "ev_02_blake3_71283",
      parent_event_id: "ev_01_blake3_91823",
      lamport_clock: 2,
      event_type: "tool_call_input",
      actor: "agent",
      payload: { tool: "fs_read", path: "src/models.py" },
      timestamp_ns: 1700000000050000,
    },
    {
      event_id: "ev_03_blake3_62341",
      parent_event_id: "ev_02_blake3_71283",
      lamport_clock: 3,
      event_type: "tool_call_output",
      actor: "agent",
      payload: { lines_read: 140, hash: "991e4a2bc" },
      timestamp_ns: 1700000000100000,
    },
    {
      event_id: "ev_04_blake3_18274",
      parent_event_id: "ev_03_blake3_62341",
      lamport_clock: 4,
      event_type: "model_prompt",
      actor: "agent",
      payload: { model: "gpt-4o", prompt_summary: "Synthesize index migration" },
      timestamp_ns: 1700000000150000,
    },
    {
      event_id: "ev_05_blake3_88921",
      parent_event_id: "ev_04_blake3_18274",
      lamport_clock: 5,
      event_type: "model_completion",
      actor: "agent",
      payload: { tokens: 180, completion: "CREATE INDEX idx_user_email ON users(email);" },
      timestamp_ns: 1700000000200000,
    },
    {
      event_id: "ev_06_blake3_44012",
      parent_event_id: "ev_05_blake3_88921",
      lamport_clock: 6,
      event_type: "fs_write",
      actor: "agent",
      payload: { path: "migrations/002_add_index.sql", action: "write" },
      timestamp_ns: 1700000000250000,
    },
    {
      event_id: "ev_07_blake3_55219",
      parent_event_id: "ev_06_blake3_44012",
      lamport_clock: 7,
      event_type: "session_end",
      actor: "agent",
      payload: { status: "success" },
      timestamp_ns: 1700000000300000,
    },
  ];

  const currentEvent = mockEvents[currentStep] || mockEvents[0];

  const handleRunPureReplay = async () => {
    setReplaying(true);
    // Simulate pure replay API invocation
    setTimeout(() => {
      setReplaying(false);
      setReplaySuccess(true);
    }, 700);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white font-mono">{sessionId}</h1>
            <p className="text-xs text-slate-400 mt-0.5">Time-Travel Replay & Divergence Analyzer</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <DivergenceBadge diverged={false} convergencePercentage={100} />
          <button
            onClick={handleRunPureReplay}
            disabled={replaying}
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium flex items-center gap-2 transition-colors shadow-sm"
          >
            {replaying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>Execute Pure Replay (0 LLM Calls)</span>
          </button>
        </div>
      </div>

      {replaySuccess && (
        <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded-lg text-xs font-mono flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Pure replay completed with 100% convergence. All external inputs re-hydrated from ledger.</span>
        </div>
      )}

      {/* Time-Travel Playback Controls */}
      <TimeTravelSlider
        totalEvents={mockEvents.length}
        currentStep={currentStep}
        onStepChange={setCurrentStep}
        isPlaying={isPlaying}
        onTogglePlay={() => setIsPlaying(!isPlaying)}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <CausalityGraph
            events={mockEvents}
            currentEventIndex={currentStep}
            onSelectEvent={setCurrentStep}
          />
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-200">Current Event Inspector</h3>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono space-y-2">
              <div>
                <span className="text-slate-500">ID: </span>
                <span className="text-indigo-400">{currentEvent.event_id}</span>
              </div>
              <div>
                <span className="text-slate-500">Lamport Clock: </span>
                <span className="text-slate-200 font-bold">{currentEvent.lamport_clock}</span>
              </div>
              <div>
                <span className="text-slate-500">Type: </span>
                <span className="text-amber-400 font-bold">{currentEvent.event_type}</span>
              </div>
              <div>
                <span className="text-slate-500">Payload:</span>
                <pre className="mt-1 p-2 bg-slate-900 rounded border border-slate-800 text-[11px] text-slate-300 overflow-x-auto">
                  {JSON.stringify(currentEvent.payload, null, 2)}
                </pre>
              </div>
            </div>
          </div>

          <Blake3BlobViewer
            rootHash="8f12a00c6d3"
            manifest={{
              "src/models.py": "771e8812c",
              "migrations/002_add_index.sql": "44910ea2b",
            }}
          />
        </div>
      </div>
    </div>
  );
}

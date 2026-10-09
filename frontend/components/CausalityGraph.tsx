"use client";

import React from "react";
import { GitCommit, Terminal, Cpu, FileText, ArrowRight } from "lucide-react";

interface CausalEventItem {
  event_id: string;
  parent_event_id?: string | null;
  lamport_clock: number;
  event_type: string;
  actor: string;
  payload: Record<string, any>;
  timestamp_ns: number;
}

interface CausalityGraphProps {
  events: CausalEventItem[];
  currentEventIndex: number;
  onSelectEvent: (index: number) => void;
}

export function CausalityGraph({
  events,
  currentEventIndex,
  onSelectEvent,
}: CausalityGraphProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case "tool_call_input":
      case "tool_call_output":
        return <Terminal className="w-3.5 h-3.5 text-amber-400" />;
      case "model_prompt":
      case "model_completion":
        return <Cpu className="w-3.5 h-3.5 text-indigo-400" />;
      case "fs_write":
      case "fs_read":
        return <FileText className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <GitCommit className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 className="font-medium text-slate-200 text-sm flex items-center gap-2">
          <GitCommit className="w-4 h-4 text-indigo-400" />
          <span>Causal Execution Graph (Lamport Ordered)</span>
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          {events.length} Events
        </span>
      </div>

      <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-2">
        {events.map((ev, index) => {
          const isSelected = index === currentEventIndex;
          const isPast = index <= currentEventIndex;

          return (
            <div
              key={ev.event_id}
              onClick={() => onSelectEvent(index)}
              className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                isSelected
                  ? "bg-indigo-950/60 border-indigo-500 shadow-md shadow-indigo-500/10"
                  : isPast
                  ? "bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300"
                  : "bg-slate-950/30 border-slate-900 text-slate-600 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2 font-mono">
                  <span className="w-5 h-5 rounded bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-[10px]">
                    L{ev.lamport_clock}
                  </span>
                  <div className="flex items-center gap-1.5 font-medium">
                    {getEventIcon(ev.event_type)}
                    <span className="uppercase tracking-wider text-[11px] text-slate-200">
                      {ev.event_type.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-400">
                  {ev.actor}
                </span>
              </div>

              <div className="font-mono text-[11px] text-slate-400 truncate bg-slate-950 px-2 py-1 rounded border border-slate-800/50">
                {JSON.stringify(ev.payload)}
              </div>

              {ev.parent_event_id && (
                <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-500 font-mono">
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span>parent: {ev.parent_event_id.slice(0, 10)}...</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

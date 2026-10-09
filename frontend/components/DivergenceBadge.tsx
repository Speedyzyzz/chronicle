import React from "react";

interface DivergenceBadgeProps {
  diverged: boolean;
  firstDivergenceIndex?: number | null;
  convergencePercentage?: number;
}

export function DivergenceBadge({
  diverged,
  firstDivergenceIndex,
  convergencePercentage = 100,
}: DivergenceBadgeProps) {
  if (!diverged) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>100% Deterministic Replay Convergence</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-950/60 border border-rose-800 text-rose-400 text-xs font-mono">
      <span className="w-2 h-2 rounded-full bg-rose-400" />
      <span>
        Divergence Pinpointed at Event #{firstDivergenceIndex} ({convergencePercentage}% Convergence)
      </span>
    </div>
  );
}

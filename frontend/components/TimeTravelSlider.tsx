"use client";

import React from "react";
import { Play, Pause, RotateCcw, FastForward } from "lucide-react";

interface TimeTravelSliderProps {
  totalEvents: number;
  currentStep: number;
  onStepChange: (step: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
}

export function TimeTravelSlider({
  totalEvents,
  currentStep,
  onStepChange,
  isPlaying,
  onTogglePlay,
}: TimeTravelSliderProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onTogglePlay}
            className="p-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white transition-colors"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => onStepChange(0)}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
            title="Reset to beginning"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => onStepChange(totalEvents - 1)}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
            title="Jump to end"
          >
            <FastForward className="w-4 h-4" />
          </button>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Step <span className="text-indigo-400 font-bold">{currentStep + 1}</span> of {Math.max(1, totalEvents)}
        </div>
      </div>

      <input
        type="range"
        min={0}
        max={Math.max(0, totalEvents - 1)}
        value={currentStep}
        onChange={(e) => onStepChange(parseInt(e.target.value, 10))}
        className="w-full accent-indigo-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
      />
    </div>
  );
}

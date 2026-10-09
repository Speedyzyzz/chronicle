import React from "react";
import { HardDrive, Hash, Check } from "lucide-react";

interface Blake3BlobViewerProps {
  rootHash?: string | null;
  manifest?: Record<string, string>;
}

export function Blake3BlobViewer({ rootHash, manifest = {} }: Blake3BlobViewerProps) {
  const fileEntries = Object.entries(manifest);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-slate-300 font-medium">
          <HardDrive className="w-4 h-4 text-indigo-400" />
          <span>Content-Addressed Filesystem Delta</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
          <Hash className="w-3.5 h-3.5 text-indigo-400" />
          <span>{rootHash ? rootHash.slice(0, 16) + "..." : "empty"}</span>
        </div>
      </div>

      {fileEntries.length === 0 ? (
        <div className="text-xs text-slate-500 py-6 text-center italic">
          No filesystem modifications recorded in this state.
        </div>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {fileEntries.map(([path, digest]) => (
            <div
              key={path}
              className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80 text-xs font-mono"
            >
              <div className="text-slate-300 truncate max-w-xs">{path}</div>
              <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                <span className="text-indigo-400">{digest.slice(0, 10)}...</span>
                <Check className="w-3.5 h-3.5 text-emerald-500" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

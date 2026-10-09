import type { Metadata } from "next";
import React from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chronicle — Deterministic Record & Replay Runtime",
  description: "Time-travel causal execution debugger and replay engine for AI coding agents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen antialiased flex flex-col font-sans">
        <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              CH
            </div>
            <div>
              <span className="font-semibold text-lg tracking-tight text-white">Chronicle</span>
              <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-300 font-mono">
                v0.1.0
              </span>
            </div>
          </div>
          <nav className="flex items-center gap-6 text-sm text-slate-400">
            <a href="/" className="hover:text-white transition-colors">Sessions</a>
            <a href="/benchmark" className="hover:text-white transition-colors">ChronicleBench</a>
            <span className="text-xs px-2.5 py-1 bg-emerald-950 border border-emerald-800 text-emerald-400 rounded-md font-mono">
              Pure Replay Ready
            </span>
          </nav>
        </header>
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>
      </body>
    </html>
  );
}

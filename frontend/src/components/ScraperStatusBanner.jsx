import React, { useState } from 'react';
import { Loader2, CheckCircle2, AlertCircle, Terminal, ChevronDown, ChevronUp, Radio } from 'lucide-react';

export default function ScraperStatusBanner({ status }) {
  const [showLogs, setShowLogs] = useState(false);

  if (!status || status.status === 'idle') {
    return null;
  }

  const isRunning = status.status === 'running';
  const isCompleted = status.status === 'completed';
  const isError = status.status === 'error';

  return (
    <div
      className={`mb-6 rounded-xl border p-4 transition-all duration-300 shadow-xs ${
        isRunning
          ? 'bg-blue-50/70 border-blue-200'
          : isError
          ? 'bg-rose-50 border-rose-200'
          : 'bg-emerald-50/70 border-emerald-200'
      }`}
    >
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center space-x-3">
          {isRunning ? (
            <div className="relative flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              <span className="absolute -top-1 -right-1 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
              </span>
            </div>
          ) : isError ? (
            <AlertCircle className="w-5 h-5 text-rose-600" />
          ) : (
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          )}

          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-sm font-semibold ${
                  isRunning
                    ? 'text-blue-900'
                    : isError
                    ? 'text-rose-900'
                    : 'text-emerald-900'
                }`}
              >
                {isRunning
                  ? 'Scraping in progress...'
                  : isError
                  ? 'Scraping encountered issues'
                  : 'Scrape cycle completed'}
              </span>
              {isRunning && status.current_source && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium animate-pulse flex items-center gap-1">
                  <Radio className="w-3 h-3 text-blue-600 animate-pulse" />
                  {status.current_source}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              {status.message || 'Processing publicly accessible portal endpoints...'}
            </p>
          </div>
        </div>

        {/* Stats summary pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="bg-white/80 backdrop-blur px-2.5 py-1 rounded-md border border-slate-200 text-slate-700 font-medium">
            Sources: <span className="font-bold text-slate-900">{status.sources_checked}/6</span>
          </div>
          <div className="bg-white/80 backdrop-blur px-2.5 py-1 rounded-md border border-slate-200 text-slate-700 font-medium">
            Found: <span className="font-bold text-slate-900">{status.tenders_found}</span>
          </div>
          <div className="bg-white/80 backdrop-blur px-2.5 py-1 rounded-md border border-slate-200 text-emerald-700 font-medium">
            IT: <span className="font-bold">{status.it_tenders}</span>
          </div>
          <div className="bg-white/80 backdrop-blur px-2.5 py-1 rounded-md border border-slate-200 text-blue-700 font-medium">
            New: <span className="font-bold">{status.new_tenders}</span>
          </div>
          <div className="bg-white/80 backdrop-blur px-2.5 py-1 rounded-md border border-slate-200 text-slate-500 font-medium">
            Dupes: <span className="font-bold text-slate-700">{status.duplicates}</span>
          </div>

          <button
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors font-medium cursor-pointer"
          >
            <Terminal className="w-3.5 h-3.5 text-slate-500" />
            <span>{showLogs ? 'Hide Logs' : 'View Logs'}</span>
            {showLogs ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Expandable Console Logs */}
      {showLogs && (
        <div className="mt-3 pt-3 border-t border-slate-200/60">
          <div className="bg-slate-900 text-slate-200 rounded-lg p-3 text-xs font-mono max-h-48 overflow-y-auto space-y-1 shadow-inner">
            {status.logs && status.logs.length > 0 ? (
              status.logs.map((log, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-emerald-400 select-none">&gt;</span>
                  <span className="text-slate-300">{log}</span>
                </div>
              ))
            ) : (
              <p className="text-slate-500 italic">No logs generated yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { Wind, Activity, Database, RefreshCw, Info, Calendar } from 'lucide-react';

export default function AppHeader({ onRefresh, isRefreshing, onToggleQuality, qualityOpen, period }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 px-6 py-3.5 backdrop-blur-md bg-opacity-90">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white">
            <Wind className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                WindScope
              </h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                UK Wind Forecast Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Day-Ahead Wholesale Power Procurement Analytics & Forecast Accuracy Evaluation
            </p>
          </div>
        </div>

        {/* Status Pills & Controls */}
        <div className="flex items-center flex-wrap gap-2.5">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-teal-400" />
            <span>Elexon BMRS:</span>
            <span className="font-mono font-medium text-emerald-400">FUELHH &bull; WINDFOR</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Calendar className="w-3.5 h-3.5 text-blue-400" />
            <span>Target Period:</span>
            <span className="font-medium text-white">Jan 2026</span>
          </div>

          <button
            onClick={onToggleQuality}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              qualityOpen
                ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Info className="w-3.5 h-3.5" />
            <span>Data Transparency</span>
          </button>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
            title="Refetch official datasets from Elexon"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Sync Elexon'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}

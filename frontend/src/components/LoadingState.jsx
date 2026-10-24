import React from 'react';
import { Wind } from 'lucide-react';

export default function LoadingState({ message = 'Loading January 2026 Elexon wind data...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
      <div className="relative mb-4">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <Wind className="w-8 h-8 animate-pulse text-emerald-400" />
        </div>
        <div className="absolute -inset-1 rounded-2xl border-2 border-emerald-500/30 border-t-emerald-400 animate-spin pointer-events-none" />
      </div>
      <h3 className="text-base font-semibold text-white tracking-tight">{message}</h3>
      <p className="text-xs text-slate-400 max-w-sm mt-1">
        Evaluating half-hour actual outturn against Day-Ahead publication cutoffs...
      </p>
    </div>
  );
}

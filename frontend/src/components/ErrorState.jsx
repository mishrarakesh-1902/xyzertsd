import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

export default function ErrorState({ title = 'Error Loading Analysis', message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center max-w-md mx-auto">
      <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-4">
        <AlertTriangle className="w-7 h-7" />
      </div>
      <h3 className="text-base font-bold text-white tracking-tight">{title}</h3>
      <p className="text-xs text-rose-300/90 mt-2 leading-relaxed bg-rose-950/40 p-3 rounded-xl border border-rose-900/50">
        {message || 'An unexpected error occurred while communicating with the backend API.'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl border border-slate-700 transition-colors shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Retry Analysis</span>
        </button>
      )}
    </div>
  );
}

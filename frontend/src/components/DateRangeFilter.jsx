import React from 'react';
import { Calendar, RotateCcw } from 'lucide-react';

export default function DateRangeFilter({ startDate, endDate, onRangeChange, onReset }) {
  const presets = [
    { label: 'Full Month (Jan 1-31)', start: '2026-01-01', end: '2026-01-31' },
    { label: 'Week 1 (Jan 1-7)', start: '2026-01-01', end: '2026-01-07' },
    { label: 'Week 2 (Jan 8-14)', start: '2026-01-08', end: '2026-01-14' },
    { label: 'Week 3 (Jan 15-21)', start: '2026-01-15', end: '2026-01-21' },
    { label: 'Week 4 (Jan 22-28)', start: '2026-01-22', end: '2026-01-28' },
    { label: 'Late Jan (Jan 29-31)', start: '2026-01-29', end: '2026-01-31' },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Presets */}
        <div className="flex items-center flex-wrap gap-1.5">
          <span className="text-xs font-semibold text-slate-400 mr-1 uppercase tracking-wider flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            Quick Slices:
          </span>
          {presets.map((p) => {
            const isActive = startDate === p.start && endDate === p.end;
            return (
              <button
                key={p.label}
                onClick={() => onRangeChange(p.start, p.end)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700 hover:text-white'
                }`}
              >
                {p.label}
              </button>
            );
          })}
        </div>

        {/* Custom Pickers */}
        <div className="flex items-center flex-wrap gap-2 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
            <span className="text-slate-400">From:</span>
            <input
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={startDate || '2026-01-01'}
              onChange={(e) => onRangeChange(e.target.value, endDate)}
              className="bg-transparent text-slate-200 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1">
            <span className="text-slate-400">To:</span>
            <input
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={endDate || '2026-01-31'}
              onChange={(e) => onRangeChange(startDate, e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            />
          </div>

          <button
            onClick={onReset}
            className="flex items-center gap-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            title="Reset to Full Month"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { Clock, ShieldAlert, Layers } from 'lucide-react';

export default function CutoffSelector({
  cutoffs,
  selectedCutoff,
  onCutoffChange,
  alignment,
  onAlignmentChange,
}) {
  const currentCutoffObj = cutoffs.find((c) => c.id === selectedCutoff);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Cutoff Selector */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <Clock className="w-4 h-4 text-emerald-400" />
            <label htmlFor="cutoff-select" className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Procurement Decision Cutoff Rule
            </label>
            <span className="text-[11px] text-slate-500">(Prevents look-ahead bias)</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              id="cutoff-select"
              value={selectedCutoff}
              onChange={(e) => onCutoffChange(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none min-w-[280px]"
            >
              {cutoffs.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label} {c.isDefault ? '— [Default Standard]' : ''}
                </option>
              ))}
            </select>

            {/* Alignment Resolution Selector */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs">
              <span className="text-slate-400 px-2 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                Resolution:
              </span>
              <button
                type="button"
                onClick={() => onAlignmentChange('exact')}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  alignment === 'exact'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Only match hourly :00 intervals (744 total)"
              >
                Exact (:00 Hourly)
              </button>
              <button
                type="button"
                onClick={() => onAlignmentChange('hourly_block')}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  alignment === 'hourly_block'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
                title="Hourly forecast mapped to both :00 and :30 half-hour periods (1,488 total)"
              >
                Block (:00 & :30 Half-Hourly)
              </button>
            </div>
          </div>

          {/* Active Cutoff Description */}
          {currentCutoffObj && (
            <p className="mt-2 text-xs text-slate-400 leading-relaxed">
              <span className="text-emerald-400 font-medium">Active Policy: </span>
              {currentCutoffObj.description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

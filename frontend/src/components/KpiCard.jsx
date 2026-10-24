import React from 'react';
import { HelpCircle } from 'lucide-react';

export default function KpiCard({ title, value, unit, subtitle, tooltip, badge, badgeColor, icon: Icon, accentColor = 'emerald' }) {
  const accentClasses = {
    emerald: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    blue: 'border-blue-500/30 text-blue-400 bg-blue-500/10',
    amber: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    rose: 'border-rose-500/30 text-rose-400 bg-rose-500/10',
    purple: 'border-purple-500/30 text-purple-400 bg-purple-500/10',
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all relative group">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </span>
          {tooltip && (
            <div className="relative group/tooltip">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 cursor-pointer" />
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover/tooltip:block w-56 p-2 bg-slate-800 text-slate-200 text-xs rounded-lg shadow-xl border border-slate-700 z-50 pointer-events-none">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg border ${accentClasses[accentColor] || accentClasses.emerald}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value !== null && value !== undefined ? value.toLocaleString() : '—'}
        </span>
        {unit && <span className="text-xs font-medium text-slate-400">{unit}</span>}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
        <span>{subtitle}</span>
        {badge && (
          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${badgeColor || 'bg-slate-800 text-slate-300'}`}>
            {badge}
          </span>
        )}
      </div>
    </div>
  );
}

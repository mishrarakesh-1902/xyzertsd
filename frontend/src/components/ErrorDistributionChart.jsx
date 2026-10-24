import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from 'recharts';

function DailyTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-xl text-xs space-y-1.5 min-w-[180px]">
        <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1">
          {data.dayLabel}
        </div>
        <div className="flex justify-between items-center text-slate-300">
          <span>Daily Bias:</span>
          <span className={`font-mono font-bold ${data.bias > 0 ? 'text-amber-400' : 'text-blue-400'}`}>
            {data.bias > 0 ? `+${data.bias} MW` : `${data.bias} MW`}
          </span>
        </div>
        <div className="flex justify-between items-center text-slate-400">
          <span>Daily MAE:</span>
          <span className="font-mono text-emerald-400 font-bold">{data.mae} MW</span>
        </div>
        <div className="flex justify-between items-center text-slate-500 text-[11px] pt-1 border-t border-slate-800">
          <span>Evaluated intervals:</span>
          <span>{data.count}</span>
        </div>
      </div>
    );
  }
  return null;
}

export default function ErrorDistributionChart({ records }) {
  const dailyData = useMemo(() => {
    const byDay = {};

    records.forEach((r) => {
      if (r.status === 'MATCHED' && r.error !== null) {
        const dayKey = r.deliveryTime.substring(0, 10);
        if (!byDay[dayKey]) {
          byDay[dayKey] = { errors: [], absErrors: [] };
        }
        byDay[dayKey].errors.push(r.error);
        byDay[dayKey].absErrors.push(r.absError);
      }
    });

    return Object.keys(byDay).sort().map((dayKey) => {
      const item = byDay[dayKey];
      const count = item.errors.length;
      const avgBias = Math.round(item.errors.reduce((a, b) => a + b, 0) / count);
      const avgMae = Math.round(item.absErrors.reduce((a, b) => a + b, 0) / count);
      const dt = new Date(`${dayKey}T00:00:00Z`);
      const dayLabel = dt.toLocaleDateString('en-GB', { month: 'short', day: 'numeric', timeZone: 'UTC' });

      return {
        dayKey,
        dayLabel,
        bias: avgBias,
        mae: avgMae,
        count,
      };
    });
  }, [records]);

  if (!dailyData.length) {
    return null;
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-slate-800/80 pb-2.5">
        <div>
          <h3 className="text-sm font-semibold text-white">Daily Forecast Bias & MAE Distribution</h3>
          <p className="text-xs text-slate-400">
            Positive (Amber) = Overforecast &bull; Negative (Blue) = Underforecast &bull; In MW
          </p>
        </div>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={dailyData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="dayLabel" stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} minTickGap={20} />
            <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} unit=" MW" width={55} />
            <Tooltip content={<DailyTooltip />} />
            <ReferenceLine y={0} stroke="#475569" strokeDasharray="2 2" />
            <Bar dataKey="bias" radius={[2, 2, 0, 0]}>
              {dailyData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.bias >= 0 ? '#f59e0b' : '#38bdf8'}
                  opacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

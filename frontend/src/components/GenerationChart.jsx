import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const dataPoint = payload[0].payload;
    const actual = dataPoint.actualGeneration;
    const forecast = dataPoint.forecastGeneration;
    const error = dataPoint.error;
    const pubTime = dataPoint.forecastPublishTime;
    const leadHours = dataPoint.leadHours;

    return (
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3.5 shadow-2xl text-xs space-y-2 min-w-[220px]">
        <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1.5 flex justify-between items-center">
          <span>{dataPoint.formattedTime}</span>
          <span className="text-[10px] text-slate-500 font-mono">SP {dataPoint.settlementPeriod || '—'}</span>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between items-center text-teal-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-400 inline-block" />
              Actual (FUELHH):
            </span>
            <span className="font-mono font-bold">
              {actual !== null && actual !== undefined ? `${actual.toLocaleString()} MW` : 'Missing'}
            </span>
          </div>

          <div className="flex justify-between items-center text-indigo-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 inline-block" />
              Forecast (WINDFOR):
            </span>
            <span className="font-mono font-bold">
              {forecast !== null && forecast !== undefined ? `${forecast.toLocaleString()} MW` : 'Missing'}
            </span>
          </div>

          {error !== null && error !== undefined && (
            <div className={`flex justify-between items-center pt-1 border-t border-slate-800/80 font-bold ${
              error > 0 ? 'text-amber-400' : error < 0 ? 'text-blue-400' : 'text-slate-300'
            }`}>
              <span>Error (F - A):</span>
              <span className="font-mono">
                {error > 0 ? `+${error.toLocaleString()} MW` : `${error.toLocaleString()} MW`}
              </span>
            </div>
          )}
        </div>

        {pubTime && (
          <div className="pt-1.5 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-0.5">
            <div>
              <span className="text-slate-500">Published:</span> {pubTime.replace('T', ' ').replace('Z', ' UTC')}
            </div>
            {leadHours !== null && (
              <div>
                <span className="text-slate-500">Lead Time:</span> {leadHours} hours
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
  return null;
}

export default function GenerationChart({ records, cutoffLabel }) {
  const chartData = useMemo(() => {
    return records.map((r) => {
      const dt = new Date(r.deliveryTime);
      const dateStr = dt.toLocaleDateString('en-GB', { month: 'short', day: 'numeric', timeZone: 'UTC' });
      const timeStr = dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' });
      return {
        ...r,
        formattedTime: `${dateStr} ${timeStr} UTC`,
        dateLabel: dateStr,
        timeLabel: timeStr,
      };
    });
  }, [records]);

  if (!records || records.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        No generation records match the current filters.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">
            Wind Generation: Actual Outturn vs. Selected Forecast
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            National GB wind generation outturn (FUELHH) and forecast selected at{' '}
            <span className="text-emerald-400 font-medium">{cutoffLabel}</span>
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-teal-400">
            <span className="w-3 h-0.5 bg-teal-400 inline-block" />
            <span>Actual Outturn</span>
          </div>
          <div className="flex items-center gap-1.5 text-indigo-400">
            <span className="w-3 h-0.5 bg-indigo-400 inline-block" />
            <span>Selected Forecast</span>
          </div>
          <div className="flex items-center gap-1.5 text-amber-400/80">
            <span className="w-2.5 h-2.5 bg-amber-500/30 border border-amber-500/50 inline-block" />
            <span>Error (F - A)</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="formattedTime"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              yAxisId="power"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              tickLine={false}
              unit=" MW"
              width={75}
            />
            <YAxis
              yAxisId="error"
              orientation="right"
              stroke="#475569"
              tick={{ fontSize: 10 }}
              tickLine={false}
              unit=" MW"
              width={65}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine yAxisId="error" y={0} stroke="#475569" strokeDasharray="2 2" />

            <Bar
              yAxisId="error"
              dataKey="error"
              fill="#f59e0b"
              opacity={0.3}
              name="Forecast Error"
            />
            <Line
              yAxisId="power"
              type="monotone"
              dataKey="actualGeneration"
              stroke="#14b8a6"
              strokeWidth={2}
              dot={false}
              name="Actual Generation"
              connectNulls={false}
            />
            <Line
              yAxisId="power"
              type="monotone"
              dataKey="forecastGeneration"
              stroke="#818cf8"
              strokeWidth={2}
              dot={false}
              name="Selected Forecast"
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

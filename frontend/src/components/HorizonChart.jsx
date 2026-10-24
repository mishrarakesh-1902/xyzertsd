import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Clock, Info, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

function HorizonTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900 border border-slate-700/80 rounded-xl p-3 shadow-xl text-xs space-y-1.5 min-w-[200px]">
        <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1">
          {data.label} Horizon
        </div>
        <div className="flex justify-between items-center text-emerald-400">
          <span>Mean Absolute Error (MAE):</span>
          <span className="font-mono font-bold">{data.mae ? `${data.mae.toLocaleString()} MW` : '—'}</span>
        </div>
        <div className="flex justify-between items-center text-blue-400">
          <span>Root Mean Sq Error (RMSE):</span>
          <span className="font-mono font-bold">{data.rmse ? `${data.rmse.toLocaleString()} MW` : '—'}</span>
        </div>
        <div className="flex justify-between items-center text-slate-300">
          <span>Forecast Bias:</span>
          <span className={`font-mono font-bold ${data.bias > 0 ? 'text-amber-400' : 'text-blue-400'}`}>
            {data.bias !== null && data.bias !== undefined ? (data.bias > 0 ? `+${data.bias} MW` : `${data.bias} MW`) : '—'}
          </span>
        </div>
        <div className="flex justify-between items-center text-slate-500 text-[11px] pt-1 border-t border-slate-800">
          <span>Sample Vintages (n):</span>
          <span className="font-mono">{data.n.toLocaleString()} pairs</span>
        </div>
      </div>
    );
  }
  return null;
}

export default function HorizonChart({ alignment, startDate, endDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getHorizonAnalysis({ alignment, startDate, endDate })
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load horizon analysis');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [alignment, startDate, endDate]);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-slate-800/80 pb-2.5">
        <div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Forecast Error by Lead-Time Horizon</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluates accuracy across all published forecast vintages from 0h to 48h+ before delivery (in MW)
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-3 h-2 bg-emerald-500 rounded-sm inline-block" />
            <span>MAE</span>
          </div>
          <div className="flex items-center gap-1.5 text-blue-400">
            <span className="w-3 h-2 bg-blue-500 rounded-sm inline-block" />
            <span>RMSE</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-xs text-slate-400">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mr-2" />
          <span>Computing lead-time horizon error curves...</span>
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      ) : data ? (
        <>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.buckets} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="label" stroke="#64748b" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickLine={false} unit=" MW" width={60} />
                <Tooltip content={<HorizonTooltip />} />
                <Bar dataKey="mae" fill="#10b981" radius={[3, 3, 0, 0]} name="MAE (MW)" />
                <Bar dataKey="rmse" fill="#3b82f6" radius={[3, 3, 0, 0]} name="RMSE (MW)" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Plain-English Takeaway */}
          <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex items-start gap-2 text-xs text-slate-300">
            <Info className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <span className="text-white font-semibold">Key Horizon Insight: </span>
              {data.takeaway}
            </p>
          </div>
        </>
      ) : null}
    </div>
  );
}

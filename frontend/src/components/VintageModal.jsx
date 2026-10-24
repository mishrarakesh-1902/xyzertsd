import React, { useEffect, useState } from 'react';
import { X, Clock, CheckCircle2, XCircle, ArrowRight, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

export default function VintageModal({ deliveryTime, cutoffType, onClose }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!deliveryTime) return;
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getVintages(deliveryTime, cutoffType)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to fetch vintage history');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [deliveryTime, cutoffType]);

  if (!deliveryTime) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Forecast Vintage Evolution</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Target Delivery: <span className="font-mono text-emerald-300">{deliveryTime.replace('T', ' ').replace('Z', ' UTC')}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {loading && (
            <div className="py-12 text-center text-slate-400">
              <div className="inline-block w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-2" />
              <p className="text-xs">Loading forecast publication history...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs">
              <AlertTriangle className="w-4 h-4 inline mr-1" />
              {error}
            </div>
          )}

          {data && (
            <>
              {/* Snapshot Summary */}
              <div className="grid grid-cols-3 gap-3 p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-xs">
                <div>
                  <span className="text-slate-500 block">Actual Outturn:</span>
                  <span className="font-mono font-bold text-teal-400 text-sm">
                    {data.actualGeneration !== null ? `${data.actualGeneration.toLocaleString()} MW` : 'Missing'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Selected Forecast:</span>
                  <span className="font-mono font-bold text-indigo-400 text-sm">
                    {data.selectedForecast ? `${data.selectedForecast.generation.toLocaleString()} MW` : 'None eligible'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Vintages Published:</span>
                  <span className="font-mono font-bold text-white text-sm">
                    {data.totalVintages} updates
                  </span>
                </div>
              </div>

              {/* Vintages Timeline Table */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  All Published Forecasts for this Interval
                </h4>
                <div className="border border-slate-800 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">Publish Time (UTC)</th>
                        <th className="py-2.5 px-3">Lead Time</th>
                        <th className="py-2.5 px-3">Forecast (MW)</th>
                        <th className="py-2.5 px-3">Cutoff Eligibility</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {data.vintages.map((v, idx) => {
                        const isSelected = data.selectedForecast && data.selectedForecast.publishTime === v.publishTime;
                        return (
                          <tr
                            key={idx}
                            className={`transition-colors ${
                              isSelected
                                ? 'bg-emerald-950/30 text-emerald-200 font-semibold'
                                : v.isEligible
                                ? 'hover:bg-slate-800/40 text-slate-300'
                                : 'bg-slate-950/30 text-slate-500 opacity-60'
                            }`}
                          >
                            <td className="py-2 px-3">
                              {v.publishTime.replace('T', ' ').replace('Z', '')}
                            </td>
                            <td className="py-2 px-3 text-slate-400">
                              {v.leadHours}h prior
                            </td>
                            <td className="py-2 px-3 font-bold text-slate-100">
                              {v.generation.toLocaleString()} MW
                            </td>
                            <td className="py-2 px-3">
                              {isSelected ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                                  <CheckCircle2 className="w-3 h-3" /> Selected (Latest Eligible)
                                </span>
                              ) : v.isEligible ? (
                                <span className="inline-flex items-center gap-1 text-[11px] text-slate-400">
                                  <CheckCircle2 className="w-3 h-3 text-slate-500" /> Eligible
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[11px] text-amber-500/80">
                                  <XCircle className="w-3 h-3" /> Excluded (Post-Cutoff)
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-950/80 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

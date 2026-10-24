import React from 'react';
import { X, ShieldCheck, Database, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react';

export default function DataQualityPanel({ quality, methodology, isOpen, onClose }) {
  if (!isOpen || !quality) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Data Quality & Methodology Transparency</h3>
              <p className="text-xs text-slate-400">Auditable verification of Elexon datasets and error calculation rules</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-5 text-xs">
          {/* Dataset Ingestion Accounting */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-emerald-400" />
              January 2026 Delivery Interval Accounting
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-500 block">Expected Intervals:</span>
                <span className="font-mono text-lg font-bold text-white">
                  {quality.expectedDeliveryIntervals}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">31 days &times; 48 periods</span>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-500 block">Actual Outturns (FUELHH):</span>
                <span className="font-mono text-lg font-bold text-teal-400">
                  {quality.actualRecordsRetrieved}
                </span>
                <span className="text-[10px] text-teal-400 block mt-0.5">
                  {quality.actualCompletenessPct}% Complete
                </span>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-500 block">Raw WINDFOR Records:</span>
                <span className="font-mono text-lg font-bold text-indigo-400">
                  {quality.rawForecastRecordsRetrieved.toLocaleString()}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">
                  Across all published vintages
                </span>
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-500 block">Matched Pairs:</span>
                <span className="font-mono text-lg font-bold text-emerald-400">
                  {quality.matchedIntervals}
                </span>
                <span className="text-[10px] text-emerald-400 block mt-0.5">
                  {quality.matchedCompletenessPct}% of evaluated
                </span>
              </div>
            </div>
          </div>

          {/* Time Resolution Notice */}
          <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-slate-300">
            <span className="font-semibold text-blue-400 block mb-1">Dataset Time Resolution Notice:</span>
            <p className="leading-relaxed">{quality.resolutionNotice}</p>
          </div>

          {/* Warnings */}
          {quality.warnings && quality.warnings.length > 0 && (
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-200 space-y-1">
              <span className="font-semibold text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" /> Coverage Considerations:
              </span>
              <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-300/90 pl-1">
                {quality.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Methodology & Formulas */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-emerald-400" />
              Mathematical Definitions & Sign Conventions
            </h4>
            <div className="space-y-2 border border-slate-800 rounded-xl p-3.5 bg-slate-950">
              <div>
                <span className="font-semibold text-slate-200">Forecast Error Definition:</span>
                <div className="font-mono text-emerald-400 bg-slate-900 px-2.5 py-1 rounded my-1 border border-slate-800 inline-block">
                  error = forecast - actual (MW)
                </div>
                <p className="text-slate-400 text-[11px]">
                  Positive error (+MW) indicates the forecast overestimated wind generation.
                  Negative error (-MW) indicates the forecast underestimated wind generation.
                </p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 grid sm:grid-cols-3 gap-3">
                <div>
                  <span className="font-semibold text-slate-200">MAE (Mean Absolute Error):</span>
                  <div className="font-mono text-emerald-400 bg-slate-900 px-2 py-0.5 rounded my-1 border border-slate-800">
                    mean(|forecast - actual|)
                  </div>
                  <p className="text-slate-400 text-[11px]">Average absolute error magnitude in MW.</p>
                </div>
                <div>
                  <span className="font-semibold text-slate-200">RMSE:</span>
                  <div className="font-mono text-emerald-400 bg-slate-900 px-2 py-0.5 rounded my-1 border border-slate-800">
                    sqrt(mean((f - a)^2))
                  </div>
                  <p className="text-slate-400 text-[11px]">Penalizes larger forecast errors more heavily.</p>
                </div>
                <div>
                  <span className="font-semibold text-slate-200">Forecast Bias:</span>
                  <div className="font-mono text-emerald-400 bg-slate-900 px-2 py-0.5 rounded my-1 border border-slate-800">
                    mean(forecast - actual)
                  </div>
                  <p className="text-slate-400 text-[11px]">Systematic over/underforecast tendency in MW.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Ingestion & Cache Status */}
          <div className="flex items-center justify-between p-3 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-400 text-[11px]">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Data Source Status:</span>
              <span className="text-white font-medium">
                {quality.cached ? 'Verified Local Cache (Upstream Elexon Stream)' : 'Live API Outturn'}
              </span>
            </div>
            {quality.cacheTimestamp && (
              <div>
                <span>Last Synchronized: </span>
                <span className="font-mono text-slate-300">
                  {quality.cacheTimestamp.replace('T', ' ').substring(0, 19)} UTC
                </span>
              </div>
            )}
          </div>
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

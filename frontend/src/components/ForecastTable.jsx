import React, { useState, useMemo } from 'react';
import { Search, ArrowUpDown, History, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ForecastTable({ records, onInspectVintages }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('deliveryTime');
  const [sortDirection, setSortDirection] = useState('asc');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // Status filter
      if (statusFilter !== 'ALL' && r.status !== statusFilter) {
        return false;
      }
      // Search term
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const timeMatch = r.deliveryTime.toLowerCase().includes(term);
        const statusMatch = r.status.toLowerCase().includes(term);
        return timeMatch || statusMatch;
      }
      return true;
    });
  }, [records, searchTerm, statusFilter]);

  const sortedRecords = useMemo(() => {
    return [...filteredRecords].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'string') {
        return sortDirection === 'asc'
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      }

      return sortDirection === 'asc' ? valA - valB : valB - valA;
    });
  }, [filteredRecords, sortField, sortDirection]);

  const totalPages = Math.ceil(sortedRecords.length / pageSize) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedRecords.slice(start, start + pageSize);
  }, [sortedRecords, page, pageSize]);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm space-y-3 p-5">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight">
            Half-Hourly & Hourly Interval Delivery Records
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Showing {filteredRecords.length} intervals &bull; Click "Vintages" to inspect historical publication evolution
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2 text-xs">
          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="MATCHED">Matched Pairs Only</option>
            <option value="MISSING_FORECAST">Missing Forecast Only</option>
            <option value="MISSING_ACTUAL">Missing Actual Only</option>
          </select>

          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search timestamp..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-500 rounded-lg pl-8 pr-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-44"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-slate-800/80 rounded-xl">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold select-none">
            <tr>
              <th
                onClick={() => handleSort('deliveryTime')}
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Delivery Time (UTC)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-3">Period</th>
              <th
                onClick={() => handleSort('actualGeneration')}
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Actual (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('forecastGeneration')}
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Forecast (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('error')}
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Error (F - A)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('absError')}
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Abs Error</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-3">Selected Publish Time</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {paginatedRecords.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-500">
                  No records match your filters.
                </td>
              </tr>
            ) : (
              paginatedRecords.map((r, idx) => {
                const isMatched = r.status === 'MATCHED';
                const isOver = r.error > 0;
                const isUnder = r.error < 0;

                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-slate-200">
                      {r.deliveryTime.replace('T', ' ').replace('Z', '')}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">
                      {r.settlementPeriod ? `SP ${r.settlementPeriod}` : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-teal-400">
                      {r.actualGeneration !== null ? `${r.actualGeneration.toLocaleString()} MW` : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-indigo-400">
                      {r.forecastGeneration !== null ? `${r.forecastGeneration.toLocaleString()} MW` : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-bold">
                      {r.error !== null ? (
                        <span className={isOver ? 'text-amber-400' : isUnder ? 'text-blue-400' : 'text-slate-300'}>
                          {isOver ? `+${r.error.toLocaleString()}` : r.error.toLocaleString()} MW
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {r.absError !== null ? `${r.absError.toLocaleString()} MW` : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {r.forecastPublishTime
                        ? `${r.forecastPublishTime.replace('T', ' ').replace('Z', '')} (${r.leadHours}h prior)`
                        : '—'}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      {isMatched ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" /> Matched
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          <AlertCircle className="w-3 h-3" /> {r.status.replace('_', ' ')}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right font-sans">
                      <button
                        onClick={() => onInspectVintages(r.deliveryTime)}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded text-[11px] font-medium transition-colors"
                        title="View all forecast vintages for this delivery interval"
                      >
                        <History className="w-3 h-3" />
                        <span>Vintages</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pt-2 text-xs text-slate-400">
        <div>
          Showing page <span className="text-white font-medium">{page}</span> of{' '}
          <span className="text-white font-medium">{totalPages}</span> ({sortedRecords.length} total entries)
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setPage(1)}
            disabled={page === 1}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none rounded transition-colors"
          >
            First
          </button>
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none rounded transition-colors"
          >
            Previous
          </button>
          <span className="px-2 font-mono text-slate-300">{page}</span>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
            disabled={page === totalPages}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none rounded transition-colors"
          >
            Next
          </button>
          <button
            onClick={() => setPage(totalPages)}
            disabled={page === totalPages}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none rounded transition-colors"
          >
            Last
          </button>
        </div>
      </div>
    </div>
  );
}

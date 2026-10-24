import React, { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import {
  Activity,
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  Percent,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Info,
} from 'lucide-react';
import { api } from './services/api';
import AppHeader from './components/AppHeader';
import KpiCard from './components/KpiCard';
import CutoffSelector from './components/CutoffSelector';
import DateRangeFilter from './components/DateRangeFilter';
import GenerationChart from './components/GenerationChart';
import HorizonChart from './components/HorizonChart';
import ErrorDistributionChart from './components/ErrorDistributionChart';
import ForecastTable from './components/ForecastTable';
import LoadingState from './components/LoadingState';
import ErrorState from './components/ErrorState';

// Code-split modals for optimal bundle size
const VintageModal = lazy(() => import('./components/VintageModal'));
const DataQualityPanel = lazy(() => import('./components/DataQualityPanel'));

export default function App() {
  const [cutoffs, setCutoffs] = useState([]);
  const [selectedCutoff, setSelectedCutoff] = useState('d1_0920');
  const [alignment, setAlignment] = useState('exact');
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-01-31');

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const [inspectVintageDelivery, setInspectVintageDelivery] = useState(null);
  const [qualityOpen, setQualityOpen] = useState(false);

  // Load cutoffs once on mount
  useEffect(() => {
    api.getCutoffs()
      .then((data) => {
        setCutoffs(data);
        const defaultCutoff = data.find((c) => c.isDefault);
        if (defaultCutoff) {
          setSelectedCutoff(defaultCutoff.id);
        }
      })
      .catch((err) => console.error('Failed to load cutoffs:', err));
  }, []);

  // Fetch analysis whenever filters change
  const loadAnalysis = useCallback(() => {
    setLoading(true);
    setError(null);

    api.getAnalysis({
      cutoffType: selectedCutoff,
      alignment,
      startDate,
      endDate,
    })
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch wind analysis');
        setLoading(false);
      });
  }, [selectedCutoff, alignment, startDate, endDate]);

  useEffect(() => {
    loadAnalysis();
  }, [loadAnalysis]);

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await api.refreshData();
      await loadAnalysis();
    } catch (err) {
      alert(`Refresh failed: ${err.message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRangeChange = (start, end) => {
    setStartDate(start);
    setEndDate(end);
  };

  const handleResetRange = () => {
    setStartDate('2026-01-01');
    setEndDate('2026-01-31');
  };

  const currentCutoffObj = cutoffs.find((c) => c.id === selectedCutoff);
  const cutoffLabel = currentCutoffObj ? currentCutoffObj.label : selectedCutoff;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <AppHeader
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        onToggleQuality={() => setQualityOpen((prev) => !prev)}
        qualityOpen={qualityOpen}
        period={analysis ? analysis.period : null}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Controls Section */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CutoffSelector
            cutoffs={cutoffs}
            selectedCutoff={selectedCutoff}
            onCutoffChange={setSelectedCutoff}
            alignment={alignment}
            onAlignmentChange={setAlignment}
          />
          <DateRangeFilter
            startDate={startDate}
            endDate={endDate}
            onRangeChange={handleRangeChange}
            onReset={handleResetRange}
          />
        </section>

        {/* Loading / Error / Content */}
        {loading && !analysis ? (
          <LoadingState message="Processing January 2026 Elexon wind generation and forecasts..." />
        ) : error ? (
          <ErrorState message={error} onRetry={loadAnalysis} />
        ) : analysis ? (
          <>
            {/* Primary KPI Metrics Cards */}
            <section className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
              <KpiCard
                title="Mean Absolute Error"
                value={analysis.metrics.mae}
                unit="MW"
                subtitle="mean(|F - A|)"
                tooltip="Average absolute error magnitude in Megawatts over all valid matched intervals."
                icon={Activity}
                accentColor="emerald"
              />

              <KpiCard
                title="Root Mean Sq Error"
                value={analysis.metrics.rmse}
                unit="MW"
                subtitle="sqrt(mean((F - A)²))"
                tooltip="Root Mean Squared Error: places higher penalty on larger forecast deviation spikes."
                icon={BarChart3}
                accentColor="blue"
              />

              <KpiCard
                title="Forecast Bias"
                value={analysis.metrics.bias}
                unit="MW"
                subtitle="mean(F - A)"
                tooltip="Mean signed forecast error. Positive indicates systematic overforecast; negative indicates underforecast."
                badge={
                  analysis.metrics.bias > 0
                    ? `Overforecast (+${analysis.metrics.bias} MW)`
                    : analysis.metrics.bias < 0
                    ? `Underforecast (${analysis.metrics.bias} MW)`
                    : 'Unbiased'
                }
                badgeColor={
                  analysis.metrics.bias > 0
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                }
                icon={TrendingUp}
                accentColor={analysis.metrics.bias > 0 ? 'amber' : 'blue'}
              />

              <KpiCard
                title="Normalised MAE"
                value={analysis.metrics.normalizedMaePct}
                unit="%"
                subtitle="(MAE / mean(Actual)) × 100"
                tooltip="Normalised MAE relative to average actual wind generation outturn."
                badge={analysis.metrics.meanActualGeneration ? `Avg: ${analysis.metrics.meanActualGeneration.toLocaleString()} MW` : null}
                badgeColor="bg-slate-800 text-slate-300"
                icon={Percent}
                accentColor="purple"
              />

              <KpiCard
                title="Matched Intervals"
                value={analysis.metrics.matchedIntervals}
                unit={`/ ${analysis.metrics.totalIntervalsEvaluated}`}
                subtitle="Valid actual vs forecast pairs"
                tooltip="Number of delivery intervals where both actual generation and eligible forecast exist."
                badge={`${analysis.dataQuality.matchedCompletenessPct}% Match`}
                badgeColor="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                icon={CheckCircle2}
                accentColor="emerald"
              />
            </section>

            {/* Risk-Sizing & Tail Uncertainty Cards */}
            <section className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="font-semibold uppercase tracking-wider">Median Absolute Error (P50)</span>
                  <span className="text-[11px] font-mono text-emerald-400">Typical Interval</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold font-mono text-white">
                    {analysis.metrics.p50AbsoluteError ? analysis.metrics.p50AbsoluteError.toLocaleString() : '—'}
                  </span>
                  <span className="text-xs text-slate-400">MW</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">50% of intervals had an absolute error under this value.</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="font-semibold uppercase tracking-wider">90th Percentile Error (P90)</span>
                  <span className="text-[11px] font-mono text-blue-400">High Deviation</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold font-mono text-white">
                    {analysis.metrics.p90AbsoluteError ? analysis.metrics.p90AbsoluteError.toLocaleString() : '—'}
                  </span>
                  <span className="text-xs text-slate-400">MW</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">90% of intervals had an absolute error below this magnitude.</p>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="font-semibold uppercase tracking-wider">95th Percentile Tail Error (P95)</span>
                  <span className="text-[11px] font-mono text-amber-400">Tail Risk Boundary</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold font-mono text-white">
                    {analysis.metrics.p95AbsoluteError ? analysis.metrics.p95AbsoluteError.toLocaleString() : '—'}
                  </span>
                  <span className="text-xs text-slate-400">MW</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Extreme tail error: only 5% of intervals exceeded this deviation.</p>
              </div>
            </section>

            {/* How to Use This for Procurement (Decision Support Box) */}
            <section className="bg-slate-900/90 border border-emerald-500/30 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>How to Use This for Procurement (Decision Support)</span>
              </div>
              <div className="text-xs text-slate-300 leading-relaxed space-y-2">
                <p>
                  Because <code className="text-emerald-400 bg-slate-950 px-1.5 py-0.5 rounded font-mono">error = forecast - actual</code>, 
                  a <span className="font-semibold text-amber-300">positive bias</span> indicates wind generation was over-forecasted, 
                  meaning thermal/conventional power was <span className="underline decoration-amber-400/50">under-procured</span> in the day-ahead auction. 
                  A <span className="font-semibold text-blue-300">negative bias</span> means thermal power was over-procured.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-amber-400 font-semibold block mb-0.5">
                      Suggested Wind Shortfall Buffer (P95 Under-Forecast):
                    </span>
                    <span className="text-lg font-mono font-bold text-white">
                      {analysis.metrics.p95UnderforecastError ? `${analysis.metrics.p95UnderforecastError.toLocaleString()} MW` : '—'}
                    </span>
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      Traders may consider sizing flexible thermal reserves or battery backup to this buffer to protect against 95% of adverse wind drops.
                    </span>
                    {analysis.metrics.maxUnderforecast && (
                      <span className="text-[10px] text-slate-500 block mt-1">
                        Worst single shortfall: {analysis.metrics.maxUnderforecast.error} MW at {analysis.metrics.maxUnderforecast.deliveryTime.replace('T', ' ').replace('Z', ' UTC')}
                      </span>
                    )}
                  </div>

                  <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-lg">
                    <span className="text-emerald-400 font-semibold block mb-0.5">
                      Over-Forecast Exposure Boundary (P95 Over-Forecast):
                    </span>
                    <span className="text-lg font-mono font-bold text-white">
                      {analysis.metrics.p95OverforecastError ? `${analysis.metrics.p95OverforecastError.toLocaleString()} MW` : '—'}
                    </span>
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      Indicates the upside wind volume that failed to materialize in 95% of over-forecast situations.
                    </span>
                    {analysis.metrics.maxOverforecast && (
                      <span className="text-[10px] text-slate-500 block mt-1">
                        Worst single overforecast: +{analysis.metrics.maxOverforecast.error} MW at {analysis.metrics.maxOverforecast.deliveryTime.replace('T', ' ').replace('Z', ' UTC')}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 italic pt-1">
                  *Disclaimer: Provided strictly as empirical decision support based on historical Elexon outturns; not financial or trading advice.
                </p>
              </div>
            </section>

            {/* Main Time-Series Chart */}
            <section>
              <GenerationChart
                records={analysis.records}
                cutoffLabel={cutoffLabel}
              />
            </section>

            {/* Horizon Error by Lead Time (Task 3) */}
            <section>
              <HorizonChart
                alignment={alignment}
                startDate={startDate}
                endDate={endDate}
              />
            </section>

            {/* Error Distribution Chart */}
            <section>
              <ErrorDistributionChart records={analysis.records} />
            </section>

            {/* Records Table */}
            <section>
              <ForecastTable
                records={analysis.records}
                onInspectVintages={(deliveryTime) => setInspectVintageDelivery(deliveryTime)}
              />
            </section>
          </>
        ) : null}
      </main>

      {/* Modals wrapped in Suspense */}
      <Suspense fallback={null}>
        {inspectVintageDelivery && (
          <VintageModal
            deliveryTime={inspectVintageDelivery}
            cutoffType={selectedCutoff}
            onClose={() => setInspectVintageDelivery(null)}
          />
        )}

        {qualityOpen && (
          <DataQualityPanel
            quality={analysis ? analysis.dataQuality : null}
            methodology={analysis ? analysis.methodology : null}
            isOpen={qualityOpen}
            onClose={() => setQualityOpen(false)}
          />
        )}
      </Suspense>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            WindScope &bull; Official Elexon BMRS Data Engine &bull; January 2026 Analysis Period
          </div>
          <div>
            UK Day-Ahead Wholesale Power Market &bull; REint Challenge v4.1 Production Implementation
          </div>
        </div>
      </footer>
    </div>
  );
}

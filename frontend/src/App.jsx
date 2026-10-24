import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Wind,
} from 'lucide-react';
import { api } from './services/api';
import AppHeader from './components/AppHeader';
import KpiCard from './components/KpiCard';
import CutoffSelector from './components/CutoffSelector';
import DateRangeFilter from './components/DateRangeFilter';
import GenerationChart from './components/GenerationChart';
import ErrorDistributionChart from './components/ErrorDistributionChart';
import ForecastTable from './components/ForecastTable';
import VintageModal from './components/VintageModal';
import DataQualityPanel from './components/DataQualityPanel';
import LoadingState from './components/LoadingState';
import ErrorState from './components/ErrorState';

export default function App() {
  const [cutoffs, setCutoffs] = useState([]);
  const [selectedCutoff, setSelectedCutoff] = useState('d1_1200');
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
      .then((data) => setCutoffs(data))
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
            {/* KPI Metrics Cards */}
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

              <KpiCard
                title="Data Completeness"
                value={analysis.dataQuality.actualCompletenessPct}
                unit="%"
                subtitle="FUELHH actuals outturn"
                tooltip="Completeness of actual wind generation outturn records for the selected period."
                badge="1,488 Intervals"
                badgeColor="bg-teal-500/10 text-teal-400 border border-teal-500/30"
                icon={Clock}
                accentColor="purple"
              />
            </section>

            {/* Main Time-Series Chart */}
            <section>
              <GenerationChart
                records={analysis.records}
                cutoffLabel={cutoffLabel}
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

      {/* Modals */}
      <VintageModal
        deliveryTime={inspectVintageDelivery}
        cutoffType={selectedCutoff}
        onClose={() => setInspectVintageDelivery(null)}
      />

      <DataQualityPanel
        quality={analysis ? analysis.dataQuality : null}
        methodology={analysis ? analysis.methodology : null}
        isOpen={qualityOpen}
        onClose={() => setQualityOpen(false)}
      />

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

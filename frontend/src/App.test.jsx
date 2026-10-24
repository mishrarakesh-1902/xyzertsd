import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { api } from './services/api';

vi.mock('./services/api', () => ({
  api: {
    getCutoffs: vi.fn(),
    getAnalysis: vi.fn(),
    getHorizonAnalysis: vi.fn(),
    getVintages: vi.fn(),
    refreshData: vi.fn(),
  },
}));

describe('WindScope Frontend Application', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getCutoffs.mockResolvedValue([
      {
        id: 'd1_0920',
        label: 'Day-Ahead gate closure 09:20 UK (EPEX GB)',
        description: 'Standard UK Day-Ahead wholesale market benchmark.',
        isDefault: true,
        group: 'Day-Ahead Auction Cutoffs',
      },
    ]);
    api.getHorizonAnalysis.mockResolvedValue({
      period: { start: '2026-01-01', end: '2026-01-31' },
      alignment: 'exact',
      buckets: [
        { bucket: '0-6h', label: '0-6h Ahead', minLeadHours: 0, maxLeadHours: 6, mae: 1767.72, rmse: 2249.21, bias: 1548.25, n: 1488 },
        { bucket: '6-12h', label: '6-12h Ahead', minLeadHours: 6, maxLeadHours: 12, mae: 1833.73, rmse: 2304.38, bias: 1616.10, n: 1488 },
      ],
      takeaway: 'Forecast error increases with lead time.',
    });
  });

  it('renders loading state initially', () => {
    api.getAnalysis.mockReturnValue(new Promise(() => {})); // Never resolves to check loading state
    render(<App />);
    expect(screen.getAllByText(/WindScope/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Processing January 2026/i)).toBeInTheDocument();
  });

  it('renders KPI cards and analysis when data loads', async () => {
    api.getAnalysis.mockResolvedValue({
      period: { start: '2026-01-01T00:00:00Z', end: '2026-01-31T23:30:00Z' },
      methodology: {
        selectionRule: 'latest_eligible_forecast_by_cutoff',
        cutoffType: 'd1_0920',
        cutoffDescription: 'Standard UK Day-Ahead wholesale market benchmark.',
        alignment: 'exact',
        unit: 'MW',
        signConvention: 'error = forecast - actual',
      },
      metrics: {
        mae: 2127.48,
        rmse: 2606.07,
        bias: 1851.53,
        p50AbsoluteError: 1758.5,
        p90AbsoluteError: 4306.4,
        p95AbsoluteError: 5350.9,
        normalizedMaePct: 18.37,
        meanActualGeneration: 11581.11,
        maxOverforecast: { error: 6894.0, deliveryTime: '2026-01-12T01:00:00Z' },
        maxUnderforecast: { error: -3389.0, deliveryTime: '2026-01-08T19:00:00Z' },
        p95OverforecastError: 5504.5,
        p95UnderforecastError: 2374.0,
        matchedIntervals: 744,
        totalIntervalsEvaluated: 744,
        overforecastCount: 600,
        underforecastCount: 144,
        exactMatchCount: 0,
      },
      dataQuality: {
        analysisPeriod: { start: '2026-01-01', end: '2026-01-31' },
        expectedDeliveryIntervals: 1488,
        actualRecordsRetrieved: 1488,
        rawForecastRecordsRetrieved: 18080,
        uniqueForecastDeliveryIntervals: 744,
        matchedIntervals: 744,
        missingActualIntervals: 0,
        missingForecastIntervals: 0,
        actualCompletenessPct: 100.0,
        forecastCompletenessPct: 100.0,
        matchedCompletenessPct: 100.0,
        resolutionNotice: 'Notice text',
        warnings: [],
        cached: true,
        cacheTimestamp: '2026-01-01T00:00:00Z',
      },
      records: [
        {
          deliveryTime: '2026-01-01T00:00:00Z',
          settlementPeriod: 1,
          actualGeneration: 10000,
          forecastGeneration: 12000,
          forecastPublishTime: '2025-12-31T08:30:00Z',
          leadHours: 15.5,
          error: 2000,
          absError: 2000,
          status: 'MATCHED',
        },
      ],
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Mean Absolute Error')).toBeInTheDocument();
      expect(screen.getByText('2,127.48')).toBeInTheDocument();
      expect(screen.getByText('Root Mean Sq Error')).toBeInTheDocument();
      expect(screen.getByText('2,606.07')).toBeInTheDocument();
      expect(screen.getByText('Forecast Bias')).toBeInTheDocument();
      expect(screen.getByText('1,851.53')).toBeInTheDocument();
      expect(screen.getByText('Normalised MAE')).toBeInTheDocument();
      expect(screen.getByText('18.37')).toBeInTheDocument();
      expect(screen.getByText(/How to Use This for Procurement/i)).toBeInTheDocument();
    });
  });

  it('renders error state on API failure', async () => {
    api.getAnalysis.mockRejectedValue(new Error('Network connection failed'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Network connection failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Retry Analysis/i)).toBeInTheDocument();
    });
  });
});

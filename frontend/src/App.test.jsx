import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { api } from './services/api';

vi.mock('./services/api', () => ({
  api: {
    getCutoffs: vi.fn(),
    getAnalysis: vi.fn(),
    getVintages: vi.fn(),
    refreshData: vi.fn(),
  },
}));

describe('WindScope Frontend Application', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getCutoffs.mockResolvedValue([
      {
        id: 'd1_1200',
        label: 'Day-Ahead 12:00 UTC (D-1 12:00)',
        description: 'Standard UK Day-Ahead wholesale market benchmark.',
        isDefault: true,
        group: 'Day-Ahead Auction Cutoffs',
      },
    ]);
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
        cutoffType: 'd1_1200',
        cutoffDescription: 'Standard UK Day-Ahead wholesale market benchmark.',
        alignment: 'exact',
        unit: 'MW',
        signConvention: 'error = forecast - actual',
      },
      metrics: {
        mae: 2002.91,
        rmse: 2470.08,
        bias: 1805.86,
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
          forecastPublishTime: '2025-12-31T11:30:00Z',
          leadHours: 12.5,
          error: 2000,
          absError: 2000,
          status: 'MATCHED',
        },
      ],
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Mean Absolute Error')).toBeInTheDocument();
      expect(screen.getByText('2,002.91')).toBeInTheDocument();
      expect(screen.getByText('Root Mean Sq Error')).toBeInTheDocument();
      expect(screen.getByText('2,470.08')).toBeInTheDocument();
      expect(screen.getByText('Forecast Bias')).toBeInTheDocument();
      expect(screen.getByText('1,805.86')).toBeInTheDocument();
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

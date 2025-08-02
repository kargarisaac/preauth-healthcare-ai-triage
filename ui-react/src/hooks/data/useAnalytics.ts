import { useState, useEffect, useCallback } from 'react';
import { 
  AnalyticsDashboardData, 
  AnalyticsMetrics, 
  DateRangePreset,
  AnalyticsApiResponse 
} from '../../types/analytics';

interface UseAnalyticsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // in seconds
  dateRange?: DateRangePreset;
}

interface UseAnalyticsReturn {
  data: AnalyticsDashboardData | null;
  metrics: AnalyticsMetrics | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
  setDateRange: (range: DateRangePreset) => void;
  exportData: (format: 'json' | 'csv' | 'excel') => Promise<void>;
}

export const useAnalytics = (options: UseAnalyticsOptions = {}): UseAnalyticsReturn => {
  const {
    autoRefresh = true,
    refreshInterval = 30, // 30 seconds default
    dateRange
  } = options;

  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [currentDateRange, setCurrentDateRange] = useState<DateRangePreset | undefined>(dateRange);

  const fetchAnalyticsData = useCallback(async () => {
    try {
      setError(null);
      const params = new URLSearchParams();
      
      if (currentDateRange) {
        params.append('start_date', currentDateRange.startDate.toISOString());
        params.append('end_date', currentDateRange.endDate.toISOString());
      }

      const response = await fetch(`/api/analytics?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: AnalyticsApiResponse<AnalyticsDashboardData> = await response.json();
      
      if (result.success && result.data) {
        setData(result.data);
        setLastUpdated(new Date());
      } else {
        throw new Error(result.error || 'Failed to fetch analytics data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('Analytics data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [currentDateRange]);

  const refresh = useCallback(async () => {
    setLoading(true);
    await fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  const setDateRange = useCallback((range: DateRangePreset) => {
    setCurrentDateRange(range);
  }, []);

  const exportData = useCallback(async (format: 'json' | 'csv' | 'excel') => {
    if (!data) return;

    try {
      const params = new URLSearchParams();
      params.append('format', format);
      
      if (currentDateRange) {
        params.append('start_date', currentDateRange.startDate.toISOString());
        params.append('end_date', currentDateRange.endDate.toISOString());
      }

      const response = await fetch(`/api/analytics/export?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analytics-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
      throw err;
    }
  }, [data, currentDateRange]);

  // Initial data fetch
  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAnalyticsData();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAnalyticsData]);

  return {
    data,
    metrics: data?.metrics || null,
    loading,
    error,
    lastUpdated,
    refresh,
    setDateRange,
    exportData
  };
};
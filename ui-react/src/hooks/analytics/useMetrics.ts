import { useState, useEffect, useMemo } from 'react';
import { 
  AnalyticsMetrics, 
  ProcessingTrend, 
  FormatDistribution, 
  ProviderPerformance,
  CostSavingsBreakdown,
  QualityMetrics 
} from '../../types/analytics';

interface UseMetricsOptions {
  refreshInterval?: number; // in seconds
  dateRange?: {
    start: Date;
    end: Date;
  };
  aggregationLevel?: 'hourly' | 'daily' | 'weekly' | 'monthly';
}

interface KPICalculation {
  current: number;
  previous: number;
  change: number;
  changePercentage: number;
  trend: 'up' | 'down' | 'stable';
  target?: number;
  status: 'good' | 'warning' | 'critical';
}

interface UseMetricsReturn {
  // Core metrics
  metrics: AnalyticsMetrics | null;
  loading: boolean;
  error: string | null;
  
  // Calculated KPIs
  kpis: {
    volume: KPICalculation;
    processingTime: KPICalculation;
    automationRate: KPICalculation;
    successRate: KPICalculation;
    costSavings: KPICalculation;
    qualityScore: KPICalculation;
    errorRate: KPICalculation;
    roi: KPICalculation;
  };
  
  // Benchmark comparisons
  benchmarks: {
    industryAverage: Record<string, number>;
    bestInClass: Record<string, number>;
    ourPosition: 'leading' | 'average' | 'lagging';
  };
  
  // Utility functions
  calculateGrowthRate: (current: number, previous: number) => number;
  formatMetric: (value: number, type: 'currency' | 'percentage' | 'number' | 'time') => string;
  getMetricStatus: (value: number, target: number, thresholds: { warning: number; critical: number }) => 'good' | 'warning' | 'critical';
  
  // Actions
  refresh: () => Promise<void>;
  exportMetrics: (format: 'json' | 'csv' | 'excel') => Promise<void>;
}

// Mock data generators for demonstration
const generateMockMetrics = (): AnalyticsMetrics => ({
  totalProcessed: Math.round(Math.random() * 100000 + 50000),
  dailyVolume: Math.round(Math.random() * 1000 + 500),
  monthlyVolume: Math.round(Math.random() * 20000 + 15000),
  volumeGrowthRate: Math.random() * 0.3 + 0.1, // 10-40% growth
  
  automationRate: Math.random() * 0.3 + 0.7, // 70-100%
  manualTouchPoints: Math.round(Math.random() * 50 + 10),
  avgProcessingTime: Math.random() * 600 + 300, // 5-15 minutes in seconds
  slaCompliance: Math.random() * 0.2 + 0.8, // 80-100%
  
  dataQualityScore: Math.random() * 0.2 + 0.8, // 80-100%
  errorRate: Math.random() * 0.05, // 0-5%
  successRate: Math.random() * 0.1 + 0.9, // 90-100%
  reprocessingRate: Math.random() * 0.03, // 0-3%
  
  costSavings: Math.round(Math.random() * 50000 + 25000),
  roiPercentage: Math.random() * 100 + 150, // 150-250%
  avgCostPerTransaction: Math.random() * 10 + 5, // 5-15 AED
  totalSavingsYTD: Math.round(Math.random() * 500000 + 250000),
  
  providerSatisfactionScore: Math.random() * 1.5 + 3.5, // 3.5-5.0 out of 5
  memberSatisfactionScore: Math.random() * 1.0 + 4.0, // 4.0-5.0 out of 5
  avgResponseTime: Math.random() * 30 + 15, // 15-45 minutes
  firstCallResolution: Math.random() * 0.2 + 0.75 // 75-95%
});

const calculateKPI = (
  current: number,
  previous: number,
  target?: number,
  thresholds?: { warning: number; critical: number }
): KPICalculation => {
  const change = current - previous;
  const changePercentage = previous !== 0 ? (change / previous) * 100 : 0;
  
  let trend: 'up' | 'down' | 'stable' = 'stable';
  if (Math.abs(changePercentage) > 1) { // 1% threshold for stability
    trend = changePercentage > 0 ? 'up' : 'down';
  }
  
  let status: 'good' | 'warning' | 'critical' = 'good';
  if (target && thresholds) {
    const deviation = Math.abs(current - target) / target;
    if (deviation > thresholds.critical) {
      status = 'critical';
    } else if (deviation > thresholds.warning) {
      status = 'warning';
    }
  }
  
  return {
    current,
    previous,
    change,
    changePercentage,
    trend,
    target,
    status
  };
};

export const useMetrics = (options: UseMetricsOptions = {}): UseMetricsReturn => {
  const { refreshInterval = 60, dateRange, aggregationLevel = 'daily' } = options;
  
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [previousMetrics, setPreviousMetrics] = useState<AnalyticsMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch metrics data
  const fetchMetrics = async () => {
    try {
      setError(null);
      
      // Store previous metrics before updating
      if (metrics) {
        setPreviousMetrics(metrics);
      }
      
      // Mock API call - replace with actual API
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
      const newMetrics = generateMockMetrics();
      setMetrics(newMetrics);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  // Calculate KPIs
  const kpis = useMemo(() => {
    if (!metrics || !previousMetrics) {
      // Return default KPIs with current values only
      if (metrics) {
        return {
          volume: calculateKPI(metrics.dailyVolume, metrics.dailyVolume, 1000),
          processingTime: calculateKPI(metrics.avgProcessingTime / 60, metrics.avgProcessingTime / 60, 15),
          automationRate: calculateKPI(metrics.automationRate * 100, metrics.automationRate * 100, 85),
          successRate: calculateKPI(metrics.successRate * 100, metrics.successRate * 100, 95),
          costSavings: calculateKPI(metrics.costSavings, metrics.costSavings),
          qualityScore: calculateKPI(metrics.dataQualityScore * 100, metrics.dataQualityScore * 100, 90),
          errorRate: calculateKPI(metrics.errorRate * 100, metrics.errorRate * 100, 5),
          roi: calculateKPI(metrics.roiPercentage, metrics.roiPercentage, 200)
        };
      }
      return {} as any;
    }

    return {
      volume: calculateKPI(
        metrics.dailyVolume, 
        previousMetrics.dailyVolume, 
        1000, 
        { warning: 0.1, critical: 0.2 }
      ),
      processingTime: calculateKPI(
        metrics.avgProcessingTime / 60, 
        previousMetrics.avgProcessingTime / 60, 
        15, 
        { warning: 0.2, critical: 0.4 }
      ),
      automationRate: calculateKPI(
        metrics.automationRate * 100, 
        previousMetrics.automationRate * 100, 
        85, 
        { warning: 0.1, critical: 0.2 }
      ),
      successRate: calculateKPI(
        metrics.successRate * 100, 
        previousMetrics.successRate * 100, 
        95, 
        { warning: 0.05, critical: 0.1 }
      ),
      costSavings: calculateKPI(
        metrics.costSavings, 
        previousMetrics.costSavings
      ),
      qualityScore: calculateKPI(
        metrics.dataQualityScore * 100, 
        previousMetrics.dataQualityScore * 100, 
        90, 
        { warning: 0.1, critical: 0.2 }
      ),
      errorRate: calculateKPI(
        metrics.errorRate * 100, 
        previousMetrics.errorRate * 100, 
        5, 
        { warning: 0.5, critical: 1.0 }
      ),
      roi: calculateKPI(
        metrics.roiPercentage, 
        previousMetrics.roiPercentage, 
        200, 
        { warning: 0.15, critical: 0.3 }
      )
    };
  }, [metrics, previousMetrics]);

  // Industry benchmarks (mock data)
  const benchmarks = useMemo(() => {
    const industryAverage = {
      automationRate: 65,
      processingTime: 25, // minutes
      successRate: 88,
      errorRate: 8,
      qualityScore: 75,
      roi: 180
    };

    const bestInClass = {
      automationRate: 92,
      processingTime: 8,
      successRate: 97,
      errorRate: 1.5,
      qualityScore: 95,
      roi: 350
    };

    let ourPosition: 'leading' | 'average' | 'lagging' = 'average';
    
    if (metrics) {
      const ourAutomation = metrics.automationRate * 100;
      const ourProcessingTime = metrics.avgProcessingTime / 60;
      const ourSuccess = metrics.successRate * 100;
      
      const leadingCount = [
        ourAutomation > bestInClass.automationRate * 0.9,
        ourProcessingTime < bestInClass.processingTime * 1.2,
        ourSuccess > bestInClass.successRate * 0.95
      ].filter(Boolean).length;
      
      if (leadingCount >= 2) {
        ourPosition = 'leading';
      } else if (leadingCount === 0) {
        ourPosition = 'lagging';
      }
    }

    return {
      industryAverage,
      bestInClass,
      ourPosition
    };
  }, [metrics]);

  // Utility functions
  const calculateGrowthRate = (current: number, previous: number): number => {
    if (previous === 0) return 0;
    return ((current - previous) / previous) * 100;
  };

  const formatMetric = (value: number, type: 'currency' | 'percentage' | 'number' | 'time'): string => {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-AE', {
          style: 'currency',
          currency: 'AED',
          minimumFractionDigits: 0
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'time':
        const hours = Math.floor(value / 60);
        const minutes = Math.round(value % 60);
        return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
      case 'number':
      default:
        return value.toLocaleString();
    }
  };

  const getMetricStatus = (
    value: number, 
    target: number, 
    thresholds: { warning: number; critical: number }
  ): 'good' | 'warning' | 'critical' => {
    const deviation = Math.abs(value - target) / target;
    if (deviation > thresholds.critical) return 'critical';
    if (deviation > thresholds.warning) return 'warning';
    return 'good';
  };

  const refresh = async () => {
    setLoading(true);
    await fetchMetrics();
  };

  const exportMetrics = async (format: 'json' | 'csv' | 'excel') => {
    if (!metrics) return;

    try {
      const data = {
        timestamp: new Date().toISOString(),
        dateRange,
        aggregationLevel,
        metrics,
        kpis,
        benchmarks
      };

      let blob: Blob;
      let filename: string;

      switch (format) {
        case 'json':
          blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
          filename = `metrics-${new Date().toISOString().split('T')[0]}.json`;
          break;
        case 'csv':
          const csv = Object.entries(metrics)
            .map(([key, value]) => `${key},${value}`)
            .join('\n');
          blob = new Blob([csv], { type: 'text/csv' });
          filename = `metrics-${new Date().toISOString().split('T')[0]}.csv`;
          break;
        case 'excel':
          // For Excel, we'll use CSV format as a fallback
          const excelCsv = Object.entries(metrics)
            .map(([key, value]) => `${key},${value}`)
            .join('\n');
          blob = new Blob([excelCsv], { type: 'application/vnd.ms-excel' });
          filename = `metrics-${new Date().toISOString().split('T')[0]}.xlsx`;
          break;
        default:
          return;
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      throw err;
    }
  };

  // Initial load and refresh interval
  useEffect(() => {
    fetchMetrics();
  }, [dateRange, aggregationLevel]);

  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchMetrics, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [refreshInterval]);

  return {
    metrics,
    loading,
    error,
    kpis,
    benchmarks,
    calculateGrowthRate,
    formatMetric,
    getMetricStatus,
    refresh,
    exportMetrics
  };
};
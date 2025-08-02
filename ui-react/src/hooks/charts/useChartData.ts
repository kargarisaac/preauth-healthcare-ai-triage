import { useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import {
  ProcessingTrend,
  FormatDistribution,
  ProviderPerformance,
  CostSavingsBreakdown,
  TimeBasedHeatmap,
  GeographicData,
  LineChartData,
  PieChartData,
  BarChartData,
  GaugeChartData,
} from '../../types/analytics';

// Color palette for charts
const CHART_COLORS = {
  primary: '#0066cc',
  secondary: '#00a86b',
  accent: '#ff6b35',
  warning: '#ffd23f',
  error: '#dc3545',
  success: '#28a745',
  info: '#17a2b8',
  formats: {
    eClaimLink: '#0066cc',
    Shafafiya: '#00a86b',
    CSV: '#ff6b35',
    'Claims CSV': '#ffd23f',
    'Clinical CSV': '#dc3545'
  },
  emirates: {
    Dubai: '#0066cc',
    'Abu Dhabi': '#00a86b',
    Sharjah: '#ff6b35',
    Ajman: '#ffd23f',
    Fujairah: '#dc3545',
    'Ras Al Khaimah': '#17a2b8',
    'Umm Al Quwain': '#6c757d'
  }
};

interface UseChartDataReturn {
  // Line Chart Data
  processingTrendData: LineChartData[];
  volumeTrendData: LineChartData[];
  performanceTrendData: LineChartData[];
  
  // Pie Chart Data
  formatDistributionData: PieChartData[];
  statusDistributionData: PieChartData[];
  geographicDistributionData: PieChartData[];
  
  // Bar Chart Data
  providerPerformanceData: BarChartData[];
  costSavingsData: BarChartData[];
  qualityMetricsData: BarChartData[];
  
  // Gauge Chart Data
  automationRateGauge: GaugeChartData;
  qualityScoreGauge: GaugeChartData;
  slaComplianceGauge: GaugeChartData;
  
  // Heatmap Data
  processingHeatmapData: Array<{
    day: string;
    hour: number;
    value: number;
    intensity: number;
  }>;
  
  // Utility functions
  formatCurrency: (value: number) => string;
  formatPercentage: (value: number) => string;
  formatDuration: (seconds: number) => string;
}

export const useChartData = (
  trends: ProcessingTrend[] = [],
  formatDistribution: FormatDistribution[] = [],
  providerPerformance: ProviderPerformance[] = [],
  costSavings: CostSavingsBreakdown[] = [],
  heatmapData: TimeBasedHeatmap[] = [],
  geographicData: GeographicData[] = [],
  metrics?: {
    automationRate: number;
    dataQualityScore: number;
    slaCompliance: number;
    successRate: number;
    errorRate: number;
  }
): UseChartDataReturn => {
  
  // Processing Trend Line Charts
  const processingTrendData = useMemo((): LineChartData[] => {
    if (!trends.length) return [];
    
    return [
      {
        id: 'volume',
        name: 'Daily Volume',
        color: CHART_COLORS.primary,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: trend.volume,
          label: `${trend.volume} requests`,
          metadata: { date: trend.date, volume: trend.volume }
        }))
      },
      {
        id: 'processing_time',
        name: 'Avg Processing Time (min)',
        color: CHART_COLORS.secondary,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: Math.round(trend.processingTime / 60),
          label: `${Math.round(trend.processingTime / 60)} minutes`,
          metadata: { date: trend.date, processingTime: trend.processingTime }
        }))
      },
      {
        id: 'success_rate',
        name: 'Success Rate (%)',
        color: CHART_COLORS.success,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: Math.round(trend.successRate * 100),
          label: `${Math.round(trend.successRate * 100)}%`,
          metadata: { date: trend.date, successRate: trend.successRate }
        }))
      }
    ];
  }, [trends]);

  const volumeTrendData = useMemo((): LineChartData[] => {
    if (!trends.length) return [];
    
    return [
      {
        id: 'volume_trend',
        name: 'Processing Volume',
        color: CHART_COLORS.primary,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: trend.volume,
          label: `${trend.volume} requests processed`
        }))
      }
    ];
  }, [trends]);

  const performanceTrendData = useMemo((): LineChartData[] => {
    if (!trends.length) return [];
    
    return [
      {
        id: 'automation_rate',
        name: 'Automation Rate',
        color: CHART_COLORS.info,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: Math.round(trend.automationRate * 100),
          label: `${Math.round(trend.automationRate * 100)}% automated`
        }))
      },
      {
        id: 'error_rate',
        name: 'Error Rate',
        color: CHART_COLORS.error,
        data: trends.map(trend => ({
          x: format(parseISO(trend.date), 'MMM dd'),
          y: trend.errorCount,
          label: `${trend.errorCount} errors`
        }))
      }
    ];
  }, [trends]);

  // Pie Chart Data
  const formatDistributionData = useMemo((): PieChartData[] => {
    return formatDistribution.map(format => ({
      name: format.format,
      value: format.count,
      percentage: format.percentage,
      color: CHART_COLORS.formats[format.format] || CHART_COLORS.primary
    }));
  }, [formatDistribution]);

  const statusDistributionData = useMemo((): PieChartData[] => {
    if (!metrics) return [];
    
    const approved = metrics.successRate * 100;
    const errors = metrics.errorRate * 100;
    const pending = 100 - approved - errors;
    
    return [
      { name: 'Approved', value: approved, percentage: approved, color: CHART_COLORS.success },
      { name: 'Pending', value: pending, percentage: pending, color: CHART_COLORS.warning },
      { name: 'Errors', value: errors, percentage: errors, color: CHART_COLORS.error }
    ];
  }, [metrics]);

  const geographicDistributionData = useMemo((): PieChartData[] => {
    return geographicData.map(geo => ({
      name: geo.emirate,
      value: geo.requests,
      percentage: (geo.requests / geographicData.reduce((sum, g) => sum + g.requests, 0)) * 100,
      color: CHART_COLORS.emirates[geo.emirate] || CHART_COLORS.primary
    }));
  }, [geographicData]);

  // Bar Chart Data
  const providerPerformanceData = useMemo((): BarChartData[] => {
    return providerPerformance
      .sort((a, b) => b.qualityScore - a.qualityScore)
      .slice(0, 10) // Top 10 providers
      .map(provider => ({
        category: provider.providerName,
        value: Math.round(provider.qualityScore * 100),
        color: provider.qualityScore > 0.8 ? CHART_COLORS.success : 
               provider.qualityScore > 0.6 ? CHART_COLORS.warning : CHART_COLORS.error,
        trend: provider.qualityScore > 0.8 ? 'up' : 
               provider.qualityScore > 0.6 ? 'stable' : 'down'
      }));
  }, [providerPerformance]);

  const costSavingsData = useMemo((): BarChartData[] => {
    return costSavings.map(saving => ({
      category: saving.category,
      value: saving.amount,
      color: saving.trend === 'up' ? CHART_COLORS.success :
             saving.trend === 'down' ? CHART_COLORS.error : CHART_COLORS.info,
      trend: saving.trend
    }));
  }, [costSavings]);

  const qualityMetricsData = useMemo((): BarChartData[] => {
    if (!metrics) return [];
    
    return [
      {
        category: 'Data Quality',
        value: Math.round(metrics.dataQualityScore * 100),
        color: CHART_COLORS.primary
      },
      {
        category: 'Success Rate',
        value: Math.round(metrics.successRate * 100),
        color: CHART_COLORS.success
      },
      {
        category: 'SLA Compliance',
        value: Math.round(metrics.slaCompliance * 100),
        color: CHART_COLORS.info
      },
      {
        category: 'Automation Rate',
        value: Math.round(metrics.automationRate * 100),
        color: CHART_COLORS.secondary
      }
    ];
  }, [metrics]);

  // Gauge Chart Data
  const automationRateGauge = useMemo((): GaugeChartData => ({
    value: metrics?.automationRate ? Math.round(metrics.automationRate * 100) : 0,
    min: 0,
    max: 100,
    target: 85,
    thresholds: [
      { value: 60, color: CHART_COLORS.error, label: 'Low' },
      { value: 80, color: CHART_COLORS.warning, label: 'Good' },
      { value: 100, color: CHART_COLORS.success, label: 'Excellent' }
    ]
  }), [metrics]);

  const qualityScoreGauge = useMemo((): GaugeChartData => ({
    value: metrics?.dataQualityScore ? Math.round(metrics.dataQualityScore * 100) : 0,
    min: 0,
    max: 100,
    target: 90,
    thresholds: [
      { value: 70, color: CHART_COLORS.error, label: 'Poor' },
      { value: 85, color: CHART_COLORS.warning, label: 'Good' },
      { value: 100, color: CHART_COLORS.success, label: 'Excellent' }
    ]
  }), [metrics]);

  const slaComplianceGauge = useMemo((): GaugeChartData => ({
    value: metrics?.slaCompliance ? Math.round(metrics.slaCompliance * 100) : 0,
    min: 0,
    max: 100,
    target: 95,
    thresholds: [
      { value: 80, color: CHART_COLORS.error, label: 'Below Target' },
      { value: 95, color: CHART_COLORS.warning, label: 'Meeting Target' },
      { value: 100, color: CHART_COLORS.success, label: 'Exceeding Target' }
    ]
  }), [metrics]);

  // Heatmap Data
  const processingHeatmapData = useMemo(() => {
    return heatmapData.map(item => ({
      day: item.day,
      hour: item.hour,
      value: item.volume,
      intensity: item.intensity
    }));
  }, [heatmapData]);

  // Utility functions
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value / 100);
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m ${seconds % 60}s`;
  };

  return {
    processingTrendData,
    volumeTrendData,
    performanceTrendData,
    formatDistributionData,
    statusDistributionData,
    geographicDistributionData,
    providerPerformanceData,
    costSavingsData,
    qualityMetricsData,
    automationRateGauge,
    qualityScoreGauge,
    slaComplianceGauge,
    processingHeatmapData,
    formatCurrency,
    formatPercentage,
    formatDuration
  };
};
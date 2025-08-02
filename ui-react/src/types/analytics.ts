// Analytics and Metrics Types for Healthcare Dashboard

export interface AnalyticsMetrics {
  // Processing Volume Metrics
  totalProcessed: number;
  dailyVolume: number;
  monthlyVolume: number;
  volumeGrowthRate: number;

  // Automation & Efficiency Metrics
  automationRate: number;
  manualTouchPoints: number;
  avgProcessingTime: number; // in seconds
  slaCompliance: number; // percentage

  // Quality & Performance Metrics
  dataQualityScore: number;
  errorRate: number;
  successRate: number;
  reprocessingRate: number;

  // Financial Metrics
  costSavings: number;
  roiPercentage: number;
  avgCostPerTransaction: number;
  totalSavingsYTD: number;

  // Provider & Member Metrics
  providerSatisfactionScore: number;
  memberSatisfactionScore: number;
  avgResponseTime: number; // in minutes
  firstCallResolution: number; // percentage
}

export interface ProcessingTrend {
  date: string;
  volume: number;
  processingTime: number;
  successRate: number;
  errorCount: number;
  automationRate: number;
}

export interface FormatDistribution {
  format: 'eClaimLink' | 'Shafafiya' | 'CSV' | 'Claims CSV' | 'Clinical CSV';
  count: number;
  percentage: number;
  avgProcessingTime: number;
  successRate: number;
}

export interface ProviderPerformance {
  providerId: string;
  providerName: string;
  totalRequests: number;
  approvalRate: number;
  avgResponseTime: number;
  qualityScore: number;
  costSavings: number;
  satisfactionScore: number;
}

export interface SystemHealth {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  apiResponseTime: number;
  errorRate: number;
  uptime: number; // in seconds
  status: 'healthy' | 'warning' | 'critical';
}

export interface CostSavingsBreakdown {
  category: string;
  amount: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
  comparison: number; // vs previous period
}

export interface QualityMetrics {
  metric: string;
  current: number;
  target: number;
  trend: 'improving' | 'stable' | 'declining';
  benchmark: number;
  unit: string;
}

export interface TimeBasedHeatmap {
  hour: number;
  day: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
  volume: number;
  intensity: number; // 0-1 for color mapping
}

export interface GeographicData {
  emirate: 'Dubai' | 'Abu Dhabi' | 'Sharjah' | 'Ajman' | 'Fujairah' | 'Ras Al Khaimah' | 'Umm Al Quwain';
  requests: number;
  approvalRate: number;
  avgProcessingTime: number;
  topProviders: string[];
}

export interface AlertThreshold {
  id: string;
  metric: keyof AnalyticsMetrics;
  name: string;
  warningThreshold: number;
  criticalThreshold: number;
  currentValue: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  lastTriggered?: string;
}

export interface RealTimeUpdate {
  timestamp: string;
  type: 'metric_update' | 'alert' | 'system_status';
  data: any;
  priority: 'low' | 'medium' | 'high';
}

// Chart Data Types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
  metadata?: Record<string, any>;
}

export interface LineChartData {
  id: string;
  name: string;
  data: ChartDataPoint[];
  color: string;
}

export interface PieChartData {
  name: string;
  value: number;
  percentage: number;
  color: string;
}

export interface BarChartData {
  category: string;
  value: number;
  color?: string;
  trend?: 'up' | 'down' | 'stable';
}

export interface GaugeChartData {
  value: number;
  min: number;
  max: number;
  target?: number;
  thresholds: Array<{
    value: number;
    color: string;
    label: string;
  }>;
}

// Dashboard Configuration Types
export interface DashboardConfig {
  layout: 'grid' | 'columns' | 'rows';
  refreshInterval: number; // in seconds
  timezone: string;
  currency: 'AED' | 'USD';
  dateFormat: string;
  theme: 'light' | 'dark' | 'auto';
}

export interface DashboardWidget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'alert' | 'custom';
  title: string;
  size: 'small' | 'medium' | 'large' | 'xl';
  position: {
    row: number;
    col: number;
    width: number;
    height: number;
  };
  config: Record<string, any>;
  isVisible: boolean;
  lastUpdated: string;
}

export interface DateRangePreset {
  id: string;
  label: string;
  startDate: Date;
  endDate: Date;
  isCustom: boolean;
}

// Export/Report Types
export interface AnalyticsExportOptions {
  format: 'png' | 'pdf' | 'excel' | 'csv';
  includeCharts: boolean;
  includeData: boolean;
  dateRange: {
    start: string;
    end: string;
  };
  widgets: string[]; // widget IDs to include
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  widgets: string[];
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly';
    time: string;
    recipients: string[];
  };
}

// API Response Types for Analytics
export interface AnalyticsApiResponse<T = any> {
  success: boolean;
  data: T;
  metadata: {
    generatedAt: string;
    dataRange: {
      start: string;
      end: string;
    };
    totalRecords: number;
    cacheStatus: 'fresh' | 'cached' | 'stale';
  };
  error?: string;
}

export interface AnalyticsDashboardData {
  metrics: AnalyticsMetrics;
  trends: ProcessingTrend[];
  formatDistribution: FormatDistribution[];
  providerPerformance: ProviderPerformance[];
  systemHealth: SystemHealth;
  costSavings: CostSavingsBreakdown[];
  qualityMetrics: QualityMetrics[];
  heatmapData: TimeBasedHeatmap[];
  geographicData: GeographicData[];
  alerts: AlertThreshold[];
}

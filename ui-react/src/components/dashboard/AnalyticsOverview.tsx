import React, { useState } from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  Target,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  RefreshCw,
  Download,
  Calendar,
  Filter
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { AnalyticsMetrics, AnalyticsDashboardData } from '../../types/analytics';
import { useAnalytics } from '../../hooks/data/useAnalytics';
import type { DashboardSummaryResponse } from '../../types/api';

interface AnalyticsOverviewProps {
  data?: AnalyticsDashboardData | null;
  pipelineData?: DashboardSummaryResponse | null;
  isLoading?: boolean;
  className?: string;
}

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  target?: number;
  unit: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  description?: string;
  isPercentage?: boolean;
}

interface AlertIndicatorProps {
  alerts: Array<{
    id: string;
    type: 'warning' | 'critical' | 'info';
    message: string;
    timestamp: string;
  }>;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  change,
  target,
  unit,
  icon,
  color,
  description,
  isPercentage = false
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200'
  };

  const formatValue = (val: string | number) => {
    if (typeof val === 'number') {
      if (isPercentage) {
        return `${val.toFixed(1)}%`;
      }
      if (unit === 'AED') {
        return new Intl.NumberFormat('en-AE', {
          style: 'currency',
          currency: 'AED',
          minimumFractionDigits: 0
        }).format(val);
      }
      if (unit === 'min') {
        return `${val.toFixed(1)} min`;
      }
      return val.toLocaleString();
    }
    return val;
  };

  const isPositiveChange = change !== undefined && change > 0;
  const isOnTarget = target !== undefined && typeof value === 'number' &&
    Math.abs(value - target) <= (target * 0.05);

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg border ${colorClasses[color]}`}>
          {icon}
        </div>
        {target !== undefined && (
          <div className={`text-xs px-2 py-1 rounded ${
            isOnTarget ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
          }`}>
            {isOnTarget ? 'On Target' : 'Off Target'}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>

        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-gray-900">
            {formatValue(value)}
          </span>
          {!isPercentage && unit !== 'AED' && unit !== 'min' && (
            <span className="text-sm text-gray-500">{unit}</span>
          )}
        </div>

        {change !== undefined && (
          <div className={`flex items-center text-sm ${
            isPositiveChange ? 'text-green-600' : 'text-red-600'
          }`}>
            {isPositiveChange ? (
              <TrendingUp className="h-3 w-3 mr-1" />
            ) : (
              <TrendingDown className="h-3 w-3 mr-1" />
            )}
            <span>{Math.abs(change).toFixed(1)}% vs last period</span>
          </div>
        )}

        {target !== undefined && (
          <div className="text-xs text-gray-500">
            Target: {isPercentage ? `${target}%` : formatValue(target)}
          </div>
        )}

        {description && (
          <p className="text-xs text-gray-500 mt-2">{description}</p>
        )}
      </div>
    </Card>
  );
};

const AlertIndicator: React.FC<AlertIndicatorProps> = ({ alerts }) => {
  const criticalAlerts = alerts.filter(a => a.type === 'critical').length;
  const warningAlerts = alerts.filter(a => a.type === 'warning').length;

  if (alerts.length === 0) {
    return (
      <div className="flex items-center text-green-600">
        <CheckCircle className="h-4 w-4 mr-2" />
        <span className="text-sm">All systems operational</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4">
      {criticalAlerts > 0 && (
        <div className="flex items-center text-red-600">
          <AlertTriangle className="h-4 w-4 mr-1" />
          <span className="text-sm font-medium">{criticalAlerts} Critical</span>
        </div>
      )}
      {warningAlerts > 0 && (
        <div className="flex items-center text-yellow-600">
          <AlertTriangle className="h-4 w-4 mr-1" />
          <span className="text-sm">{warningAlerts} Warnings</span>
        </div>
      )}
    </div>
  );
};

export const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({
  data,
  pipelineData,
  isLoading = false,
  className = ''
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState('today');
  const { refresh, exportData } = useAnalytics();

  // Mock alerts for demonstration
  const mockAlerts = [
    {
      id: '1',
      type: 'warning' as const,
      message: 'Processing time above average',
      timestamp: new Date().toISOString()
    }
  ];

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="h-6 bg-gray-200 rounded w-48 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-64"></div>
            </div>
            <div className="flex space-x-2">
              <div className="h-8 bg-gray-200 rounded w-20"></div>
              <div className="h-8 bg-gray-200 rounded w-20"></div>
            </div>
          </div>

          {/* KPI Cards skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-40 bg-gray-200 rounded"></div>
            ))}
          </div>

          {/* Additional metrics skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!data?.metrics) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Data</h3>
          <p className="text-gray-600">Analytics data will appear here once processing begins.</p>
        </div>
      </div>
    );
  }

  const metrics = data.metrics;

  // Calculate period changes - mock for now
  const periodChanges = {
    volume: 12.5,
    processingTime: -8.3,
    automationRate: 5.2,
    costSavings: 15.7,
    successRate: 2.1,
    errorRate: -12.4,
    qualityScore: 3.8,
    roi: 18.9
  };

  // Use pipeline data if available, fallback to legacy analytics
  const pipelineMetrics = pipelineData?.data;
  
  const primaryKPIs = [
    {
      title: 'Daily Volume',
      value: pipelineMetrics?.processing_metrics.total_processed_today || metrics.dailyVolume,
      change: periodChanges.volume,
      unit: 'requests',
      icon: <Activity className="h-5 w-5" />,
      color: 'blue' as const,
      description: 'Total requests processed today'
    },
    {
      title: 'Processing Time',
      value: pipelineMetrics ? 
        (pipelineMetrics.processing_metrics.avg_processing_time_seconds / 60).toFixed(1) :
        Math.round(metrics.avgProcessingTime / 60),
      change: periodChanges.processingTime,
      target: 15,
      unit: 'min',
      icon: <Clock className="h-5 w-5" />,
      color: 'green' as const,
      description: 'Average time per request'
    },
    {
      title: 'Success Rate',
      value: pipelineMetrics ?
        Math.round(pipelineMetrics.processing_metrics.success_rate * 100) :
        Math.round(metrics.automationRate * 100),
      change: periodChanges.automationRate,
      target: 95,
      unit: '%',
      icon: <Target className="h-5 w-5" />,
      color: 'purple' as const,
      description: 'Successful processing rate',
      isPercentage: true
    },
    {
      title: 'Cost Per Request',
      value: pipelineMetrics ?
        `$${pipelineMetrics.processing_metrics.cost_per_request_usd.toFixed(3)}` :
        metrics.costSavings,
      change: periodChanges.costSavings,
      unit: pipelineMetrics ? 'USD' : 'AED',
      icon: <DollarSign className="h-5 w-5" />,
      color: 'green' as const,
      description: pipelineMetrics ? 'Average cost per processing request' : 'Monthly cost reduction'
    }
  ];

  const secondaryKPIs = [
    {
      title: 'Success Rate',
      value: Math.round(metrics.successRate * 100),
      change: periodChanges.successRate,
      target: 95,
      unit: '%',
      icon: <CheckCircle className="h-4 w-4" />,
      color: 'green' as const,
      isPercentage: true
    },
    {
      title: 'Error Rate',
      value: Math.round(metrics.errorRate * 100),
      change: periodChanges.errorRate,
      unit: '%',
      icon: <AlertTriangle className="h-4 w-4" />,
      color: 'red' as const,
      isPercentage: true
    },
    {
      title: 'Quality Score',
      value: Math.round(metrics.dataQualityScore * 100),
      change: periodChanges.qualityScore,
      target: 90,
      unit: '%',
      icon: <Target className="h-4 w-4" />,
      color: 'blue' as const,
      isPercentage: true
    },
    {
      title: 'ROI',
      value: Math.round(metrics.roiPercentage),
      change: periodChanges.roi,
      unit: '%',
      icon: <TrendingUp className="h-4 w-4" />,
      color: 'purple' as const,
      isPercentage: true
    }
  ];

  const periodOptions = [
    { value: 'today', label: 'Today' },
    { value: '7days', label: '7 Days' },
    { value: '30days', label: '30 Days' },
    { value: '90days', label: '90 Days' }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Overview</h2>
          <p className="text-gray-600">Real-time healthcare data processing insights</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {periodOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={refresh}
            className="flex items-center space-x-1"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => exportData('json')}
            className="flex items-center space-x-1"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-1">System Status</h3>
            <AlertIndicator alerts={mockAlerts} />
          </div>
          <div className="text-xs text-gray-500">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </Card>

      {/* Primary KPIs */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Performance Indicators</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {primaryKPIs.map((kpi, index) => (
            <KPICard key={index} {...kpi} />
          ))}
        </div>
      </div>

      {/* Secondary Metrics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {secondaryKPIs.map((kpi, index) => (
            <KPICard key={index} {...kpi} />
          ))}
        </div>
      </div>

      {/* Pipeline Decision Outcomes */}
      {pipelineMetrics && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Outcomes</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-2xl font-bold text-green-900">
                {pipelineMetrics.decision_outcomes.approved}
              </p>
              <p className="text-sm text-gray-600">Approved</p>
              <p className="text-xs text-gray-500 mt-1">Auto-authorized</p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
              <p className="text-2xl font-bold text-red-900">
                {pipelineMetrics.decision_outcomes.denied}
              </p>
              <p className="text-sm text-gray-600">Denied</p>
              <p className="text-xs text-gray-500 mt-1">Policy violations</p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Users className="h-8 w-8 text-yellow-500" />
              </div>
              <p className="text-2xl font-bold text-yellow-900">
                {pipelineMetrics.decision_outcomes.review_required}
              </p>
              <p className="text-sm text-gray-600">Review Required</p>
              <p className="text-xs text-gray-500 mt-1">Manual review needed</p>
            </div>
          </div>
        </Card>
      )}

      {/* Pipeline Efficiency */}
      {pipelineMetrics && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Efficiency</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm font-medium">Deterministic ($0.00)</span>
              </div>
              <span className="text-sm text-gray-900">
                {pipelineMetrics.pipeline_efficiency.deterministic_percentage.toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium">Hybrid (&lt;$0.10)</span>
              </div>
              <span className="text-sm text-gray-900">
                {pipelineMetrics.pipeline_efficiency.hybrid_percentage.toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <span className="text-sm font-medium">Agentic (&lt;$0.25)</span>
              </div>
              <span className="text-sm text-gray-900">
                {pipelineMetrics.pipeline_efficiency.agentic_percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* Recent Activity */}
      {pipelineMetrics?.recent_activity && pipelineMetrics.recent_activity.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {pipelineMetrics.recent_activity.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={clsx(
                    'w-2 h-2 rounded-full',
                    activity.outcome === 'APPROVE' ? 'bg-green-500' :
                    activity.outcome === 'DENY' ? 'bg-red-500' : 'bg-yellow-500'
                  )}></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {activity.patient_id}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(activity.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={clsx(
                    'text-sm font-medium',
                    activity.outcome === 'APPROVE' ? 'text-green-800' :
                    activity.outcome === 'DENY' ? 'text-red-800' : 'text-yellow-800'
                  )}>
                    {activity.outcome}
                  </p>
                  <p className="text-xs text-gray-500">
                    {activity.processing_time.toFixed(1)}s
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Legacy Summary Stats - shown if no pipeline data */}
      {!pipelineMetrics && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Users className="h-8 w-8 text-blue-500" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.totalProcessed.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">Total Requests Processed</p>
              <p className="text-xs text-gray-500 mt-1">All time</p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Clock className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(metrics.avgResponseTime)}
              </p>
              <p className="text-sm text-gray-600">Avg Response Time (min)</p>
              <p className="text-xs text-gray-500 mt-1">Within SLA targets</p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <DollarSign className="h-8 w-8 text-purple-500" />
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {new Intl.NumberFormat('en-AE', {
                  style: 'currency',
                  currency: 'AED',
                  minimumFractionDigits: 0
                }).format(metrics.totalSavingsYTD)}
              </p>
              <p className="text-sm text-gray-600">Total Savings YTD</p>
              <p className="text-xs text-gray-500 mt-1">
                {Math.round(metrics.roiPercentage)}% ROI achieved
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

import React from 'react';
import {
  Activity,
  Clock,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Users,
  Zap,
  Target,
  Award
} from 'lucide-react';
import Card from '../ui/Card';
import { AnalyticsMetrics } from '../../types/analytics';

interface MetricsGridProps {
  metrics: AnalyticsMetrics;
  isLoading?: boolean;
  showTrends?: boolean;
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    period: string;
  };
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'indigo';
  isLoading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'blue',
  isLoading = false
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-200'
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    stable: 'text-yellow-600'
  };

  if (isLoading) {
    return (
      <Card className="p-6 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-24"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
            <div className="h-3 bg-gray-200 rounded w-20"></div>
          </div>
          <div className="h-12 w-12 bg-gray-200 rounded-lg"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline space-x-2">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {trend && (
              <span className={`text-sm font-medium ${trendColors[trend.direction]}`}>
                {trend.direction === 'up' && '+'}
                {trend.value}% {trend.period}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg border ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};

export const MetricsGrid: React.FC<MetricsGridProps> = ({
  metrics,
  isLoading = false,
  showTrends = true,
  className = ''
}) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${Math.round(value * 100)}%`;
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  const formatNumber = (value: number): string => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  const metricsData = [
    {
      title: 'Total Processed',
      value: formatNumber(metrics.totalProcessed),
      subtitle: `${metrics.dailyVolume} today`,
      icon: <Activity className="h-6 w-6" />,
      color: 'blue' as const,
      trend: showTrends ? {
        value: metrics.volumeGrowthRate,
        direction: metrics.volumeGrowthRate > 0 ? 'up' : metrics.volumeGrowthRate < 0 ? 'down' : 'stable' as const,
        period: 'vs last month'
      } : undefined
    },
    {
      title: 'Automation Rate',
      value: formatPercentage(metrics.automationRate),
      subtitle: `${metrics.manualTouchPoints} manual interventions`,
      icon: <Zap className="h-6 w-6" />,
      color: 'green' as const,
      trend: showTrends ? {
        value: 12.5,
        direction: 'up' as const,
        period: 'this week'
      } : undefined
    },
    {
      title: 'Avg Processing Time',
      value: formatDuration(metrics.avgProcessingTime),
      subtitle: `${formatPercentage(metrics.slaCompliance)} SLA compliance`,
      icon: <Clock className="h-6 w-6" />,
      color: 'indigo' as const,
      trend: showTrends ? {
        value: 8.3,
        direction: 'down' as const,
        period: 'improvement'
      } : undefined
    },
    {
      title: 'Success Rate',
      value: formatPercentage(metrics.successRate),
      subtitle: `${formatPercentage(metrics.errorRate)} error rate`,
      icon: <CheckCircle className="h-6 w-6" />,
      color: 'green' as const,
      trend: showTrends ? {
        value: 2.1,
        direction: 'up' as const,
        period: 'this month'
      } : undefined
    },
    {
      title: 'Cost Savings YTD',
      value: formatCurrency(metrics.totalSavingsYTD),
      subtitle: `${formatPercentage(metrics.roiPercentage / 100)} ROI`,
      icon: <DollarSign className="h-6 w-6" />,
      color: 'purple' as const,
      trend: showTrends ? {
        value: metrics.roiPercentage,
        direction: 'up' as const,
        period: 'return on investment'
      } : undefined
    },
    {
      title: 'Data Quality Score',
      value: formatPercentage(metrics.dataQualityScore),
      subtitle: `${formatPercentage(metrics.reprocessingRate)} reprocessing rate`,
      icon: <Award className="h-6 w-6" />,
      color: 'yellow' as const,
      trend: showTrends ? {
        value: 3.7,
        direction: 'up' as const,
        period: 'quality improvement'
      } : undefined
    },
    {
      title: 'Provider Satisfaction',
      value: `${Math.round(metrics.providerSatisfactionScore * 100)}/100`,
      subtitle: `${Math.round(metrics.avgResponseTime)} min avg response`,
      icon: <Users className="h-6 w-6" />,
      color: 'blue' as const,
      trend: showTrends ? {
        value: 4.2,
        direction: 'up' as const,
        period: 'satisfaction score'
      } : undefined
    },
    {
      title: 'Member Satisfaction',
      value: `${Math.round(metrics.memberSatisfactionScore * 100)}/100`,
      subtitle: `${formatPercentage(metrics.firstCallResolution)} first call resolution`,
      icon: <Target className="h-6 w-6" />,
      color: 'green' as const,
      trend: showTrends ? {
        value: 6.1,
        direction: 'up' as const,
        period: 'member experience'
      } : undefined
    }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Key Performance Metrics</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Live Updates</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricsData.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.title}
            value={metric.value}
            subtitle={metric.subtitle}
            icon={metric.icon}
            color={metric.color}
            trend={metric.trend}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Processing Summary</h3>
            <TrendingUp className="h-5 w-5 text-green-500" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Monthly Volume</span>
              <span className="font-medium">{formatNumber(metrics.monthlyVolume)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Daily Average</span>
              <span className="font-medium">{formatNumber(Math.round(metrics.monthlyVolume / 30))}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Growth Rate</span>
              <span className={`font-medium ${metrics.volumeGrowthRate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {metrics.volumeGrowthRate > 0 ? '+' : ''}{metrics.volumeGrowthRate.toFixed(1)}%
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Efficiency Metrics</h3>
            <Zap className="h-5 w-5 text-blue-500" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Cost per Transaction</span>
              <span className="font-medium">{formatCurrency(metrics.avgCostPerTransaction)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Manual Touch Points</span>
              <span className="font-medium">{metrics.manualTouchPoints}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">SLA Compliance</span>
              <span className="font-medium text-green-600">{formatPercentage(metrics.slaCompliance)}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Financial Impact</h3>
            <DollarSign className="h-5 w-5 text-purple-500" />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Monthly Savings</span>
              <span className="font-medium">{formatCurrency(metrics.costSavings)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">ROI Percentage</span>
              <span className="font-medium text-green-600">{formatPercentage(metrics.roiPercentage / 100)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">YTD Total</span>
              <span className="font-medium">{formatCurrency(metrics.totalSavingsYTD)}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

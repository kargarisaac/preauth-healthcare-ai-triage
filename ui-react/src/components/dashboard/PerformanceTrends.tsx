import React, { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  Target,
  AlertTriangle,
  Calendar,
  Filter
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import {
  ProcessingTrend,
  ProviderPerformance,
  QualityMetrics
} from '../../types/analytics';

interface PerformanceTrendsProps {
  trends: ProcessingTrend[];
  providerPerformance: ProviderPerformance[];
  qualityMetrics: QualityMetrics[];
  isLoading?: boolean;
  className?: string;
}

interface TrendAnalysisCardProps {
  title: string;
  currentValue: number;
  previousValue: number;
  target?: number;
  unit: string;
  icon: React.ReactNode;
  color: 'green' | 'red' | 'blue' | 'yellow';
}

const TrendAnalysisCard: React.FC<TrendAnalysisCardProps> = ({
  title,
  currentValue,
  previousValue,
  target,
  unit,
  icon,
  color
}) => {
  const change = ((currentValue - previousValue) / previousValue) * 100;
  const isPositive = change > 0;
  const isOnTarget = target ? Math.abs(currentValue - target) <= (target * 0.05) : false; // Within 5% of target

  const colorClasses = {
    green: 'bg-green-50 text-green-600 border-green-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200'
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg border ${colorClasses[color]}`}>
          {icon}
        </div>
        {target && (
          <div className={`text-xs px-2 py-1 rounded ${isOnTarget ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
            {isOnTarget ? 'On Target' : 'Off Target'}
          </div>
        )}
      </div>

      <h4 className="text-sm font-medium text-gray-600 mb-1">{title}</h4>

      <div className="flex items-baseline space-x-2">
        <span className="text-xl font-bold text-gray-900">
          {currentValue.toFixed(1)}{unit}
        </span>
        <div className={`flex items-center text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          <span className="ml-1">{Math.abs(change).toFixed(1)}%</span>
        </div>
      </div>

      {target && (
        <div className="text-xs text-gray-500 mt-1">
          Target: {target.toFixed(1)}{unit}
        </div>
      )}
    </Card>
  );
};

export const PerformanceTrends: React.FC<PerformanceTrendsProps> = ({
  trends,
  providerPerformance,
  qualityMetrics,
  isLoading = false,
  className = ''
}) => {
  const [timeRange, setTimeRange] = useState('30days');
  const [selectedMetric, setSelectedMetric] = useState('all');

  // Transform trends data for charts
  const trendData = trends.map(trend => ({
    date: new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    volume: trend.volume,
    processingTime: Math.round(trend.processingTime / 60), // Convert to minutes
    successRate: Math.round(trend.successRate * 100),
    automationRate: Math.round(trend.automationRate * 100),
    errorCount: trend.errorCount,
    efficiency: Math.round((trend.successRate * trend.automationRate) * 100) // Combined efficiency score
  }));

  // Calculate performance metrics
  const currentPeriod = trendData.slice(-7); // Last 7 days
  const previousPeriod = trendData.slice(-14, -7); // Previous 7 days

  const calculateAverage = (data: any[], key: string) => {
    return data.reduce((sum, item) => sum + item[key], 0) / data.length;
  };

  const performanceMetrics = [
    {
      title: 'Avg Processing Time',
      currentValue: calculateAverage(currentPeriod, 'processingTime'),
      previousValue: calculateAverage(previousPeriod, 'processingTime'),
      target: 15, // 15 minutes target
      unit: 'min',
      icon: <Clock className="h-4 w-4" />,
      color: 'blue' as const
    },
    {
      title: 'Success Rate',
      currentValue: calculateAverage(currentPeriod, 'successRate'),
      previousValue: calculateAverage(previousPeriod, 'successRate'),
      target: 95,
      unit: '%',
      icon: <Target className="h-4 w-4" />,
      color: 'green' as const
    },
    {
      title: 'Automation Rate',
      currentValue: calculateAverage(currentPeriod, 'automationRate'),
      previousValue: calculateAverage(previousPeriod, 'automationRate'),
      target: 85,
      unit: '%',
      icon: <TrendingUp className="h-4 w-4" />,
      color: 'blue' as const
    },
    {
      title: 'Efficiency Score',
      currentValue: calculateAverage(currentPeriod, 'efficiency'),
      previousValue: calculateAverage(previousPeriod, 'efficiency'),
      target: 80,
      unit: '%',
      icon: <Target className="h-4 w-4" />,
      color: 'green' as const
    }
  ];

  // Top performing providers
  const topProviders = providerPerformance
    .sort((a, b) => b.qualityScore - a.qualityScore)
    .slice(0, 5);

  const timeRangeOptions = [
    { value: '7days', label: '7 Days' },
    { value: '30days', label: '30 Days' },
    { value: '90days', label: '90 Days' },
    { value: '1year', label: '1 Year' }
  ];

  const metricOptions = [
    { value: 'all', label: 'All Metrics' },
    { value: 'processing', label: 'Processing Time' },
    { value: 'success', label: 'Success Rate' },
    { value: 'automation', label: 'Automation' }
  ];

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-80 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Performance Trends Analysis</h2>
          <p className="text-sm text-gray-600">Historical performance analysis and trend monitoring</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {timeRangeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {metricOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Performance Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {performanceMetrics.map((metric, index) => (
          <TrendAnalysisCard key={index} {...metric} />
        ))}
      </div>

      {/* Main Trends Chart */}
      <Card className="p-6">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Historical Performance Trends</h3>
          <p className="text-sm text-gray-600">Key performance indicators over time</p>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                stroke="#666"
                fontSize={12}
              />
              <YAxis
                yAxisId="left"
                stroke="#666"
                fontSize={12}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#666"
                fontSize={12}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-medium text-gray-900">{label}</p>
                        {payload.map((entry: any, index: number) => (
                          <p key={index} className="text-sm" style={{ color: entry.color }}>
                            {entry.name}: {entry.value}
                            {entry.name.includes('Rate') && '%'}
                            {entry.name.includes('Time') && ' min'}
                          </p>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />

              {/* Reference lines for targets */}
              <ReferenceLine yAxisId="right" y={95} stroke="#dc3545" strokeDasharray="5 5" label="Success Target" />
              <ReferenceLine yAxisId="right" y={85} stroke="#0066cc" strokeDasharray="5 5" label="Automation Target" />

              <Bar
                yAxisId="left"
                dataKey="volume"
                fill="#0066cc40"
                name="Volume"
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="processingTime"
                stroke="#ff6b35"
                strokeWidth={2}
                dot={{ fill: '#ff6b35', strokeWidth: 2, r: 3 }}
                name="Processing Time (min)"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="successRate"
                stroke="#28a745"
                strokeWidth={2}
                dot={{ fill: '#28a745', strokeWidth: 2, r: 3 }}
                name="Success Rate (%)"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="automationRate"
                stroke="#0066cc"
                strokeWidth={2}
                dot={{ fill: '#0066cc', strokeWidth: 2, r: 3 }}
                name="Automation Rate (%)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Provider Performance Ranking */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Top Performing Providers</h3>
              <p className="text-sm text-gray-600">Ranked by quality score and efficiency</p>
            </div>
            <Users className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-3">
            {topProviders.map((provider, index) => (
              <div key={provider.providerId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    index === 0 ? 'bg-yellow-500' :
                    index === 1 ? 'bg-gray-400' :
                    index === 2 ? 'bg-yellow-600' : 'bg-blue-500'
                  }`}>
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{provider.providerName}</p>
                    <p className="text-sm text-gray-600">
                      {provider.totalRequests} requests | {Math.round(provider.approvalRate * 100)}% approval
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-900">
                    {Math.round(provider.qualityScore * 100)}%
                  </p>
                  <p className="text-sm text-gray-600">quality score</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Quality Metrics Breakdown */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Quality Metrics</h3>
              <p className="text-sm text-gray-600">Current vs target performance</p>
            </div>
            <Target className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            {qualityMetrics.map((metric, index) => {
              const progressPercentage = (metric.current / metric.target) * 100;
              const isOnTrack = progressPercentage >= 90;

              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{metric.measure}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">
                        {metric.current.toFixed(1)} / {metric.target.toFixed(1)} {metric.unit}
                      </span>
                      {metric.trend === 'improving' ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : metric.trend === 'declining' ? (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      ) : (
                        <div className="h-4 w-4" />
                      )}
                    </div>
                  </div>

                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isOnTrack ? 'bg-green-500' : progressPercentage >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{metric.description}</span>
                    <span className={isOnTrack ? 'text-green-600' : 'text-yellow-600'}>
                      {progressPercentage.toFixed(1)}% of target
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Error Analysis */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Error Rate Analysis</h3>
            <p className="text-sm text-gray-600">Error patterns and resolution trends</p>
          </div>
          <AlertTriangle className="h-5 w-5 text-yellow-500" />
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#666" fontSize={12} />
              <YAxis stroke="#666" fontSize={12} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-white p-3 border rounded-lg shadow-lg">
                        <p className="font-medium text-gray-900">{label}</p>
                        <p className="text-sm text-red-600">Errors: {payload[0]?.value}</p>
                        <p className="text-sm text-green-600">
                          Success Rate: {trendData.find(d => d.date === label)?.successRate}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="errorCount"
                stroke="#dc3545"
                fill="#dc354520"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};

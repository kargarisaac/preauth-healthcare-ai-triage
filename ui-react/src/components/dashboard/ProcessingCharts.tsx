import React, { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieChartIcon, Activity } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import {
  LineChartData,
  PieChartData,
  BarChartData,
  ProcessingTrend,
  FormatDistribution
} from '../../types/analytics';

interface ProcessingChartsProps {
  trends: ProcessingTrend[];
  formatDistribution: FormatDistribution[];
  isLoading?: boolean;
  className?: string;
}

interface ChartSelectorProps {
  activeChart: string;
  onChartChange: (chart: string) => void;
  charts: Array<{ id: string; label: string; icon: React.ReactNode }>;
}

const ChartSelector: React.FC<ChartSelectorProps> = ({ activeChart, onChartChange, charts }) => (
  <div className="flex space-x-2">
    {charts.map((chart) => (
      <Button
        key={chart.id}
        variant={activeChart === chart.id ? 'primary' : 'secondary'}
        size="sm"
        onClick={() => onChartChange(chart.id)}
        className="flex items-center space-x-2"
      >
        {chart.icon}
        <span>{chart.label}</span>
      </Button>
    ))}
  </div>
);

const CustomTooltip = ({ active, payload, label }: any) => {
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
};

const LoadingChart = () => (
  <div className="h-80 flex items-center justify-center">
    <div className="animate-pulse space-y-4 w-full">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 rounded w-4/6"></div>
      </div>
    </div>
  </div>
);

export const ProcessingCharts: React.FC<ProcessingChartsProps> = ({
  trends,
  formatDistribution,
  isLoading = false,
  className = ''
}) => {
  const [activeVolumeChart, setActiveVolumeChart] = useState('line');
  const [activePerformanceChart, setActivePerformanceChart] = useState('area');

  // Transform data for charts
  const volumeData = trends.map(trend => ({
    date: new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    volume: trend.volume,
    successRate: Math.round(trend.successRate * 100),
    errorCount: trend.errorCount,
    automationRate: Math.round(trend.automationRate * 100),
    processingTime: Math.round(trend.processingTime / 60) // Convert to minutes
  }));

  const formatData = formatDistribution.map(format => ({
    name: format.format,
    value: format.count,
    percentage: format.percentage,
    avgTime: Math.round(format.avgProcessingTime / 60),
    successRate: Math.round(format.successRate * 100)
  }));

  const COLORS = {
    primary: '#0066cc',
    secondary: '#00a86b',
    accent: '#ff6b35',
    warning: '#ffd23f',
    error: '#dc3545',
    success: '#28a745',
    info: '#17a2b8'
  };

  const PIE_COLORS = ['#0066cc', '#00a86b', '#ff6b35', '#ffd23f', '#dc3545'];

  const volumeCharts = [
    { id: 'line', label: 'Line', icon: <TrendingUp className="h-4 w-4" /> },
    { id: 'area', label: 'Area', icon: <Activity className="h-4 w-4" /> },
    { id: 'bar', label: 'Bar', icon: <BarChart3 className="h-4 w-4" /> }
  ];

  const performanceCharts = [
    { id: 'area', label: 'Area', icon: <Activity className="h-4 w-4" /> },
    { id: 'line', label: 'Line', icon: <TrendingUp className="h-4 w-4" /> }
  ];

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card className="p-6">
          <LoadingChart />
        </Card>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <LoadingChart />
          </Card>
          <Card className="p-6">
            <LoadingChart />
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Processing Volume Trends */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Processing Volume Trends</h3>
            <p className="text-sm text-gray-600">Daily processing volume and success rates over time</p>
          </div>
          <ChartSelector
            activeChart={activeVolumeChart}
            onChartChange={setActiveVolumeChart}
            charts={volumeCharts}
          />
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            {activeVolumeChart === 'line' ? (
              <LineChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  stroke="#666"
                  fontSize={12}
                />
                <YAxis
                  yAxisId="volume"
                  stroke="#666"
                  fontSize={12}
                />
                <YAxis
                  yAxisId="percentage"
                  orientation="right"
                  stroke="#666"
                  fontSize={12}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  yAxisId="volume"
                  type="monotone"
                  dataKey="volume"
                  stroke={COLORS.primary}
                  strokeWidth={3}
                  dot={{ fill: COLORS.primary, strokeWidth: 2, r: 4 }}
                  name="Volume"
                />
                <Line
                  yAxisId="percentage"
                  type="monotone"
                  dataKey="successRate"
                  stroke={COLORS.success}
                  strokeWidth={2}
                  dot={{ fill: COLORS.success, strokeWidth: 2, r: 3 }}
                  name="Success Rate (%)"
                />
              </LineChart>
            ) : activeVolumeChart === 'area' ? (
              <AreaChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" stroke="#666" fontSize={12} />
                <YAxis stroke="#666" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="volume"
                  stroke={COLORS.primary}
                  fill={`${COLORS.primary}20`}
                  strokeWidth={2}
                  name="Volume"
                />
              </AreaChart>
            ) : (
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" stroke="#666" fontSize={12} />
                <YAxis stroke="#666" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar
                  dataKey="volume"
                  fill={COLORS.primary}
                  name="Volume"
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Metrics */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Performance Metrics</h3>
              <p className="text-sm text-gray-600">Automation rate and processing efficiency</p>
            </div>
            <ChartSelector
              activeChart={activePerformanceChart}
              onChartChange={setActivePerformanceChart}
              charts={performanceCharts}
            />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {activePerformanceChart === 'area' ? (
                <AreaChart data={volumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="automationRate"
                    stackId="1"
                    stroke={COLORS.secondary}
                    fill={`${COLORS.secondary}40`}
                    name="Automation Rate (%)"
                  />
                  <Area
                    type="monotone"
                    dataKey="processingTime"
                    stackId="2"
                    stroke={COLORS.info}
                    fill={`${COLORS.info}40`}
                    name="Avg Processing Time (min)"
                  />
                </AreaChart>
              ) : (
                <LineChart data={volumeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" stroke="#666" fontSize={12} />
                  <YAxis stroke="#666" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="automationRate"
                    stroke={COLORS.secondary}
                    strokeWidth={2}
                    dot={{ fill: COLORS.secondary, strokeWidth: 2, r: 3 }}
                    name="Automation Rate (%)"
                  />
                  <Line
                    type="monotone"
                    dataKey="processingTime"
                    stroke={COLORS.info}
                    strokeWidth={2}
                    dot={{ fill: COLORS.info, strokeWidth: 2, r: 3 }}
                    name="Avg Processing Time (min)"
                  />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Format Distribution */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Format Distribution</h3>
              <p className="text-sm text-gray-600">Processing volume by file format</p>
            </div>
            <PieChartIcon className="h-5 w-5 text-gray-400" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={formatData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                  labelLine={false}
                >
                  {formatData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border rounded-lg shadow-lg">
                          <p className="font-medium text-gray-900">{data.name}</p>
                          <p className="text-sm text-gray-600">Volume: {data.value}</p>
                          <p className="text-sm text-gray-600">Percentage: {data.percentage.toFixed(1)}%</p>
                          <p className="text-sm text-gray-600">Avg Time: {data.avgTime} min</p>
                          <p className="text-sm text-gray-600">Success Rate: {data.successRate}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Format Legend */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            {formatData.map((format, index) => (
              <div key={format.name} className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}
                />
                <span className="text-sm text-gray-700">{format.name}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Error Rate Trend */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Error Rate Analysis</h3>
            <p className="text-sm text-gray-600">Error counts and success rate trends</p>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={volumeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#666" fontSize={12} />
              <YAxis yAxisId="errors" stroke="#666" fontSize={12} />
              <YAxis yAxisId="percentage" orientation="right" stroke="#666" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                yAxisId="errors"
                type="monotone"
                dataKey="errorCount"
                stroke={COLORS.error}
                fill={`${COLORS.error}30`}
                strokeWidth={2}
                name="Error Count"
              />
              <Line
                yAxisId="percentage"
                type="monotone"
                dataKey="successRate"
                stroke={COLORS.success}
                strokeWidth={2}
                dot={{ fill: COLORS.success, strokeWidth: 2, r: 3 }}
                name="Success Rate (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};

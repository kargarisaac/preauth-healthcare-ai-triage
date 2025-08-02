import React, { useState, useEffect } from 'react';
import {
  Activity,
  Wifi,
  WifiOff,
  Zap,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Server,
  Cpu,
  HardDrive,
  MemoryStick,
  Gauge
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Area,
  AreaChart
} from 'recharts';
import { useRealTimeMetrics } from '../../hooks/data/useRealTimeMetrics';
import { SystemHealth, AnalyticsMetrics } from '../../types/analytics';

interface RealtimeMetricsProps {
  enabled?: boolean;
  className?: string;
}

interface LiveMetricCardProps {
  title: string;
  value: number;
  unit: string;
  change?: number;
  status: 'good' | 'warning' | 'critical';
  icon: React.ReactNode;
  isLive?: boolean;
}

interface SystemHealthCardProps {
  health: SystemHealth;
}

interface GaugeChartProps {
  value: number;
  max: number;
  min?: number;
  title: string;
  unit: string;
  color: string;
  size?: number;
}

const LiveMetricCard: React.FC<LiveMetricCardProps> = ({
  title,
  value,
  unit,
  change,
  status,
  icon,
  isLive = true
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isLive) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 500);
      return () => clearTimeout(timer);
    }
  }, [value, isLive]);

  const statusColors = {
    good: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    critical: 'border-red-200 bg-red-50'
  };

  const iconColors = {
    good: 'text-green-600',
    warning: 'text-yellow-600',
    critical: 'text-red-600'
  };

  return (
    <Card className={`p-4 transition-all duration-300 ${statusColors[status]} ${
      isAnimating ? 'scale-105 shadow-lg' : ''
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${iconColors[status]}`}>
          {icon}
        </div>
        {isLive && (
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-600">LIVE</span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-medium text-gray-700">{title}</h3>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-bold text-gray-900">
            {typeof value === 'number' ? value.toFixed(1) : value}
          </span>
          <span className="text-sm text-gray-600">{unit}</span>
        </div>

        {change !== undefined && (
          <div className={`flex items-center text-xs ${
            change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
          }`}>
            {change > 0 ? (
              <TrendingUp className="h-3 w-3 mr-1" />
            ) : change < 0 ? (
              <TrendingDown className="h-3 w-3 mr-1" />
            ) : null}
            <span>{Math.abs(change).toFixed(1)}% from last minute</span>
          </div>
        )}
      </div>
    </Card>
  );
};

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ health }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5" />;
      case 'warning': return <AlertCircle className="h-5 w-5" />;
      case 'critical': return <AlertCircle className="h-5 w-5" />;
      default: return <Server className="h-5 w-5" />;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
        <div className={`flex items-center space-x-2 ${getStatusColor(health.status)}`}>
          {getStatusIcon(health.status)}
          <span className="font-medium capitalize">{health.status}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <Cpu className="h-4 w-4 text-blue-500" />
            <div className="flex-1">
              <div className="flex justify-between text-sm">
                <span>CPU Usage</span>
                <span className="font-medium">{health.cpuUsage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    health.cpuUsage > 80 ? 'bg-red-500' :
                    health.cpuUsage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.cpuUsage}%` }}
                />
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <MemoryStick className="h-4 w-4 text-purple-500" />
            <div className="flex-1">
              <div className="flex justify-between text-sm">
                <span>Memory</span>
                <span className="font-medium">{health.memoryUsage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    health.memoryUsage > 85 ? 'bg-red-500' :
                    health.memoryUsage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.memoryUsage}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <HardDrive className="h-4 w-4 text-green-500" />
            <div className="flex-1">
              <div className="flex justify-between text-sm">
                <span>Disk Usage</span>
                <span className="font-medium">{health.diskUsage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    health.diskUsage > 90 ? 'bg-red-500' :
                    health.diskUsage > 75 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.diskUsage}%` }}
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-400" />
              <span>Uptime</span>
            </span>
            <span className="font-medium">{formatUptime(health.uptime)}</span>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span>API Response Time</span>
          <span className={`font-medium ${
            health.apiResponseTime > 1000 ? 'text-red-600' :
            health.apiResponseTime > 500 ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {health.apiResponseTime.toFixed(0)}ms
          </span>
        </div>
      </div>
    </Card>
  );
};

const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  max,
  min = 0,
  title,
  unit,
  color,
  size = 120
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  const circumference = 2 * Math.PI * (size / 2 - 10);
  const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 10}
            stroke="#e5e7eb"
            strokeWidth="8"
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 10}
            stroke={color}
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold text-gray-900">
            {value.toFixed(1)}
          </span>
          <span className="text-xs text-gray-600">{unit}</span>
        </div>
      </div>
      <p className="text-sm font-medium text-gray-700 mt-2">{title}</p>
    </div>
  );
};

export const RealtimeMetrics: React.FC<RealtimeMetricsProps> = ({
  enabled = true,
  className = ''
}) => {
  const {
    metrics,
    systemHealth,
    isConnected,
    connectionStatus,
    lastUpdate,
    connect,
    disconnect
  } = useRealTimeMetrics({ enabled });

  const [historicalData, setHistoricalData] = useState<Array<{
    time: string;
    volume: number;
    processingTime: number;
    successRate: number;
  }>>([]);

  // Mock real-time data updates for demonstration
  useEffect(() => {
    if (!metrics) return;

    const interval = setInterval(() => {
      const now = new Date();
      const timeString = now.toLocaleTimeString();

      setHistoricalData(prev => {
        const newData = {
          time: timeString,
          volume: Math.round(Math.random() * 50 + 100), // Mock volume
          processingTime: Math.round(Math.random() * 30 + 120), // Mock processing time in seconds
          successRate: Math.round(Math.random() * 10 + 90) // Mock success rate
        };

        return [...prev.slice(-29), newData]; // Keep last 30 data points
      });
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [metrics]);

  if (!metrics && !systemHealth) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Card className="p-8 text-center">
          <WifiOff className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Real-time Metrics Unavailable
          </h3>
          <p className="text-gray-600 mb-4">
            Unable to connect to real-time data stream.
          </p>
          <Button onClick={connect} variant="primary">
            Retry Connection
          </Button>
        </Card>
      </div>
    );
  }

  const mockChanges = {
    volume: Math.random() * 20 - 10,
    processingTime: Math.random() * 10 - 5,
    automation: Math.random() * 5 - 2.5,
    errorRate: Math.random() * 2 - 1
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Real-time Metrics</h2>
          <p className="text-sm text-gray-600">Live performance monitoring and system health</p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-500" />
            )}
            <span className={`text-sm font-medium ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              {connectionStatus}
            </span>
          </div>

          {lastUpdate && (
            <div className="text-xs text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </div>
          )}

          <Button
            size="sm"
            variant={enabled ? "secondary" : "primary"}
            onClick={enabled ? disconnect : connect}
          >
            {enabled ? 'Disconnect' : 'Connect'}
          </Button>
        </div>
      </div>

      {/* Live Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <LiveMetricCard
            title="Current Volume"
            value={Math.round(Math.random() * 50 + 100)}
            unit="req/min"
            change={mockChanges.volume}
            status="good"
            icon={<Activity className="h-5 w-5" />}
            isLive={isConnected}
          />

          <LiveMetricCard
            title="Processing Time"
            value={Math.round(metrics.avgProcessingTime / 60)}
            unit="minutes"
            change={mockChanges.processingTime}
            status={metrics.avgProcessingTime > 900 ? "warning" : "good"}
            icon={<Clock className="h-5 w-5" />}
            isLive={isConnected}
          />

          <LiveMetricCard
            title="Automation Rate"
            value={Math.round(metrics.automationRate * 100)}
            unit="%"
            change={mockChanges.automation}
            status={metrics.automationRate > 0.8 ? "good" : "warning"}
            icon={<Zap className="h-5 w-5" />}
            isLive={isConnected}
          />

          <LiveMetricCard
            title="Error Rate"
            value={Math.round(metrics.errorRate * 100)}
            unit="%"
            change={mockChanges.errorRate}
            status={metrics.errorRate < 0.05 ? "good" : metrics.errorRate < 0.1 ? "warning" : "critical"}
            icon={<AlertCircle className="h-5 w-5" />}
            isLive={isConnected}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        {systemHealth && <SystemHealthCard health={systemHealth} />}

        {/* Performance Gauges */}
        {metrics && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Gauges</h3>
            <div className="grid grid-cols-2 gap-4">
              <GaugeChart
                value={Math.round(metrics.automationRate * 100)}
                max={100}
                title="Automation"
                unit="%"
                color="#0066cc"
              />

              <GaugeChart
                value={Math.round(metrics.dataQualityScore * 100)}
                max={100}
                title="Quality"
                unit="%"
                color="#00a86b"
              />

              <GaugeChart
                value={Math.round(metrics.slaCompliance * 100)}
                max={100}
                title="SLA"
                unit="%"
                color="#ff6b35"
              />

              <GaugeChart
                value={Math.round(metrics.successRate * 100)}
                max={100}
                title="Success"
                unit="%"
                color="#28a745"
              />
            </div>
          </Card>
        )}
      </div>

      {/* Real-time Chart */}
      {historicalData.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Real-time Processing Activity
          </h3>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historicalData}>
                <XAxis
                  dataKey="time"
                  stroke="#666"
                  fontSize={12}
                  tick={{ fontSize: 10 }}
                />
                <YAxis
                  stroke="#666"
                  fontSize={12}
                  tick={{ fontSize: 10 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="volume"
                  stroke="#0066cc"
                  fill="#0066cc30"
                  strokeWidth={2}
                  name="Volume (req/min)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
};

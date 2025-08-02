import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Download, 
  RefreshCw, 
  Calendar,
  Maximize2,
  Minimize2,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';
import { MetricsGrid } from './MetricsGrid';
import { ProcessingCharts } from './ProcessingCharts';
import { PerformanceTrends } from './PerformanceTrends';
import { CostSavingsTracker } from './CostSavingsTracker';
import { AnalyticsOverview } from './AnalyticsOverview';
import { RealtimeMetrics } from './RealtimeMetrics';
import { useAnalytics } from '../../hooks/data/useAnalytics';
import { useRealTimeMetrics } from '../../hooks/data/useRealTimeMetrics';
import { useDashboardLayout } from '../../hooks/ui/useDashboardLayout';
import { DateRangePreset } from '../../types/analytics';

interface AnalyticsDashboardProps {
  className?: string;
}

interface DateRangeSelectorProps {
  dateRange: DateRangePreset;
  onDateRangeChange: (range: DateRangePreset) => void;
  presets: DateRangePreset[];
}

interface RealTimeStatusProps {
  isConnected: boolean;
  connectionStatus: string;
  lastUpdate: Date | null;
}

const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  dateRange,
  onDateRangeChange,
  presets
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2"
      >
        <Calendar className="h-4 w-4" />
        <span>{dateRange.label}</span>
      </Button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-300 rounded-md shadow-lg z-50">
          <div className="py-1">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => {
                  onDateRangeChange(preset);
                  setIsOpen(false);
                }}
                className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                  dateRange.id === preset.id ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const RealTimeStatus: React.FC<RealTimeStatusProps> = ({
  isConnected,
  connectionStatus,
  lastUpdate
}) => {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = () => {
    return isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />;
  };

  return (
    <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
      {getStatusIcon()}
      <span className="capitalize">{connectionStatus}</span>
      {lastUpdate && (
        <span className="text-gray-500">
          • Updated {lastUpdate.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Custom hooks
  const {
    dateRange,
    setDateRange,
    dateRangePresets,
    visibleWidgets,
    // toggleWidgetVisibility,
    // isMobile,
    // screenSize
  } = useDashboardLayout();

  const {
    data: analyticsData,
    loading: analyticsLoading,
    error: analyticsError,
    refresh: refreshAnalytics,
    exportData
  } = useAnalytics({
    autoRefresh: true,
    refreshInterval: 30,
    dateRange
  });

  const {
    metrics: realTimeMetrics,
    systemHealth,
    isConnected: isRealTimeConnected,
    connectionStatus,
    lastUpdate: lastRealTimeUpdate
  } = useRealTimeMetrics({
    enabled: true
  });

  // Use real-time metrics if available, otherwise fall back to analytics data
  const metrics = realTimeMetrics || analyticsData?.metrics;
  const trends = analyticsData?.trends || [];
  const formatDistribution = analyticsData?.formatDistribution || [];
  const providerPerformance = analyticsData?.providerPerformance || [];
  const costSavings = analyticsData?.costSavings || [];
  const qualityMetrics = analyticsData?.qualityMetrics || [];
  const alerts = analyticsData?.alerts || [];
  // const heatmapData = analyticsData?.heatmapData || [];
  // const geographicData = analyticsData?.geographicData || [];

  const tabs = [
    { id: 'overview', label: 'Overview', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'realtime', label: 'Real-time', icon: <Wifi className="h-4 w-4" /> },
    { id: 'performance', label: 'Performance', icon: <TrendingUp className="h-4 w-4" /> },
    { id: 'financial', label: 'Financial', icon: <TrendingUp className="h-4 w-4" /> }
  ];

  // const handleExport = async (format: 'png' | 'pdf' | 'excel') => {
  //   try {
  //     await exportData(format === 'png' || format === 'pdf' ? 'excel' : format);
  //   } catch (error) {
  //     console.error('Export failed:', error);
  //   }
  // };

  const handleRefresh = async () => {
    await refreshAnalytics();
  };

  // Handle loading states
  if (analyticsLoading && !metrics) {
    return (
      <div className={`flex items-center justify-center min-h-96 ${className}`}>
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600">Loading analytics dashboard...</p>
        </div>
      </div>
    );
  }

  // Handle error states
  if (analyticsError && !metrics) {
    return (
      <div className={`flex items-center justify-center min-h-96 ${className}`}>
        <Card className="p-8 text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load Analytics</h3>
          <p className="text-gray-600 mb-4">{analyticsError}</p>
          <Button onClick={handleRefresh} className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4" />
            <span>Retry</span>
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive healthcare data processing insights</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Real-time Status */}
          <RealTimeStatus
            isConnected={isRealTimeConnected}
            connectionStatus={connectionStatus}
            lastUpdate={lastRealTimeUpdate}
          />
          
          {/* Date Range Selector */}
          <DateRangeSelector
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            presets={dateRangePresets}
          />
          
          {/* Action Buttons */}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRefresh}
            disabled={analyticsLoading}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${analyticsLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          
          <div className="relative">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {/* Toggle export menu */}}
              className="flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </Button>
          </div>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center space-x-2"
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            <span>{isFullscreen ? 'Exit' : 'Fullscreen'}</span>
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">Active Alerts</h3>
              <div className="mt-2 space-y-1">
                {alerts.slice(0, 3).map((alert) => (
                  <p key={alert.id} className="text-sm text-yellow-700">
                    {alert.name}: {alert.currentValue} {alert.unit} 
                    ({alert.status === 'warning' ? 'Above warning' : 'Critical'} threshold)
                  </p>
                ))}
              </div>
              {alerts.length > 3 && (
                <p className="text-sm text-yellow-600 mt-1">
                  +{alerts.length - 3} more alerts
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Dashboard Content */}
      <div className={isFullscreen ? 'fixed inset-0 z-50 bg-white overflow-auto p-6' : ''}>
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Analytics Overview */}
            <AnalyticsOverview
              data={analyticsData}
              isLoading={analyticsLoading}
            />
            
            {/* Key Metrics */}
            {metrics && (
              <MetricsGrid
                metrics={metrics}
                isLoading={analyticsLoading}
                showTrends={true}
              />
            )}
            
            {/* Processing Charts */}
            <ProcessingCharts
              trends={trends}
              formatDistribution={formatDistribution}
              isLoading={analyticsLoading}
            />
          </div>
        )}

        {activeTab === 'realtime' && (
          <RealtimeMetrics
            enabled={true}
          />
        )}

        {activeTab === 'performance' && (
          <PerformanceTrends
            trends={trends}
            providerPerformance={providerPerformance}
            qualityMetrics={qualityMetrics}
            isLoading={analyticsLoading}
          />
        )}

        {activeTab === 'financial' && metrics && (
          <CostSavingsTracker
            costSavings={costSavings}
            metrics={metrics}
            isLoading={analyticsLoading}
          />
        )}
      </div>

      {/* System Health Footer */}
      {systemHealth && (
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${
                systemHealth.status === 'healthy' ? 'bg-green-500' :
                systemHealth.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-sm font-medium text-gray-900">
                System Status: {systemHealth.status.charAt(0).toUpperCase() + systemHealth.status.slice(1)}
              </span>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-600">
              <span>CPU: {systemHealth.cpuUsage.toFixed(1)}%</span>
              <span>Memory: {systemHealth.memoryUsage.toFixed(1)}%</span>
              <span>API Response: {systemHealth.apiResponseTime}ms</span>
              <span>Uptime: {Math.floor(systemHealth.uptime / 86400)}d {Math.floor((systemHealth.uptime % 86400) / 3600)}h</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
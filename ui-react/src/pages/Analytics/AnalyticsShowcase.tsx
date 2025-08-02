import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Activity,
  Target,
  Clock,
  Users,
  Zap,
  CheckCircle,
  AlertTriangle,
  Gauge
} from 'lucide-react';
import { AnalyticsOverview } from '../../components/dashboard/AnalyticsOverview';
import { ProcessingCharts } from '../../components/dashboard/ProcessingCharts';
import { PerformanceTrends } from '../../components/dashboard/PerformanceTrends';
import { CostSavingsTracker } from '../../components/dashboard/CostSavingsTracker';
import { RealtimeMetrics } from '../../components/dashboard/RealtimeMetrics';
import { ProcessingHeatmap } from '../../components/dashboard/ProcessingHeatmap';
import { GaugeMetrics } from '../../components/dashboard/GaugeMetrics';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import {
  generateMockAnalyticsDashboardData,
  generateMockAnalyticsMetrics
} from '../../utils/mockAnalyticsData';
import { GaugeChartData } from '../../types/analytics';

interface AnalyticsShowcaseProps {
  className?: string;
}

const AnalyticsShowcase: React.FC<AnalyticsShowcaseProps> = ({
  className = ''
}) => {
  const [activeDemo, setActiveDemo] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [mockData, setMockData] = useState(() => generateMockAnalyticsDashboardData());

  // Refresh mock data
  const refreshData = () => {
    setIsLoading(true);
    setTimeout(() => {
      setMockData(generateMockAnalyticsDashboardData());
      setIsLoading(false);
    }, 1000);
  };

  // Auto-refresh data every 30 seconds for demo
  useEffect(() => {
    const interval = setInterval(() => {
      setMockData(generateMockAnalyticsDashboardData());
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Generate gauge data from metrics
  const generateGaugeData = () => {
    const metrics = mockData.metrics;

    return [
      {
        id: 'automation',
        title: 'Automation Rate',
        icon: <Zap className="h-5 w-5" />,
        description: 'Percentage of requests processed automatically',
        data: {
          value: Math.round(metrics.automationRate * 100),
          min: 0,
          max: 100,
          target: 85,
          thresholds: [
            { value: 60, color: '#dc3545', label: 'Low' },
            { value: 80, color: '#ffc107', label: 'Good' },
            { value: 100, color: '#28a745', label: 'Excellent' }
          ]
        } as GaugeChartData
      },
      {
        id: 'quality',
        title: 'Data Quality',
        icon: <CheckCircle className="h-5 w-5" />,
        description: 'Overall data completeness and accuracy',
        data: {
          value: Math.round(metrics.dataQualityScore * 100),
          min: 0,
          max: 100,
          target: 90,
          thresholds: [
            { value: 70, color: '#dc3545', label: 'Poor' },
            { value: 85, color: '#ffc107', label: 'Good' },
            { value: 100, color: '#28a745', label: 'Excellent' }
          ]
        } as GaugeChartData
      },
      {
        id: 'sla',
        title: 'SLA Compliance',
        icon: <Clock className="h-5 w-5" />,
        description: 'Requests processed within SLA targets',
        data: {
          value: Math.round(metrics.slaCompliance * 100),
          min: 0,
          max: 100,
          target: 95,
          thresholds: [
            { value: 80, color: '#dc3545', label: 'Below Target' },
            { value: 95, color: '#ffc107', label: 'Meeting Target' },
            { value: 100, color: '#28a745', label: 'Exceeding' }
          ]
        } as GaugeChartData
      },
      {
        id: 'success',
        title: 'Success Rate',
        icon: <Target className="h-5 w-5" />,
        description: 'Percentage of successfully processed requests',
        data: {
          value: Math.round(metrics.successRate * 100),
          min: 0,
          max: 100,
          target: 95,
          thresholds: [
            { value: 85, color: '#dc3545', label: 'Needs Improvement' },
            { value: 95, color: '#ffc107', label: 'Good' },
            { value: 100, color: '#28a745', label: 'Excellent' }
          ]
        } as GaugeChartData
      }
    ];
  };

  const demoSections = [
    {
      id: 'overview',
      label: 'Analytics Overview',
      icon: <BarChart3 className="h-4 w-4" />,
      description: 'Comprehensive KPI dashboard with key metrics and trends'
    },
    {
      id: 'realtime',
      label: 'Real-time Metrics',
      icon: <Activity className="h-4 w-4" />,
      description: 'Live performance monitoring and system health'
    },
    {
      id: 'charts',
      label: 'Processing Charts',
      icon: <TrendingUp className="h-4 w-4" />,
      description: 'Interactive charts showing volume, performance, and format distribution'
    },
    {
      id: 'performance',
      label: 'Performance Trends',
      icon: <TrendingUp className="h-4 w-4" />,
      description: 'Historical analysis with provider performance and quality metrics'
    },
    {
      id: 'financial',
      label: 'Cost Savings',
      icon: <DollarSign className="h-4 w-4" />,
      description: 'ROI tracking and cost savings breakdown with projections'
    },
    {
      id: 'heatmap',
      label: 'Activity Heatmap',
      icon: <Users className="h-4 w-4" />,
      description: 'Processing volume patterns by day and hour'
    },
    {
      id: 'gauges',
      label: 'Performance Gauges',
      icon: <Gauge className="h-4 w-4" />,
      description: 'Animated gauge charts for key performance indicators'
    }
  ];

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Healthcare Analytics Dashboard Demo
              </h1>
              <p className="text-sm text-gray-600">
                Comprehensive data visualization and performance monitoring
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={refreshData}
                disabled={isLoading}
                className="flex items-center space-x-2"
              >
                <Activity className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh Data</span>
              </Button>

              <div className="flex items-center text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                <span>Live Demo</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <Card className="p-4 mb-8">
          <div className="flex flex-wrap gap-2">
            {demoSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveDemo(section.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeDemo === section.id
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                }`}
              >
                {section.icon}
                <span>{section.label}</span>
              </button>
            ))}
          </div>

          {/* Active section description */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              {demoSections.find(s => s.id === activeDemo)?.description}
            </p>
          </div>
        </Card>

        {/* Demo Content */}
        <div className="space-y-8">
          {activeDemo === 'overview' && (
            <AnalyticsOverview
              data={mockData}
              isLoading={isLoading}
            />
          )}

          {activeDemo === 'realtime' && (
            <RealtimeMetrics enabled={true} />
          )}

          {activeDemo === 'charts' && (
            <ProcessingCharts
              trends={mockData.trends}
              formatDistribution={mockData.formatDistribution}
              isLoading={isLoading}
            />
          )}

          {activeDemo === 'performance' && (
            <PerformanceTrends
              trends={mockData.trends}
              providerPerformance={mockData.providerPerformance}
              qualityMetrics={mockData.qualityMetrics}
              isLoading={isLoading}
            />
          )}

          {activeDemo === 'financial' && (
            <CostSavingsTracker
              costSavings={mockData.costSavings}
              metrics={mockData.metrics}
              isLoading={isLoading}
            />
          )}

          {activeDemo === 'heatmap' && (
            <ProcessingHeatmap
              data={mockData.heatmapData}
              isLoading={isLoading}
            />
          )}

          {activeDemo === 'gauges' && (
            <GaugeMetrics
              gauges={generateGaugeData()}
              isLoading={isLoading}
            />
          )}
        </div>

        {/* Data Info */}
        <Card className="p-6 mt-8">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-gray-900">Demo Data Notice</h3>
              <p className="text-sm text-gray-600 mt-1">
                This demo uses simulated healthcare data for demonstration purposes.
                In production, all data would be sourced from secure healthcare APIs
                compliant with UAE healthcare regulations and GDPR requirements.
              </p>

              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-500">
                <div>
                  <strong>Data Sources:</strong>
                  <ul className="mt-1 space-y-1">
                    <li>• eClaimLink (Dubai Health Authority)</li>
                    <li>• Shafafiya (Abu Dhabi DoH)</li>
                    <li>• Healthcare CSV imports</li>
                  </ul>
                </div>

                <div>
                  <strong>Key Features:</strong>
                  <ul className="mt-1 space-y-1">
                    <li>• Real-time data processing</li>
                    <li>• Interactive visualizations</li>
                    <li>• Mobile-responsive design</li>
                  </ul>
                </div>

                <div>
                  <strong>Compliance:</strong>
                  <ul className="mt-1 space-y-1">
                    <li>• UAE healthcare standards</li>
                    <li>• FHIR R4 compatibility</li>
                    <li>• Data privacy protection</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsShowcase;

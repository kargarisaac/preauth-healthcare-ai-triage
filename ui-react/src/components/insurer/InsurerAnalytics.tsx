import React, { useState, useMemo } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  Users,
  Building,
  DollarSign,
  Activity,
  Calendar,
  BarChart3,
  PieChart,
  Filter,
  Download,
  RefreshCw,
} from 'lucide-react';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import type { InsurerMetrics } from '@/types/insurer';

// Simple chart components (replace with actual charting library)
const SimpleBarChart: React.FC<{
  data: Array<{ label: string; value: number; color?: string }>;
  height?: number;
}> = ({ data, height = 200 }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className="space-y-2">
      {data.map((item, index) => (
        <div key={index} className="flex items-center space-x-3">
          <div className="w-20 text-sm text-gray-600 dark:text-dark-text-secondary">
            {item.label}
          </div>
          <div className="flex-1 relative">
            <div className="w-full bg-gray-200 dark:bg-dark-bg-tertiary rounded-full h-4">
              <div
                className={`h-4 rounded-full ${item.color || 'bg-blue-600'}`}
                style={{ width: `${(item.value / maxValue) * 100}%` }}
              />
            </div>
            <span className="absolute right-2 top-0 text-xs text-gray-700 dark:text-dark-text-primary leading-4">
              {item.value}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

const SimpleLineChart: React.FC<{
  data: Array<{ date: string; requests: number; decisions: number }>;
}> = ({ data }) => {
  const maxValue = Math.max(...data.flatMap(d => [d.requests, d.decisions]));
  
  return (
    <div className="space-y-3">
      <div className="flex justify-between text-sm">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
            <span className="text-gray-600 dark:text-dark-text-secondary">Requests</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-600 rounded-full"></div>
            <span className="text-gray-600 dark:text-dark-text-secondary">Decisions</span>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-7 gap-2 h-32">
        {data.map((item, index) => (
          <div key={index} className="flex flex-col items-center justify-end space-y-1">
            <div className="flex flex-col justify-end h-24 space-y-1">
              <div
                className="bg-blue-600 rounded-t"
                style={{ height: `${(item.requests / maxValue) * 80}px` }}
              />
              <div
                className="bg-green-600 rounded-t"
                style={{ height: `${(item.decisions / maxValue) * 80}px` }}
              />
            </div>
            <span className="text-xs text-gray-500 dark:text-dark-text-tertiary">
              {new Date(item.date).getDate()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

interface InsurerAnalyticsProps {
  metrics: InsurerMetrics;
  onDrillDown?: (type: string, data: any) => void;
}

export const InsurerAnalytics: React.FC<InsurerAnalyticsProps> = ({
  metrics,
  onDrillDown,
}) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'week' | 'month' | 'quarter'>('week');
  const [selectedMetric, setSelectedMetric] = useState<'volume' | 'performance' | 'distribution'>('volume');

  // Calculate trends and insights
  const insights = useMemo(() => {
    const { workload, performance, trends } = metrics;
    
    return {
      totalBacklog: workload.totalPending + workload.underReview,
      processingEfficiency: ((workload.decisionsToday / workload.totalPending) * 100).toFixed(1),
      avgDecisionTimeImprovement: workload.avgReviewTime < 20 ? 'improved' : 'needs_attention',
      aiAgreementTrend: performance.aiAgreementRate > 85 ? 'high' : 'moderate',
      weeklyVolumeTrend: trends.dailyVolume.length > 1 ? 
        (trends.dailyVolume[trends.dailyVolume.length - 1].requests > 
         trends.dailyVolume[trends.dailyVolume.length - 2].requests ? 'increasing' : 'decreasing') : 'stable',
    };
  }, [metrics]);

  const urgencyDistributionData = Object.entries(metrics.distribution.byUrgency).map(([urgency, count]) => ({
    label: urgency.charAt(0).toUpperCase() + urgency.slice(1),
    value: count,
    color: urgency === 'critical' ? 'bg-red-600' :
           urgency === 'urgent' ? 'bg-orange-600' :
           urgency === 'emergency' ? 'bg-red-500' :
           'bg-gray-600',
  }));

  const riskLevelData = Object.entries(metrics.distribution.byRiskLevel).map(([level, count]) => ({
    label: level.charAt(0).toUpperCase() + level.slice(1),
    value: count,
    color: level === 'critical' ? 'bg-red-600' :
           level === 'high' ? 'bg-orange-600' :
           level === 'medium' ? 'bg-yellow-600' :
           'bg-green-600',
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
            Medical Director Analytics
          </h2>
          <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
            Performance insights and decision analytics
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="text-sm border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-1 bg-white dark:bg-dark-bg-secondary text-gray-900 dark:text-dark-text-primary"
          >
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="quarter">Last Quarter</option>
          </select>
          
          <Button variant="tertiary" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          
          <Button variant="secondary" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">
                Total Backlog
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-dark-text-primary">
                {insights.totalBacklog}
              </p>
              <p className="text-xs text-gray-500 dark:text-dark-text-tertiary mt-1">
                Pending + Under Review
              </p>
            </div>
            <Clock className="h-8 w-8 text-orange-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">
                Processing Efficiency
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-dark-text-primary">
                {insights.processingEfficiency}%
              </p>
              <p className="text-xs text-green-600 mt-1">
                Decisions/Pending Ratio
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">
                AI Agreement Rate
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-dark-text-primary">
                {metrics?.performance?.aiAgreementRate || 0}%
              </p>
              <p className={`text-xs mt-1 ${
                insights.aiAgreementTrend === 'high' ? 'text-green-600' : 'text-yellow-600'
              }`}>
                {insights.aiAgreementTrend === 'high' ? 'Excellent alignment' : 'Moderate alignment'}
              </p>
            </div>
            <Activity className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">
                Quality Score
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-dark-text-primary">
                {metrics?.performance?.qualityScore || 0}%
              </p>
              <p className="text-xs text-green-600 mt-1">
                Above target (90%)
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </Card>
      </div>

      {/* Main Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Volume Trends */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              Daily Volume Trends
            </h3>
            <div className="flex items-center space-x-2">
              <span className={`text-sm ${
                insights.weeklyVolumeTrend === 'increasing' ? 'text-green-600' :
                insights.weeklyVolumeTrend === 'decreasing' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {insights.weeklyVolumeTrend === 'increasing' ? '↗ Increasing' :
                 insights.weeklyVolumeTrend === 'decreasing' ? '↘ Decreasing' :
                 '→ Stable'}
              </span>
            </div>
          </div>
          <SimpleLineChart data={metrics.trends.dailyVolume} />
        </Card>
        
        {/* Urgency Distribution */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              Cases by Urgency
            </h3>
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => onDrillDown?.('urgency', metrics.distribution.byUrgency)}
            >
              View Details
            </Button>
          </div>
          <SimpleBarChart data={urgencyDistributionData} />
        </Card>
        
        {/* Risk Level Distribution */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              Cases by Risk Level
            </h3>
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => onDrillDown?.('risk', metrics.distribution.byRiskLevel)}
            >
              View Details
            </Button>
          </div>
          <SimpleBarChart data={riskLevelData} />
        </Card>
        
        {/* Provider Performance */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              Top Providers
            </h3>
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => onDrillDown?.('providers', metrics.distribution.byProvider)}
            >
              View All
            </Button>
          </div>
          <div className="space-y-3">
            {metrics.distribution.byProvider.map((provider, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-dark-bg-tertiary rounded-lg">
                <div className="flex items-center space-x-3">
                  <Building className="h-5 w-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-dark-text-primary">
                      {provider.name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      {provider.count} requests
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-medium ${
                    provider.approvalRate >= 90 ? 'text-green-600' :
                    provider.approvalRate >= 75 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {provider.approvalRate || 0}%
                  </p>
                  <p className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                    approval rate
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4">
            Decision Metrics
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Approval Rate</span>
              <div className="flex items-center space-x-2">
                <span className="font-medium text-green-600">{metrics?.performance?.approvalRate || 0}%</span>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Override Rate</span>
              <div className="flex items-center space-x-2">
                <span className="font-medium text-gray-900 dark:text-dark-text-primary">
                  {metrics?.performance?.overrideRate || 0}%
                </span>
                <Activity className="h-4 w-4 text-gray-600" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Avg Decision Time</span>
              <div className="flex items-center space-x-2">
                <span className={`font-medium ${
                  insights.avgDecisionTimeImprovement === 'improved' ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {metrics?.performance?.avgDecisionTime || 0}m
                </span>
                <Clock className={`h-4 w-4 ${
                  insights.avgDecisionTimeImprovement === 'improved' ? 'text-green-600' : 'text-orange-600'
                }`} />
              </div>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4">
            Workload Overview
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Total Pending</span>
              <span className="font-bold text-xl text-blue-600">
                {metrics?.workload?.totalPending || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Under Review</span>
              <span className="font-medium text-orange-600">
                {metrics?.workload?.underReview || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Overdue</span>
              <span className={`font-medium ${
                metrics?.workload?.overdueReviews > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {metrics?.workload?.overdueReviews || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-dark-text-secondary">Decisions Today</span>
              <span className="font-medium text-green-600">
                {metrics?.workload?.decisionsToday || 0}
              </span>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4">
            Monthly Trends
          </h3>
          <div className="space-y-3">
            {metrics.trends.monthlyApprovals.map((month, index) => {
              const total = month.approved + month.denied;
              const approvalRate = total > 0 ? ((month.approved / total) * 100).toFixed(1) : '0';
              
              return (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-dark-text-secondary">
                    {month.month}
                  </span>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                      {approvalRate || 0}% approved
                    </p>
                    <p className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                      {total} total cases
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Insights and Recommendations */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4">
          Insights & Recommendations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <h4 className="font-medium text-blue-900 dark:text-blue-300 mb-2">
              Workload Management
            </h4>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              {metrics?.workload?.overdueReviews > 0 
                ? `${metrics?.workload?.overdueReviews} overdue cases need immediate attention. Consider prioritizing by urgency.`
                : 'Workload is well managed. All cases are within deadline.'}
            </p>
          </div>
          
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <h4 className="font-medium text-green-900 dark:text-green-300 mb-2">
              AI Collaboration
            </h4>
            <p className="text-sm text-green-800 dark:text-green-200">
              {metrics?.performance?.aiAgreementRate > 85
                ? 'Excellent AI-human collaboration. Consider leveraging AI for routine cases.'
                : 'Review AI recommendations more carefully. Consider providing feedback to improve accuracy.'}
            </p>
          </div>
          
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <h4 className="font-medium text-orange-900 dark:text-orange-300 mb-2">
              Performance Optimization
            </h4>
            <p className="text-sm text-orange-800 dark:text-orange-200">
              {metrics?.performance?.avgDecisionTime < 20
                ? 'Decision times are optimal. Maintain current efficiency standards.'
                : 'Consider streamlining decision processes. Focus on high-urgency cases first.'}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

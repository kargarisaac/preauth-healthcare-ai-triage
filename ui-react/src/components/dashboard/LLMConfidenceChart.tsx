import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
  Legend
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  Target,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import Card from '../ui/Card';
import { LLMValidationResult, LLMFinding } from '../../types/llm';

interface LLMConfidenceChartProps {
  results: LLMValidationResult[];
  className?: string;
}

interface ConfidenceData {
  name: string;
  confidence: number;
  category: string;
  findings: number;
  criticalFindings: number;
}

interface CategoryDistribution {
  name: string;
  value: number;
  color: string;
}

interface TrendData {
  time: string;
  confidence: number;
  throughput: number;
}

const CONFIDENCE_COLORS = {
  high: '#10b981', // green-500
  medium: '#f59e0b', // yellow-500
  low: '#ef4444' // red-500
};

const CATEGORY_COLORS = {
  clinical: '#dc2626', // red-600
  administrative: '#2563eb', // blue-600
  compliance: '#16a34a', // green-600
  quality: '#9333ea' // purple-600
};

export const LLMConfidenceChart: React.FC<LLMConfidenceChartProps> = ({
  results,
  className = ''
}) => {
  const confidenceData = useMemo((): ConfidenceData[] => {
    return results
      .filter(result => result.status === 'completed')
      .map(result => ({
        name: result.functionId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        confidence: result.confidence,
        category: result.findings[0]?.category || 'unknown',
        findings: result.findings.length,
        criticalFindings: result.findings.filter(f => f.type === 'critical').length
      }));
  }, [results]);

  const categoryDistribution = useMemo((): CategoryDistribution[] => {
    const categories = results.reduce((acc, result) => {
      if (result.status === 'completed') {
        result.findings.forEach(finding => {
          acc[finding.category] = (acc[finding.category] || 0) + 1;
        });
      }
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(categories).map(([category, count]) => ({
      name: category.charAt(0).toUpperCase() + category.slice(1),
      value: count as number,
      color: CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || '#6b7280'
    }));
  }, [results]);

  const trendData = useMemo((): TrendData[] => {
    // Simulate historical trend data
    const now = new Date();
    return Array.from({ length: 12 }, (_, i) => {
      const time = new Date(now.getTime() - (11 - i) * 5 * 60 * 1000); // 5-minute intervals
      return {
        time: time.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        }),
        confidence: 75 + Math.random() * 20, // 75-95%
        throughput: 40 + Math.random() * 30 // 40-70 req/min
      };
    });
  }, []);

  const overallStats = useMemo(() => {
    const completedResults = results.filter(r => r.status === 'completed');
    if (completedResults.length === 0) {
      return {
        averageConfidence: 0,
        totalFindings: 0,
        criticalFindings: 0,
        trend: 'neutral' as const
      };
    }

    const avgConfidence = completedResults.reduce((sum, r) => sum + r.confidence, 0) / completedResults.length;
    const totalFindings = completedResults.reduce((sum, r) => sum + r.findings.length, 0);
    const criticalFindings = completedResults.reduce((sum, r) =>
      sum + r.findings.filter(f => f.type === 'critical').length, 0
    );

    // Determine trend based on confidence levels
    let trend: 'up' | 'down' | 'neutral' = 'neutral';
    if (avgConfidence >= 85) trend = 'up';
    else if (avgConfidence < 70) trend = 'down';

    return {
      averageConfidence: avgConfidence,
      totalFindings,
      criticalFindings,
      trend
    };
  }, [results]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-600" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return CONFIDENCE_COLORS.high;
    if (confidence >= 60) return CONFIDENCE_COLORS.medium;
    return CONFIDENCE_COLORS.low;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-md">
          <p className="font-medium text-gray-900">{label}</p>
          <div className="space-y-1 mt-2">
            <p className="text-sm text-gray-600">
              Confidence: <span className="font-medium">{data.confidence.toFixed(1)}%</span>
            </p>
            <p className="text-sm text-gray-600">
              Findings: <span className="font-medium">{data.findings}</span>
            </p>
            {data.criticalFindings > 0 && (
              <p className="text-sm text-red-600">
                Critical: <span className="font-medium">{data.criticalFindings}</span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  if (results.length === 0) {
    return (
      <Card className={`p-8 text-center ${className}`}>
        <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Data</h3>
        <p className="text-gray-600">Run LLM validation to see confidence metrics and charts.</p>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Average Confidence</p>
              <p className="text-2xl font-bold text-gray-900">
                {overallStats.averageConfidence.toFixed(1)}%
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {getTrendIcon(overallStats.trend)}
              <Target className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${overallStats.averageConfidence}%`,
                  backgroundColor: getConfidenceColor(overallStats.averageConfidence)
                }}
              />
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Total Findings</p>
              <p className="text-2xl font-bold text-gray-900">{overallStats.totalFindings}</p>
            </div>
            <Brain className="h-6 w-6 text-purple-600" />
          </div>
          <p className="text-xs text-gray-600 mt-2">
            Across {confidenceData.length} functions
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Critical Issues</p>
              <p className="text-2xl font-bold text-gray-900">{overallStats.criticalFindings}</p>
            </div>
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <p className="text-xs text-gray-600 mt-2">
            Require immediate attention
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {results.filter(r => r.status === 'completed').length}/{results.length}
              </p>
            </div>
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <p className="text-xs text-gray-600 mt-2">
            Functions completed successfully
          </p>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confidence Bar Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Confidence by Function</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={confidenceData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
                stroke="#6b7280"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="confidence"
                radius={[4, 4, 0, 0]}
              >
                {confidenceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getConfidenceColor(entry.confidence)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Category Distribution Pie Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Findings by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryDistribution}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {categoryDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [value, 'Findings']}
                labelStyle={{ color: '#374151' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Confidence Trend */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Confidence Trend (Last Hour)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={trendData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis
              yAxisId="confidence"
              domain={[60, 100]}
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis
              yAxisId="throughput"
              orientation="right"
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                name === 'confidence' ? `${value.toFixed(1)}%` : `${value.toFixed(0)} req/min`,
                name === 'confidence' ? 'Confidence' : 'Throughput'
              ]}
              labelStyle={{ color: '#374151' }}
            />
            <Legend />
            <Area
              yAxisId="confidence"
              type="monotone"
              dataKey="confidence"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.2}
              strokeWidth={2}
              name="Confidence"
            />
            <Line
              yAxisId="throughput"
              type="monotone"
              dataKey="throughput"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="Throughput"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
};

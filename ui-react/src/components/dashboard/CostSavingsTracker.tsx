import React, { useState } from 'react';
import {
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
  ResponsiveContainer,
} from 'recharts';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Calculator,
  PieChart as PieChartIcon,
  BarChart3,
  Calendar,
  Award
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { CostSavingsBreakdown, AnalyticsMetrics } from '../../types/analytics';

interface CostSavingsTrackerProps {
  costSavings: CostSavingsBreakdown[];
  metrics: AnalyticsMetrics;
  isLoading?: boolean;
  className?: string;
}

interface ROICalculatorProps {
  totalSavings: number;
  totalCosts: number;
  roi: number;
}

interface SavingsProjectionProps {
  currentMonthly: number;
  yearlyTarget: number;
  progress: number;
}

const ROICalculator: React.FC<ROICalculatorProps> = ({ totalSavings, totalCosts, roi }) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">ROI Calculator</h3>
        <Calculator className="h-5 w-5 text-blue-500" />
      </div>
      
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <DollarSign className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Total Savings</p>
            <p className="text-xl font-bold text-green-600">
              {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(totalSavings)}
            </p>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Implementation Cost</p>
            <p className="text-xl font-bold text-blue-600">
              {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(totalCosts)}
            </p>
          </div>
        </div>
        
        <div className="text-center p-4 bg-purple-50 rounded-lg border-2 border-purple-200">
          <Award className="h-10 w-10 text-purple-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Return on Investment</p>
          <p className="text-3xl font-bold text-purple-600">{roi.toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">
            For every AED 1 invested, we save AED {(roi / 100 + 1).toFixed(2)}
          </p>
        </div>
      </div>
    </Card>
  );
};

const SavingsProjection: React.FC<SavingsProjectionProps> = ({ currentMonthly, yearlyTarget, progress }) => {
  // const monthsRemaining = 12 - (new Date().getMonth() + 1);
  const projectedYearly = currentMonthly * 12;
  const onTrack = projectedYearly >= yearlyTarget;
  
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Yearly Projection</h3>
        <Calendar className="h-5 w-5 text-blue-500" />
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Monthly Average</span>
          <span className="font-medium">
            {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(currentMonthly)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Yearly Target</span>
          <span className="font-medium">
            {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(yearlyTarget)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Projected Yearly</span>
          <span className={`font-medium ${onTrack ? 'text-green-600' : 'text-yellow-600'}`}>
            {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(projectedYearly)}
          </span>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Progress to Target</span>
            <span className={`text-sm font-medium ${onTrack ? 'text-green-600' : 'text-yellow-600'}`}>
              {(progress * 100).toFixed(1)}%
            </span>
          </div>
          
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-300 ${
                onTrack ? 'bg-green-500' : progress >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(progress * 100, 100)}%` }}
            />
          </div>
        </div>
        
        <div className={`p-3 rounded-lg ${onTrack ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>
          <div className="flex items-center space-x-2">
            {onTrack ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
            <span className="text-sm font-medium">
              {onTrack 
                ? `On track to exceed target by ${new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(projectedYearly - yearlyTarget)}`
                : `Behind target by ${new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(yearlyTarget - projectedYearly)}`
              }
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export const CostSavingsTracker: React.FC<CostSavingsTrackerProps> = ({
  costSavings,
  metrics,
  isLoading = false,
  className = ''
}) => {
  const [chartType, setChartType] = useState<'bar' | 'pie'>('bar');
  // const [timeframe, setTimeframe] = useState('monthly');

  // Generate mock historical data for demonstration
  const generateHistoricalData = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const currentMonth = new Date().getMonth();
    
    return months.slice(0, currentMonth + 1).map((month, index) => {
      const baseAmount = metrics.costSavings;
      const variation = (Math.random() - 0.5) * 0.3; // ±15% variation
      const monthlyAmount = baseAmount * (1 + variation);
      
      return {
        month,
        amount: Math.round(monthlyAmount),
        automation: Math.round(monthlyAmount * 0.4),
        efficiency: Math.round(monthlyAmount * 0.35),
        quality: Math.round(monthlyAmount * 0.25),
        cumulative: Math.round(monthlyAmount * (index + 1))
      };
    });
  };

  const historicalData = generateHistoricalData();
  const yearlyTarget = metrics.costSavings * 12 * 1.2; // 20% growth target
  const currentProgress = metrics.totalSavingsYTD / yearlyTarget;

  // Calculate ROI data
  const implementationCost = 850000; // Estimated implementation cost in AED
  const roiData = {
    totalSavings: metrics.totalSavingsYTD,
    totalCosts: implementationCost,
    roi: metrics.roiPercentage
  };

  // Prepare data for charts
  const savingsBreakdown = costSavings.map((item, index) => ({
    ...item,
    color: ['#0066cc', '#00a86b', '#ff6b35', '#ffd23f', '#dc3545'][index % 5]
  }));

  const COLORS = ['#0066cc', '#00a86b', '#ff6b35', '#ffd23f', '#dc3545'];

  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-64 mb-4"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="h-80 bg-gray-200 rounded"></div>
            <div className="h-80 bg-gray-200 rounded"></div>
          </div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Cost Savings & ROI Tracker</h2>
          <p className="text-sm text-gray-600">Financial impact analysis and ROI projections</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={chartType === 'bar' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setChartType('bar')}
            className="flex items-center space-x-1"
          >
            <BarChart3 className="h-4 w-4" />
            <span>Bar</span>
          </Button>
          <Button
            variant={chartType === 'pie' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setChartType('pie')}
            className="flex items-center space-x-1"
          >
            <PieChartIcon className="h-4 w-4" />
            <span>Pie</span>
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Monthly Savings</p>
              <p className="text-2xl font-bold text-green-600">
                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(metrics.costSavings)}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">YTD Total</p>
              <p className="text-2xl font-bold text-blue-600">
                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(metrics.totalSavingsYTD)}
              </p>
            </div>
            <Target className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">ROI Percentage</p>
              <p className="text-2xl font-bold text-purple-600">{metrics.roiPercentage.toFixed(1)}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cost per Transaction</p>
              <p className="text-2xl font-bold text-orange-600">
                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', maximumFractionDigits: 2 }).format(metrics.avgCostPerTransaction)}
              </p>
            </div>
            <Calculator className="h-8 w-8 text-orange-500" />
          </div>
        </Card>
      </div>

      {/* ROI Calculator and Yearly Projection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ROICalculator {...roiData} />
        <SavingsProjection
          currentMonthly={metrics.costSavings}
          yearlyTarget={yearlyTarget}
          progress={currentProgress}
        />
      </div>

      {/* Savings Breakdown Chart */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Savings Breakdown by Category</h3>
            <p className="text-sm text-gray-600">Cost savings distribution across different optimization areas</p>
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'bar' ? (
              <BarChart data={savingsBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="category" 
                  stroke="#666"
                  fontSize={12}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  stroke="#666"
                  fontSize={12}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip 
                  formatter={(value: number) => [
                    new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(value),
                    'Savings'
                  ]}
                  labelFormatter={(label) => `Category: ${label}`}
                />
                <Bar 
                  dataKey="amount" 
                  fill="#0066cc"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            ) : (
              <PieChart>
                <Pie
                  data={savingsBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={140}
                  paddingAngle={2}
                  dataKey="amount"
                  label={({ category, percentage }) => `${category}: ${percentage.toFixed(1)}%`}
                  labelLine={false}
                >
                  {savingsBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [
                    new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(value),
                    'Savings'
                  ]}
                />
              </PieChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Category Legends */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mt-6">
          {savingsBreakdown.map((category, index) => (
            <div key={category.category} className="flex items-center space-x-2">
              <div 
                className="w-4 h-4 rounded"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{category.category}</p>
                <p className="text-xs text-gray-600">
                  {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(category.amount)}
                </p>
                <div className={`flex items-center text-xs ${
                  category.trend === 'up' ? 'text-green-600' : 
                  category.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {category.trend === 'up' && <TrendingUp className="h-3 w-3 mr-1" />}
                  {category.trend === 'down' && <TrendingDown className="h-3 w-3 mr-1" />}
                  <span>{category.comparison > 0 ? '+' : ''}{category.comparison.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Historical Trends */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Historical Savings Trend</h3>
            <p className="text-sm text-gray-600">Monthly savings progression and cumulative impact</p>
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" stroke="#666" fontSize={12} />
              <YAxis 
                stroke="#666" 
                fontSize={12}
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', minimumFractionDigits: 0 }).format(value),
                  name
                ]}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="automation"
                stackId="1"
                stroke="#0066cc"
                fill="#0066cc40"
                name="Automation Savings"
              />
              <Area
                type="monotone"
                dataKey="efficiency"
                stackId="1"
                stroke="#00a86b"
                fill="#00a86b40"
                name="Efficiency Gains"
              />
              <Area
                type="monotone"
                dataKey="quality"
                stackId="1"
                stroke="#ff6b35"
                fill="#ff6b3540"
                name="Quality Improvements"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};
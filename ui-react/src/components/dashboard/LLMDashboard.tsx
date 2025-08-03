import React, { useState, useCallback } from 'react';
import {
  Brain,
  BarChart3,
  Activity,
  Settings,
  Download,
  RefreshCw,
  Filter,
  Search,
  Calendar,
  ChevronDown
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { LLMValidationPanel } from './LLMValidationPanel';
import { RealtimeLLMAnalysis } from './RealtimeLLMAnalysis';
import { LLMConfidenceChart } from './LLMConfidenceChart';
import { LLMValidationResult } from '../../types/llm';

interface LLMDashboardProps {
  fileData?: any;
  isProcessingActive?: boolean;
  className?: string;
}

type TabView = 'validation' | 'realtime' | 'analytics' | 'settings';

interface FilterOptions {
  dateRange: 'last1h' | 'last24h' | 'last7d' | 'last30d' | 'custom';
  confidence: 'all' | 'high' | 'medium' | 'low';
  status: 'all' | 'completed' | 'failed' | 'running';
  category: 'all' | 'clinical' | 'administrative' | 'compliance' | 'quality';
}

export const LLMDashboard: React.FC<LLMDashboardProps> = ({
  fileData,
  isProcessingActive = false,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<TabView>('validation');
  const [isRealtimeConnected, setIsRealtimeConnected] = useState(false);
  const [validationResults, setValidationResults] = useState<LLMValidationResult[]>([]);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: 'last24h',
    confidence: 'all',
    status: 'all',
    category: 'all'
  });
  const [searchQuery, setSearchQuery] = useState('');

  const handleValidationComplete = useCallback((results: LLMValidationResult[]) => {
    setValidationResults(results);
    setActiveTab('analytics'); // Auto-switch to analytics when validation completes
  }, []);

  const handleRealtimeStatusChange = useCallback((connected: boolean) => {
    setIsRealtimeConnected(connected);
  }, []);

  const handleExportResults = () => {
    if (validationResults.length === 0) return;

    const exportData = {
      timestamp: new Date().toISOString(),
      summary: {
        totalFunctions: validationResults.length,
        completedFunctions: validationResults.filter(r => r.status === 'completed').length,
        averageConfidence: validationResults
          .filter(r => r.status === 'completed')
          .reduce((sum, r) => sum + r.confidence, 0) / validationResults.filter(r => r.status === 'completed').length || 0,
        totalFindings: validationResults.reduce((sum, r) => sum + r.findings.length, 0)
      },
      results: validationResults
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm-validation-results-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleRefreshData = () => {
    // Simulate data refresh
    window.location.reload();
  };

  const getTabIcon = (tab: TabView) => {
    switch (tab) {
      case 'validation':
        return <Brain className="h-4 w-4" />;
      case 'realtime':
        return <Activity className="h-4 w-4" />;
      case 'analytics':
        return <BarChart3 className="h-4 w-4" />;
      case 'settings':
        return <Settings className="h-4 w-4" />;
      default:
        return <Brain className="h-4 w-4" />;
    }
  };

  const getTabTitle = (tab: TabView) => {
    switch (tab) {
      case 'validation':
        return 'Validation';
      case 'realtime':
        return 'Real-time';
      case 'analytics':
        return 'Analytics';
      case 'settings':
        return 'Settings';
      default:
        return 'Validation';
    }
  };

  const tabs: TabView[] = ['validation', 'realtime', 'analytics', 'settings'];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl">
            <Brain className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LLM Analysis Dashboard</h1>
            <p className="text-gray-600">AI-powered healthcare data validation and insights</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search functions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>

          {/* Filters */}
          <div className="relative">
            <Button
              variant="secondary"
              onClick={() => setIsFiltersOpen(!isFiltersOpen)}
              className="flex items-center space-x-2"
            >
              <Filter className="h-4 w-4" />
              <span>Filters</span>
              <ChevronDown className="h-4 w-4" />
            </Button>

            {isFiltersOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4">
                <h3 className="font-medium text-gray-900 mb-3">Filter Results</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
                    <select
                      value={filters.dateRange}
                      onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value as any }))}
                      className="w-full text-sm border border-gray-200 rounded px-3 py-2"
                    >
                      <option value="last1h">Last Hour</option>
                      <option value="last24h">Last 24 Hours</option>
                      <option value="last7d">Last 7 Days</option>
                      <option value="last30d">Last 30 Days</option>
                      <option value="custom">Custom Range</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Confidence Level</label>
                    <select
                      value={filters.confidence}
                      onChange={(e) => setFilters(prev => ({ ...prev, confidence: e.target.value as any }))}
                      className="w-full text-sm border border-gray-200 rounded px-3 py-2"
                    >
                      <option value="all">All Levels</option>
                      <option value="high">High (80%+)</option>
                      <option value="medium">Medium (60-79%)</option>
                      <option value="low">Low (&lt;60%)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                    <select
                      value={filters.status}
                      onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as any }))}
                      className="w-full text-sm border border-gray-200 rounded px-3 py-2"
                    >
                      <option value="all">All Status</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                      <option value="running">Running</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Category</label>
                    <select
                      value={filters.category}
                      onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value as any }))}
                      className="w-full text-sm border border-gray-200 rounded px-3 py-2"
                    >
                      <option value="all">All Categories</option>
                      <option value="clinical">Clinical</option>
                      <option value="administrative">Administrative</option>
                      <option value="compliance">Compliance</option>
                      <option value="quality">Quality</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end space-x-2 mt-4 pt-3 border-t border-gray-200">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setFilters({
                      dateRange: 'last24h',
                      confidence: 'all',
                      status: 'all',
                      category: 'all'
                    })}
                  >
                    Reset
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setIsFiltersOpen(false)}
                  >
                    Apply
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <Button
            variant="secondary"
            onClick={handleRefreshData}
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>

          <Button
            variant="primary"
            onClick={handleExportResults}
            disabled={validationResults.length === 0}
            className="flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </Button>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isProcessingActive ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
            }`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Processing Status</p>
              <p className="text-xs text-gray-600">
                {isProcessingActive ? 'Active processing detected' : 'No active processing'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isRealtimeConnected ? 'bg-blue-500 animate-pulse' : 'bg-gray-300'
            }`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Real-time Connection</p>
              <p className="text-xs text-gray-600">
                {isRealtimeConnected ? 'Connected to analysis stream' : 'Not connected'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              validationResults.length > 0 ? 'bg-purple-500' : 'bg-gray-300'
            }`} />
            <div>
              <p className="text-sm font-medium text-gray-900">Validation Results</p>
              <p className="text-xs text-gray-600">
                {validationResults.length > 0
                  ? `${validationResults.length} functions analyzed`
                  : 'No results available'
                }
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {getTabIcon(tab)}
              <span>{getTabTitle(tab)}</span>
              {tab === 'realtime' && isRealtimeConnected && (
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'validation' && (
          <LLMValidationPanel
            fileData={fileData}
            onValidationComplete={handleValidationComplete}
          />
        )}

        {activeTab === 'realtime' && (
          <RealtimeLLMAnalysis
            isActive={isProcessingActive}
            onStatusChange={handleRealtimeStatusChange}
          />
        )}

        {activeTab === 'analytics' && (
          <LLMConfidenceChart results={validationResults} />
        )}

        {activeTab === 'settings' && (
          <Card className="p-8 text-center">
            <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">LLM Settings</h3>
            <p className="text-gray-600 mb-4">Configure LLM validation parameters and preferences.</p>
            <div className="space-y-4 max-w-md mx-auto">
              <div className="text-left">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Parallel Execution
                </label>
                <select className="w-full border border-gray-200 rounded-lg px-3 py-2">
                  <option>Enabled (Recommended)</option>
                  <option>Disabled</option>
                </select>
              </div>
              <div className="text-left">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Concurrent Functions
                </label>
                <select className="w-full border border-gray-200 rounded-lg px-3 py-2">
                  <option>3 (Default)</option>
                  <option>5</option>
                  <option>10</option>
                </select>
              </div>
              <div className="text-left">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timeout per Function (seconds)
                </label>
                <input
                  type="number"
                  defaultValue={120}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2"
                />
              </div>
              <Button variant="primary" className="w-full">
                Save Settings
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import { useToast } from '@contexts/ToastContext';
import { useTheme } from '@contexts/ThemeContext';
import { useInsurer } from '@contexts/InsurerContext';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import ThemeToggle from '@components/ui/ThemeToggle';
import ToastContainer from '@components/ui/ToastContainer';
import InsurerWorkflowIntegration from '@components/dashboard/InsurerWorkflowIntegration';
import FileUploadPage from './FileUploadPage';
import RequestHistoryDemo from './RequestHistoryDemo';
import InsurerDashboardPage from './InsurerDashboardPage';
import logoImage from '@assets/logo.png';

const DashboardOverview: React.FC = () => {
  const { metrics } = useApp();
  const { showToast } = useToast();
  const { isDarkMode } = useTheme();
  const { metrics: insurerMetrics, notifications } = useInsurer();

  const handleTestToast = () => {
    showToast({
      type: 'success',
      title: 'Welcome to Healthcare AI Platform!',
      message: 'Your React dashboard is working perfectly.',
    });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">Medical Director Dashboard</h1>
          <p className="text-gray-600 dark:text-dark-text-secondary mt-1">
            Dubai Health Insurance • Pre-Authorization Management
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">Today's Date</div>
            <div className="text-xs text-gray-500 dark:text-dark-text-secondary">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
          </div>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">{insurerMetrics?.workload?.totalPending || 24}</div>
              <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Pending Reviews</div>
              <div className="text-xs text-blue-600 mt-1">Requires attention</div>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
              <span className="text-2xl">📋</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">{metrics.autoApproved}%</div>
              <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Auto-Approval Rate</div>
              <div className="text-xs text-green-600 mt-1">+5% this month</div>
            </div>
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">{metrics.avgResponseTime}</div>
              <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Avg Decision Time</div>
              <div className="text-xs text-orange-600 mt-1">Target: 24hrs</div>
            </div>
            <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-full">
              <span className="text-2xl">⏱️</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">{metrics.costSavings}</div>
              <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Cost Efficiency</div>
              <div className="text-xs text-purple-600 mt-1">This quarter</div>
            </div>
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
              <span className="text-2xl">💎</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Dashboard Status & Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Summary */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary mb-4">Today's Summary</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                <span className="text-gray-700 dark:text-dark-text-secondary">Approved Today</span>
              </div>
              <span className="text-green-600 font-bold text-lg">{metrics.approvedCount}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-orange-500 rounded-full mr-3"></div>
                <span className="text-gray-700 dark:text-dark-text-secondary">Awaiting Review</span>
              </div>
              <span className="text-orange-600 font-bold text-lg">{insurerMetrics?.workload?.totalPending || 0}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                <span className="text-gray-700 dark:text-dark-text-secondary">In Progress</span>
              </div>
              <span className="text-blue-600 font-bold text-lg">{insurerMetrics?.workload?.underReview || 8}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-3"></div>
                <span className="text-gray-700 dark:text-dark-text-secondary">Denied Today</span>
              </div>
              <span className="text-red-600 font-bold text-lg">{metrics.deniedCount}</span>
            </div>
          </div>
        </Card>

        {/* System Status */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary mb-4">System Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-700 dark:text-dark-text-secondary">AI Engine</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700 dark:text-dark-text-secondary">Processing Queue</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">Normal</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700 dark:text-dark-text-secondary">API Status</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Healthy</span>
            </div>
            <div className="pt-2 border-t border-gray-100 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-dark-text-tertiary">Last updated: {new Date().toLocaleTimeString()}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Workflow Management */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity Feed */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary mb-4">Recent Activity</h3>
          <div className="space-y-4">
            <div className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border-l-4 border-red-500">
              <div className="flex-shrink-0 mt-1">
                <span className="text-red-500 text-sm">🚨</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  3 high-priority requests require immediate review
                </p>
                <p className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
                  SLA deadline approaching • 2 minutes ago
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border-l-4 border-green-500">
              <div className="flex-shrink-0 mt-1">
                <span className="text-green-500 text-sm">✅</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  AI analysis completed for 8 new requests
                </p>
                <p className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
                  Ready for medical director review • 15 minutes ago
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-500">
              <div className="flex-shrink-0 mt-1">
                <span className="text-blue-500 text-sm">📋</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  12 requests processed successfully today
                </p>
                <p className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
                  Average decision time: 14.2 minutes • 1 hour ago
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Performance Overview */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary mb-4">Performance Overview</h3>
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">SLA Compliance</span>
                <span className="text-lg font-bold text-blue-600">96.2%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{width: '96.2%'}}></div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">AI Accuracy</span>
                <span className="text-lg font-bold text-green-600">94.7%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{width: '94.7%'}}></div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">Cost Efficiency</span>
                <span className="text-lg font-bold text-purple-600">87.3%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{width: '87.3%'}}></div>
              </div>
            </div>

            <div className="pt-2 mt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                📊 All metrics updated in real-time • Last sync: {new Date().toLocaleTimeString()}
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const DashboardPage: React.FC = () => {
  const { metrics: insurerMetrics } = useInsurer();
  const location = useLocation();

  // Determine current active route
  const getCurrentRoute = () => {
    const path = location.pathname;
    if (path === '/dashboard' || path === '/dashboard/overview') return 'overview';
    if (path.includes('/dashboard/requests')) return 'requests';
    if (path.includes('/dashboard/upload')) return 'upload';
    if (path.includes('/dashboard/analytics')) return 'analytics';
    return 'overview';
  };

  const currentRoute = getCurrentRoute();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg-primary transition-colors duration-200">
      {/* Navigation */}
      <nav className="bg-white dark:bg-dark-bg-secondary shadow-soft border-b border-gray-200 dark:border-dark-border-primary transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center">
              <img src={logoImage} alt="Healthcare AI Platform" className="h-8 w-8" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-dark-text-primary">Dubai Health Insurance</span>
            </Link>
            <div className="flex items-center space-x-1">
              <Link
                to="/dashboard/overview"
                className={`px-4 py-2 rounded-lg font-medium transition-colors relative ${
                  currentRoute === 'overview'
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                🏠 Overview
              </Link>
              <Link
                to="/dashboard/requests"
                className={`px-4 py-2 rounded-lg font-medium transition-colors relative ${
                  currentRoute === 'requests'
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                📋 Request Inbox
                {insurerMetrics?.workload?.totalPending > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[1rem] text-center">
                    {insurerMetrics.workload?.totalPending}
                  </span>
                )}
              </Link>
              <Link
                to="/dashboard/upload"
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentRoute === 'upload'
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                📄 Process Files
              </Link>
              <Link
                to="/dashboard/analytics"
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  currentRoute === 'analytics'
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    : 'text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                📊 Analytics
              </Link>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-sm">
                  <span className="text-white font-medium">AA</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-700 dark:text-dark-text-primary">Dr. Ahmed Al-Mansouri</div>
                  <div className="text-xs text-gray-500 dark:text-dark-text-secondary">Medical Director</div>
                </div>
                <ThemeToggle variant="dropdown" size="md" />
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Routes>
          <Route index element={<DashboardOverview />} />
          <Route path="overview" element={<DashboardOverview />} />
          <Route path="requests" element={<InsurerDashboardPage />} />
          <Route path="upload" element={<FileUploadPage />} />
          <Route path="analytics" element={<RequestHistoryDemo />} />
          <Route path="*" element={<Navigate to="/dashboard/overview" replace />} />
        </Routes>
      </main>

      <ToastContainer />
    </div>
  );
};

export default DashboardPage;
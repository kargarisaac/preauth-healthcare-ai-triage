import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import { useToast } from '@contexts/ToastContext';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import ToastContainer from '@components/ui/ToastContainer';
import FileUploadArea from '@components/dashboard/FileUploadArea';
import FileUploadPage from './FileUploadPage';
import RequestHistoryDemo from './RequestHistoryDemo';

const DashboardOverview: React.FC = () => {
  const { metrics } = useApp();
  const { showToast } = useToast();

  const handleTestToast = () => {
    showToast({
      type: 'success',
      title: 'Welcome to Nazmito!',
      message: 'Your React dashboard is working perfectly.',
    });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
          <p className="text-gray-600 mt-1">
            Monitor and manage pre-authorization requests with AI-powered intelligence
          </p>
        </div>
        <Button onClick={handleTestToast}>
          Test Toast
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="metric-card">
          <div className="flex items-center">
            <div className="metric-icon bg-blue-100 text-blue-600">📝</div>
            <div className="ml-4">
              <div className="metric-value">{metrics.activeRequests}</div>
              <div className="metric-label">Active Requests</div>
              <div className="metric-change metric-change-positive">+12% this week</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card">
          <div className="flex items-center">
            <div className="metric-icon bg-green-100 text-green-600">⚡</div>
            <div className="ml-4">
              <div className="metric-value">{metrics.autoApproved}%</div>
              <div className="metric-label">Auto-Approved</div>
              <div className="metric-change metric-change-positive">+5% improvement</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card">
          <div className="flex items-center">
            <div className="metric-icon bg-orange-100 text-orange-600">⏱️</div>
            <div className="ml-4">
              <div className="metric-value">{metrics.avgResponseTime}</div>
              <div className="metric-label">Avg Response Time</div>
              <div className="metric-change metric-change-positive">-45% faster</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card">
          <div className="flex items-center">
            <div className="metric-icon bg-purple-100 text-purple-600">💰</div>
            <div className="ml-4">
              <div className="metric-value">{metrics.costSavings}</div>
              <div className="metric-label">Cost Savings</div>
              <div className="metric-change metric-change-positive">This quarter</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title="Quick Actions">
          <div className="space-y-4">
            <Button variant="primary" fullWidth>
              📝 Submit New Request
            </Button>
            <Link to="/dashboard/requests">
              <Button variant="secondary" fullWidth>
                🔍 View All Requests
              </Button>
            </Link>
            <Link to="/dashboard/upload">
              <Button variant="secondary" fullWidth>
                📄 Upload & Process Files
              </Button>
            </Link>
            <Button variant="secondary" fullWidth>
              📊 View Analytics
            </Button>
          </div>
        </Card>

        <Card title="Status Summary">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-success-500 rounded-full mr-3"></div>
                <span className="font-medium">Approved</span>
              </div>
              <span className="text-success-600 font-bold">{metrics.approvedCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-warning-500 rounded-full mr-3"></div>
                <span className="font-medium">Pending Review</span>
              </div>
              <span className="text-warning-600 font-bold">{metrics.pendingCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-error-500 rounded-full mr-3"></div>
                <span className="font-medium">Denied</span>
              </div>
              <span className="text-error-600 font-bold">{metrics.deniedCount}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Upload */}
      <Card title="Quick Upload">
        <div className="space-y-4">
          <p className="text-gray-600">
            Upload healthcare files directly from the dashboard for quick processing.
          </p>
          <FileUploadArea />
        </div>
      </Card>
    </div>
  );
};

const DashboardPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-soft border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center">
              <img src="/assets/logo.png" alt="Nazmito" className="h-8 w-8" />
              <span className="ml-2 text-xl font-bold text-gray-900">Nazmito Platform</span>
            </Link>
            <div className="flex items-center space-x-6">
              <span className="nav-link-active">Dashboard</span>
              <Link to="/dashboard/upload" className="nav-link">Upload</Link>
              <Link to="/dashboard/requests" className="nav-link">Requests</Link>
              <Link to="/" className="nav-link">Home</Link>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm">
                  👤
                </div>
                <span className="text-sm font-medium text-gray-700">Dr. Sarah Ahmed</span>
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
          <Route path="upload" element={<FileUploadPage />} />
          <Route path="requests" element={<RequestHistoryDemo />} />
          <Route path="*" element={<Navigate to="/dashboard/overview" replace />} />
        </Routes>
      </main>

      <ToastContainer />
    </div>
  );
};

export default DashboardPage;
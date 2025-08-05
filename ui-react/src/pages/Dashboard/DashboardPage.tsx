import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { useApp } from '@contexts/AppContext';
import { useToast } from '@contexts/ToastContext';
import { useTheme } from '@contexts/ThemeContext';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import ThemeToggle from '@components/ui/ThemeToggle';
import ToastContainer from '@components/ui/ToastContainer';
import FileUploadArea from '@components/dashboard/FileUploadArea';
import FileUploadPage from './FileUploadPage';
import PatientFileUploadPage from './PatientFileUploadPage';
import RequestHistoryDemo from './RequestHistoryDemo';
import PatientSelectionPage from './PatientSelectionPage';
import PatientDashboardPage from './PatientDashboardPage';
import logoImage from '@assets/logo.png';

const DashboardOverview: React.FC = () => {
  const { metrics } = useApp();
  const { showToast } = useToast();
  const { isDarkMode } = useTheme();

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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-dark-text-primary">Dashboard Overview</h1>
          <p className="text-gray-600 dark:text-dark-text-secondary mt-1">
            Monitor and manage pre-authorization requests with AI-powered intelligence
          </p>
        </div>
        <Button onClick={handleTestToast}>
          Test Toast
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="metric-card" padding="md">
          <div className="flex items-center w-full">
            <div className="metric-icon bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">📝</div>
            <div className="ml-4 flex-1">
              <div className="metric-value text-gray-900 dark:text-dark-text-primary">{metrics.activeRequests}</div>
              <div className="metric-label text-gray-600 dark:text-dark-text-secondary">Active Requests</div>
              <div className="metric-change metric-change-positive text-green-600 dark:text-green-400">+12% this week</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card" padding="md">
          <div className="flex items-center w-full">
            <div className="metric-icon bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">⚡</div>
            <div className="ml-4 flex-1">
              <div className="metric-value text-gray-900 dark:text-dark-text-primary">{metrics.autoApproved}%</div>
              <div className="metric-label text-gray-600 dark:text-dark-text-secondary">Auto-Approved</div>
              <div className="metric-change metric-change-positive text-green-600 dark:text-green-400">+5% improvement</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card" padding="md">
          <div className="flex items-center w-full">
            <div className="metric-icon bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400">⏱️</div>
            <div className="ml-4 flex-1">
              <div className="metric-value text-gray-900 dark:text-dark-text-primary">{metrics.avgResponseTime}</div>
              <div className="metric-label text-gray-600 dark:text-dark-text-secondary">Avg Response Time</div>
              <div className="metric-change metric-change-positive text-green-600 dark:text-green-400">-45% faster</div>
            </div>
          </div>
        </Card>

        <Card className="metric-card" padding="md">
          <div className="flex items-center w-full">
            <div className="metric-icon bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">💰</div>
            <div className="ml-4 flex-1">
              <div className="metric-value text-gray-900 dark:text-dark-text-primary">{metrics.costSavings}</div>
              <div className="metric-label text-gray-600 dark:text-dark-text-secondary">Cost Savings</div>
              <div className="metric-change metric-change-positive text-green-600 dark:text-green-400">This quarter</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card title="Quick Actions">
          <div className="space-y-4">
            <Link to="/dashboard/patients">
              <Button variant="primary" fullWidth>
                👥 Select Patient
              </Button>
            </Link>
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
            <Link to="/dashboard/patient-upload">
              <Button variant="secondary" fullWidth>
                👤 Patient File Upload
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
              <div className="flex items-center w-full">
                <div className="w-3 h-3 bg-success-500 dark:bg-success-400 rounded-full mr-3"></div>
                <span className="font-medium text-gray-900 dark:text-dark-text-primary">Approved</span>
              </div>
              <span className="text-success-600 dark:text-success-400 font-bold">{metrics.approvedCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center w-full">
                <div className="w-3 h-3 bg-warning-500 dark:bg-warning-400 rounded-full mr-3"></div>
                <span className="font-medium text-gray-900 dark:text-dark-text-primary">Pending Review</span>
              </div>
              <span className="text-warning-600 dark:text-warning-400 font-bold">{metrics.pendingCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center w-full">
                <div className="w-3 h-3 bg-error-500 dark:bg-error-400 rounded-full mr-3"></div>
                <span className="font-medium text-gray-900 dark:text-dark-text-primary">Denied</span>
              </div>
              <span className="text-error-600 dark:text-error-400 font-bold">{metrics.deniedCount}</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Upload */}
      <Card title="Quick Upload">
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-dark-text-secondary">
            Upload healthcare files directly from the dashboard for quick processing.
          </p>
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-dark-text-tertiary mb-4">
              For patient-specific uploads, use the dedicated patient upload workflow.
            </p>
            <Link to="/dashboard/patient-upload">
              <Button variant="primary">
                Go to Patient Upload
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

const DashboardPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg-primary transition-colors duration-200">
      {/* Navigation */}
      <nav className="bg-white dark:bg-dark-bg-secondary shadow-soft border-b border-gray-200 dark:border-dark-border-primary transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center">
              <img src={logoImage} alt="Nazmito" className="h-8 w-8" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-dark-text-primary">Nazmito Platform</span>
            </Link>
            <div className="flex items-center space-x-6">
              <span className="nav-link-active text-primary-600 dark:text-primary-400">Dashboard</span>
              <Link to="/dashboard/patients" className="nav-link text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary">Patients</Link>
              <Link to="/dashboard/upload" className="nav-link text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary">Upload</Link>
              <Link to="/dashboard/patient-upload" className="nav-link text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary">Patient Upload</Link>
              <Link to="/dashboard/requests" className="nav-link text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary">Requests</Link>
              <Link to="/" className="nav-link text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary">Home</Link>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gray-300 dark:bg-dark-bg-tertiary rounded-full flex items-center justify-center text-sm">
                  👤
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-dark-text-primary">Dr. Sarah Ahmed</span>
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
          <Route path="patients" element={<PatientSelectionPage />} />
          <Route path="patient/:patientId" element={<PatientDashboardPage />} />
          <Route path="upload" element={<FileUploadPage />} />
          <Route path="patient-upload" element={<PatientFileUploadPage />} />
          <Route path="requests" element={<RequestHistoryDemo />} />
          <Route path="*" element={<Navigate to="/dashboard/overview" replace />} />
        </Routes>
      </main>

      <ToastContainer />
    </div>
  );
};

export default DashboardPage;

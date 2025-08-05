import React, { useEffect, useState } from 'react';
import {
  User,
  Upload,
  Play,
  Download,
  RefreshCw,
  Calendar,
  Shield,
  Activity,
  FileText,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { Card, Button, Badge, StatusBadge, LoadingSpinner } from '../ui';
import { usePatient } from '../../contexts/PatientContext';
import { useToast } from '../../contexts/ToastContext';
import type { PatientInfo, DashboardData } from '../../types/api';

interface PatientDashboardProps {
  patientId: string;
  className?: string;
}

const PatientDashboard: React.FC<PatientDashboardProps> = ({
  patientId,
  className = ''
}) => {
  const { dashboardData, fetchPatientDashboard, isLoading, error } = usePatient();
  const { showToast } = useToast();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (patientId) {
      fetchPatientDashboard(patientId);
    }
  }, [patientId, fetchPatientDashboard]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchPatientDashboard(patientId);
      showToast({
        type: 'success',
        title: 'Data Refreshed',
        message: 'Patient dashboard data has been updated',
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Refresh Failed',
        message: 'Failed to refresh patient data',
      });
    } finally {
      setRefreshing(false);
    }
  };

  const handleUploadFile = () => {
    // Navigate to file upload page for this patient
    window.location.href = `/dashboard/patient/${patientId}/upload`;
  };

  const handleRunAnalysis = () => {
    // Navigate to analysis page or trigger analysis
    showToast({
      type: 'info',
      title: 'Analysis Started',
      message: 'Running multi-agent analysis for patient',
    });
  };

  const handleExportData = () => {
    // Export patient data
    showToast({
      type: 'info',
      title: 'Export Started',
      message: 'Preparing patient data export',
    });
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (isLoading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
        <p className="ml-4 text-gray-600">Loading patient dashboard...</p>
      </div>
    );
  }

  if (error && !dashboardData) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Dashboard</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={() => fetchPatientDashboard(patientId)}>
          Try Again
        </Button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="text-center py-12">
        <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Data Available</h3>
        <p className="text-gray-600">No dashboard data found for this patient</p>
      </div>
    );
  }

  const { patient_info, summary_stats, recent_files, analysis_history } = dashboardData;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Patient Profile Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{patient_info.folder_name}</h1>
              <div className="flex items-center space-x-4 mt-1">
                <span className="text-gray-600">ID: {patient_info.patient_id}</span>
                <Badge variant={patient_info.has_profile ? "success" : "warning"}>
                  {patient_info.has_profile ? "Profile Available" : "No Profile"}
                </Badge>
              </div>
              <div className="flex items-center space-x-2 mt-2">
                <Shield className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">
                  {summary_stats.patient_name || 'Unknown'} - {summary_stats.insurance_company || 'Unknown'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUploadFile}
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload File
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRunAnalysis}
            >
              <Play className="h-4 w-4 mr-2" />
              Run Analysis
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleExportData}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
          </div>
        </div>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">XML Files</p>
              <p className="text-2xl font-bold text-gray-900">{patient_info.xml_files}</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <FileText className="h-6 w-6" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Processed Files</p>
              <p className="text-2xl font-bold text-gray-900">{patient_info.processed_json_files}</p>
            </div>
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <CheckCircle className="h-6 w-6" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round((summary_stats.processing_success_rate || 0) * 100)}%</p>
            </div>
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <Clock className="h-6 w-6" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Historical Records</p>
              <p className="text-2xl font-bold text-gray-900">{summary_stats.total_historical_records || 0}</p>
            </div>
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <TrendingUp className="h-6 w-6" />
            </div>
          </div>
        </Card>
      </div>

      {/* File Processing Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">File Processing Overview</h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Processed ({patient_info.processed_json_files})</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Pending ({patient_info.xml_files - patient_info.processed_json_files})</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Claude Available ({summary_stats.claude_analysis_available ? 'Yes' : 'No'})</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {Math.round((summary_stats.processing_success_rate || 0) * 100)}%
            </div>
            <p className="text-sm text-gray-600">Processing Success Rate</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {patient_info.xml_files}
            </div>
            <p className="text-sm text-gray-600">Total XML Files</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900 mb-2">
              {summary_stats.last_activity ? formatDate(summary_stats.last_activity) : 'N/A'}
            </div>
            <p className="text-sm text-gray-600">Last Activity</p>
          </div>
        </div>
      </Card>

      {/* Recent Files */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Files</h3>
          <Button variant="secondary" size="sm">
            View All
          </Button>
        </div>
        
        <div className="space-y-3">
          {recent_files.length > 0 ? (
            recent_files.slice(0, 5).map((file, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  file.processed ? 'bg-green-100' : 'bg-yellow-100'
                }`}>
                  {file.processed ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <Clock className="h-4 w-4 text-yellow-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                  <p className="text-xs text-gray-600">
                    {file.source} • {file.file_size ? `${Math.round(file.file_size / 1024)} KB` : 'Unknown size'}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">
                    {file.upload_date ? formatDate(file.upload_date) : 'Unknown date'}
                  </span>
                  {file.processed && file.processed_date && (
                    <p className="text-xs text-green-600">Processed {formatDate(file.processed_date)}</p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-gray-500">
              <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No recent files found</p>
            </div>
          )}
        </div>
      </Card>

      {/* System Status */}
      <div className="text-center text-xs text-gray-500">
        Last updated: {summary_stats.last_activity ? formatDate(summary_stats.last_activity) : 'Never'}
      </div>
    </div>
  );
};

export default PatientDashboard;
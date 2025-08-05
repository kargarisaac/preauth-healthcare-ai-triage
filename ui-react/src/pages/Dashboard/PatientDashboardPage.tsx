import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  User,
  Upload,
  Activity,
  FileText,
  Brain,
  Settings,
  RefreshCw
} from 'lucide-react';
import { Card, Button, Tabs, Breadcrumbs, LoadingSpinner, ErrorBoundary } from '../../components/ui';
import type { BreadcrumbItem } from '../../components/ui';
import PatientDashboard from '../../components/dashboard/PatientDashboard';
import PatientHistoryTable from '../../components/dashboard/PatientHistoryTable';
import AnalysisResultsViewer from '../../components/dashboard/AnalysisResultsViewer';
import { usePatient } from '../../contexts/PatientContext';
import { useToast } from '../../contexts/ToastContext';

// Mock data for demonstration - replace with real API calls
const mockFileData = [
  {
    id: '1',
    filename: 'medical_claim_20241201.xml',
    upload_date: '2024-12-01T10:30:00Z',
    file_size: 245760,
    source: 'eClaimLink' as const,
    status: 'completed' as const,
    processed_date: '2024-12-01T10:32:00Z',
    total_claims: 5,
    approved_claims: 4,
    total_amount: 12500,
    analysis_status: 'completed' as const,
  },
  {
    id: '2',
    filename: 'health_data_export.csv',
    upload_date: '2024-11-28T14:15:00Z',
    file_size: 156800,
    source: 'CSV' as const,
    status: 'completed' as const,
    processed_date: '2024-11-28T14:18:00Z',
    total_claims: 8,
    approved_claims: 6,
    total_amount: 8750,
    analysis_status: 'not_started' as const,
  },
  {
    id: '3',
    filename: 'shafafiya_report_nov.xml',
    upload_date: '2024-11-25T09:45:00Z',
    file_size: 412000,
    source: 'Shafafiya' as const,
    status: 'processing' as const,
    total_claims: 12,
    analysis_status: 'in_progress' as const,
  },
  {
    id: '4',
    filename: 'emergency_visit_data.xml',
    upload_date: '2024-11-20T16:20:00Z',
    file_size: 89600,
    source: 'eClaimLink' as const,
    status: 'error' as const,
    error_message: 'Invalid XML structure: Missing required elements',
    analysis_status: 'failed' as const,
  },
];

const mockAnalysisResults = {
  id: 'analysis_123',
  patient_id: 'patient_001',
  analysis_date: '2024-12-01T15:30:00Z',
  confidence_score: 0.89,
  clinical_summary: {
    primary_diagnosis: 'Type 2 Diabetes Mellitus with complications',
    secondary_conditions: ['Hypertension', 'Obesity', 'Peripheral neuropathy'],
    medications: ['Metformin 1000mg BID', 'Lisinopril 10mg daily', 'Atorvastatin 20mg daily'],
    procedures: ['HbA1c monitoring', 'Blood pressure monitoring', 'Diabetic foot exam'],
    risk_factors: ['Family history of diabetes', 'Sedentary lifestyle', 'High BMI'],
  },
  risk_assessment: {
    overall_risk: 'high' as const,
    risk_score: 78,
    risk_factors: [
      {
        factor: 'Uncontrolled diabetes',
        impact: 'high' as const,
        description: 'HbA1c levels consistently above target range',
      },
      {
        factor: 'Cardiovascular risk',
        impact: 'medium' as const,
        description: 'Multiple cardiovascular risk factors present',
      },
    ],
    recommendations: [
      'Intensify diabetes management with additional medication',
      'Refer to endocrinologist for specialist care',
      'Implement structured lifestyle intervention program',
    ],
  },
  recommendations: [
    {
      category: 'clinical' as const,
      priority: 'high' as const,
      title: 'Optimize Diabetes Management',
      description: 'Current HbA1c levels indicate suboptimal glycemic control',
      expected_outcome: 'Improved glycemic control and reduced risk of complications',
      timeframe: '3-6 months',
    },
    {
      category: 'preventive' as const,
      priority: 'medium' as const,
      title: 'Cardiovascular Risk Reduction',
      description: 'Implement comprehensive cardiovascular risk reduction strategy',
      expected_outcome: 'Reduced 10-year cardiovascular risk by 25%',
      timeframe: '6-12 months',
    },
  ],
  cost_analysis: {
    estimated_total_cost: 45000,
    cost_breakdown: [
      { category: 'Medications', amount: 15000, percentage: 33 },
      { category: 'Monitoring', amount: 8000, percentage: 18 },
      { category: 'Specialist visits', amount: 12000, percentage: 27 },
      { category: 'Prevention', amount: 10000, percentage: 22 },
    ],
    potential_savings: 12000,
    savings_opportunities: [
      'Generic medication substitution could save AED 3,000 annually',
      'Home monitoring program could reduce clinic visits by 40%',
      'Early intervention could prevent costly complications',
    ],
  },
  quality_metrics: {
    data_completeness: 94,
    clinical_coherence: 87,
    guideline_adherence: 91,
    cost_effectiveness: 83,
  },
  agent_insights: [
    {
      agent_name: 'Clinical Risk Assessor',
      specialty: 'Internal Medicine',
      findings: [
        'Multiple diabetes complications present',
        'Medication adherence appears suboptimal',
        'Family history indicates genetic predisposition',
      ],
      recommendations: [
        'Intensify glucose monitoring',
        'Consider insulin therapy',
        'Schedule endocrinology consultation',
      ],
      confidence: 0.92,
    },
    {
      agent_name: 'Cost Optimizer',
      specialty: 'Health Economics',
      findings: [
        'High medication costs relative to outcomes',
        'Frequent emergency department utilization',
        'Preventive care gaps identified',
      ],
      recommendations: [
        'Implement medication therapy management',
        'Enhance primary care coordination',
        'Invest in preventive interventions',
      ],
      confidence: 0.85,
    },
  ],
};

const PatientDashboardPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { selectedPatient, dashboardData, fetchPatientDashboard, isLoading, error } = usePatient();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (patientId) {
      fetchPatientDashboard(patientId);
    }
  }, [patientId, fetchPatientDashboard]);

  const handleGoBack = () => {
    navigate('/dashboard');
  };

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
  };

  const handleViewFileDetails = (record: any) => {
    showToast({
      type: 'info',
      title: 'File Details',
      message: `Viewing details for ${record.filename}`,
    });
  };

  const handleReanalyzeFile = (record: any) => {
    showToast({
      type: 'info',
      title: 'Analysis Started',
      message: `Starting analysis for ${record.filename}`,
    });
  };

  const handleDownloadFile = (record: any) => {
    showToast({
      type: 'info',
      title: 'Download Started',
      message: `Downloading ${record.filename}`,
    });
  };

  const handleExportAnalysis = (format: 'pdf' | 'json' | 'csv') => {
    showToast({
      type: 'success',
      title: 'Export Started',
      message: `Exporting analysis results as ${format.toUpperCase()}`,
    });
  };

  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    try {
      if (patientId) {
        await fetchPatientDashboard(patientId);
      }
      showToast({
        type: 'success',
        title: 'Data Refreshed',
        message: 'All patient data has been updated',
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Refresh Failed',
        message: 'Failed to refresh patient data',
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!patientId) {
    return (
      <div className="text-center py-12">
        <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Patient Selected</h3>
        <p className="text-gray-600 mb-4">Please select a patient to view their dashboard</p>
        <Button onClick={handleGoBack}>
          Go to Patient Selection
        </Button>
      </div>
    );
  }

  // Breadcrumb items
  const breadcrumbItems: BreadcrumbItem[] = [
    { id: 'dashboard', label: 'Dashboard', href: '/dashboard' },
    { id: 'patients', label: 'Patients', href: '/dashboard/patients' },
    {
      id: 'patient',
      label: dashboardData?.patient_info?.folder_name || selectedPatient?.folder_name || `Patient ${patientId}`,
      isActive: true,
      metadata: { patientId },
    },
  ];

  // Tab configuration
  const tabItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: Activity,
    },
    {
      id: 'history',
      label: 'File History',
      icon: FileText,
    },
    {
      id: 'analysis',
      label: 'Analysis Results',
      icon: Brain,
    },
  ];

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-4">
              <div className="flex items-center space-x-4">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleGoBack}
                  className="flex items-center"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back
                </Button>
                
                <Breadcrumbs
                  items={breadcrumbItems}
                  onItemClick={(item) => item.href && navigate(item.href)}
                  showTooltips
                />
              </div>

              <div className="flex items-center space-x-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleRefreshAll}
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                  Refresh All
                </Button>
                <Button variant="secondary" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Tab Navigation */}
          <div className="mb-6">
            <Tabs
              items={tabItems}
              activeTab={activeTab}
              onTabChange={handleTabChange}
              variant="underline"
              size="md"
              showContent={false}
            />
          </div>

          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'overview' && (
              <PatientDashboard
                patientId={patientId}
                className="space-y-6"
              />
            )}

            {activeTab === 'history' && (
              <div className="space-y-6">
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">File Processing History</h2>
                      <p className="text-gray-600">
                        Track all files uploaded and processed for this patient
                      </p>
                    </div>
                    <Button
                      variant="primary"
                      onClick={() => navigate(`/dashboard/patient/${patientId}/upload`)}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      Upload New File
                    </Button>
                  </div>
                </Card>

                <PatientHistoryTable
                  patientId={patientId}
                  data={mockFileData}
                  isLoading={isLoading}
                  onViewDetails={handleViewFileDetails}
                  onReanalyze={handleReanalyzeFile}
                  onDownload={handleDownloadFile}
                />
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="space-y-6">
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">Multi-Agent Analysis Results</h2>
                      <p className="text-gray-600">
                        AI-powered analysis of patient data using multiple specialized agents
                      </p>
                    </div>
                    <Button variant="primary">
                      <Brain className="h-4 w-4 mr-2" />
                      Run New Analysis
                    </Button>
                  </div>
                </Card>

                {dashboardData?.patient_info ? (
                  <AnalysisResultsViewer
                    analysisResults={mockAnalysisResults}
                    patient={dashboardData.patient_info}
                    onExport={handleExportAnalysis}
                  />
                ) : (
                  <Card className="p-12 text-center">
                    <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analysis Available</h3>
                    <p className="text-gray-600">
                      Run an analysis to see detailed insights for this patient
                    </p>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default PatientDashboardPage;
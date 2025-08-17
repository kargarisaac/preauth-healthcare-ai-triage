import React, { useState, useEffect } from 'react';
import {
  FileText,
  User,
  Building,
  Stethoscope,
  DollarSign,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Brain,
  Shield,
  TrendingUp,
  Eye,
  Download,
  ExternalLink,
  Flag,
  Star,
  Activity,
  Heart,
  Pill,
} from 'lucide-react';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import { DecisionWorkflow } from './DecisionWorkflow';
import type {
  InsurerRequest,
  RiskFlag,
  QualityIndicator,
  MedicalDirectorDecision,
  DecisionType,
} from '@/types/insurer';

// Mock request data - replace with actual API
const mockRequestData: InsurerRequest = {
  id: 'REQ-2025-001',
  requestNumber: 'PA-001-2025',
  memberId: 'MEM-789',
  memberName: 'Ahmed Al-Mansouri',
  dateOfBirth: '1985-03-15',
  emiratesId: '784-1985-1234567-8',
  providerId: 'PROV-001',
  providerName: 'Dubai Healthcare City',
  providerType: 'Hospital',
  facility: 'Cardiac Surgery Unit',
  type: 'authorization',
  status: 'pending',
  priority: 'high',
  submissionDate: '2025-08-17T10:30:00Z',
  diagnosis: 'Coronary Artery Disease',
  diagnosisCodes: ['I25.10'],
  procedure: 'Coronary Angioplasty',
  procedureCodes: ['92928'],
  serviceDescription: 'Percutaneous coronary intervention with drug-eluting stent',
  requestedAmount: 45000,
  currency: 'AED',
  format: 'eClaimLink',
  documents: [
    {
      id: 'DOC-001',
      name: 'Cardiac Catheterization Report.pdf',
      type: 'medical_report',
      size: 2048576,
      uploadedAt: '2025-08-17T10:25:00Z',
      url: '/api/documents/DOC-001',
    },
    {
      id: 'DOC-002',
      name: 'ECG Results.pdf',
      type: 'lab_result',
      size: 1024768,
      uploadedAt: '2025-08-17T10:27:00Z',
      url: '/api/documents/DOC-002',
    },
  ],
  createdAt: '2025-08-17T10:30:00Z',
  updatedAt: '2025-08-17T10:30:00Z',
  tags: ['cardiac', 'high-value', 'urgent'],
  notes: 'Urgent case - patient scheduled for procedure tomorrow. Recent cardiac catheterization shows significant stenosis.',
  
  // AI Analysis
  aiAnalysis: {
    recommendation: 'approve',
    confidence: 87,
    reasoning: `Patient meets clinical criteria for PCI based on:
• Documented significant coronary stenosis (>70% LAD)
• Symptomatic angina despite optimal medical therapy
• Appropriate candidate for intervention
• Evidence-based guidelines support intervention
• No contraindications identified`,
    riskScore: 23,
    policyCompliance: 92,
    evidenceStrength: 85,
    clinicalNecessity: 91,
  },
  
  // Risk Flags
  riskFlags: [
    {
      id: 'RF-001',
      type: 'financial',
      severity: 'medium',
      title: 'High Cost Procedure',
      description: 'Request amount (AED 45,000) exceeds standard threshold for outpatient procedures',
      recommendation: 'Verify medical necessity documentation and consider cost-effectiveness',
      detectedAt: '2025-08-17T10:35:00Z',
      source: 'policy_engine',
    },
    {
      id: 'RF-002',
      type: 'clinical',
      severity: 'low',
      title: 'Alternative Treatment Options',
      description: 'Consider if additional medical therapy was attempted before intervention',
      recommendation: 'Review medication history and optimization efforts',
      detectedAt: '2025-08-17T10:35:00Z',
      source: 'ai_analysis',
    },
  ],
  
  // Quality Indicators
  qualityIndicators: [
    {
      id: 'QI-001',
      metric: 'Provider Performance',
      value: 94,
      benchmark: 85,
      status: 'exceeds',
      trend: 'improving',
      description: 'Provider has excellent outcomes for cardiac interventions',
    },
    {
      id: 'QI-002',
      metric: 'Facility Accreditation',
      value: 100,
      benchmark: 90,
      status: 'exceeds',
      trend: 'stable',
      description: 'JCI accredited facility with cardiac specialization',
    },
  ],
  
  urgency: 'urgent',
  reviewDeadline: '2025-08-18T16:00:00Z',
  communications: [],
  relatedRequests: [],
  patientHistory: [],
};

// Mock dossier data
const mockDossierData = {
  clinicalSummary: {
    diagnosis: 'Coronary Artery Disease with significant left anterior descending (LAD) stenosis',
    symptoms: 'Progressive chest pain on exertion, shortness of breath, reduced exercise tolerance',
    riskFactors: 'Hypertension, family history of CAD, age 39',
    priorTreatments: 'Optimal medical therapy including dual antiplatelet therapy, statin, ACE inhibitor',
    clinicalFindings: 'Cardiac catheterization shows 80% stenosis in LAD, EF 55%, no other significant disease',
  },
  policyEvaluation: {
    criteria: [
      {
        description: 'Documented coronary stenosis >70%',
        status: 'met',
        evidence: 'Cardiac catheterization report shows 80% LAD stenosis',
        score: 100,
      },
      {
        description: 'Symptomatic despite optimal medical therapy',
        status: 'met',
        evidence: 'Patient reports persistent chest pain despite 3 months of guideline-directed therapy',
        score: 95,
      },
      {
        description: 'Appropriate candidate for intervention',
        status: 'met',
        evidence: 'No contraindications, good surgical risk',
        score: 100,
      },
    ],
    overallScore: 92,
    recommendation: 'Approval recommended based on clinical guidelines',
  },
  costAnalysis: {
    requestedAmount: 45000,
    benchmarkCost: 42000,
    variance: 7.1,
    justification: 'Cost within acceptable range for complex PCI with drug-eluting stent',
  },
  evidenceBase: [
    {
      source: 'AHA/ACC Guidelines 2021',
      relevance: 95,
      citation: 'Class I recommendation for PCI in stable CAD with significant stenosis and symptoms',
    },
    {
      source: 'ESC Guidelines 2019',
      relevance: 90,
      citation: 'PCI recommended for proximal LAD lesions with symptoms',
    },
  ],
};

interface RequestReviewInterfaceProps {
  requestId: string;
  onDecisionSubmit: (decision: MedicalDirectorDecision) => Promise<void>;
  isSubmitting?: boolean;
}

export const RequestReviewInterface: React.FC<RequestReviewInterfaceProps> = ({
  requestId,
  onDecisionSubmit,
  isSubmitting = false,
}) => {
  const [request, setRequest] = useState<InsurerRequest | null>(null);
  const [dossierData, setDossierData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showDecisionWorkflow, setShowDecisionWorkflow] = useState(false);

  useEffect(() => {
    const loadRequestData = async () => {
      setIsLoading(true);
      try {
        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 500));
        setRequest(mockRequestData);
        setDossierData(mockDossierData);
      } catch (error) {
        console.error('Failed to load request data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadRequestData();
  }, [requestId]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FileText },
    { id: 'clinical', label: 'Clinical Summary', icon: Stethoscope },
    { id: 'ai-analysis', label: 'AI Analysis', icon: Brain },
    { id: 'policy', label: 'Policy Review', icon: Shield },
    { id: 'dossier', label: 'Professional Dossier', icon: Star },
  ];

  const getRiskColor = (severity: RiskFlag['severity']): string => {
    switch (severity) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-orange-600 bg-orange-50';
      case 'low': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getQualityStatus = (status: QualityIndicator['status']): string => {
    switch (status) {
      case 'exceeds': return 'text-green-600 bg-green-100';
      case 'meets': return 'text-blue-600 bg-blue-100';
      case 'below': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    );
  }

  if (!request) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
            Request Not Found
          </h3>
          <p className="text-gray-600 dark:text-dark-text-secondary">
            Unable to load request details.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Request Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
                {request.requestNumber}
              </h2>
              <p className="text-gray-600 dark:text-dark-text-secondary">
                {request.procedure} • {request.memberName}
              </p>
              <div className="flex items-center space-x-4 mt-2 text-sm">
                <span className="text-gray-500">Submitted: {new Date(request.submissionDate).toLocaleDateString()}</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  request.urgency === 'critical' ? 'bg-red-100 text-red-800' :
                  request.urgency === 'urgent' ? 'bg-orange-100 text-orange-800' :
                  request.urgency === 'emergency' ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {request.urgency.toUpperCase()}
                </span>
                <span className="text-gray-500">
                  Deadline: {new Date(request.reviewDeadline).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <Button
              variant="primary"
              onClick={() => setShowDecisionWorkflow(true)}
              disabled={isSubmitting}
            >
              Make Decision
            </Button>
          </div>
        </div>
      </Card>

      {/* AI Recommendation Banner */}
      <Card className="p-4 border-l-4 border-blue-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
                AI Recommendation: {request.aiAnalysis.recommendation.replace('_', ' ').toUpperCase()}
              </h3>
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                Confidence: {request.aiAnalysis.confidence}% • Risk Score: {request.aiAnalysis.riskScore}/100
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                Policy Compliance: {request.aiAnalysis.policyCompliance}%
              </div>
              <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                Clinical Necessity: {request.aiAnalysis.clinicalNecessity}%
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Risk Flags */}
      {request.riskFlags.length > 0 && (
        <Card className="p-4">
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-3 flex items-center">
            <Flag className="h-5 w-5 mr-2 text-red-500" />
            Risk Flags ({request.riskFlags.length})
          </h3>
          <div className="space-y-3">
            {request.riskFlags.map((flag) => (
              <div key={flag.id} className={`p-3 rounded-lg ${getRiskColor(flag.severity)}`}>
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium">{flag.title}</h4>
                    <p className="text-sm mt-1">{flag.description}</p>
                    <p className="text-xs mt-2 font-medium">Recommendation: {flag.recommendation}</p>
                  </div>
                  <span className="text-xs font-medium uppercase">{flag.severity}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Card className="overflow-hidden">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 dark:border-dark-border-primary">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <OverviewTab request={request} />
          )}
          
          {activeTab === 'clinical' && (
            <ClinicalSummaryTab clinicalData={dossierData?.clinicalSummary} />
          )}
          
          {activeTab === 'ai-analysis' && (
            <AIAnalysisTab analysis={request.aiAnalysis} reasoning={request.aiAnalysis.reasoning} />
          )}
          
          {activeTab === 'policy' && (
            <PolicyReviewTab policyData={dossierData?.policyEvaluation} />
          )}
          
          {activeTab === 'dossier' && (
            <ProfessionalDossierTab requestId={request.id} />
          )}
        </div>
      </Card>

      {/* Decision Workflow Modal */}
      {showDecisionWorkflow && (
        <DecisionWorkflow
          request={request}
          onDecisionSubmit={onDecisionSubmit}
          onClose={() => setShowDecisionWorkflow(false)}
          isSubmitting={isSubmitting}
        />
      )}
    </div>
  );
};

// Tab Components
const OverviewTab: React.FC<{ request: InsurerRequest }> = ({ request }) => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    {/* Member Information */}
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <User className="w-5 h-5 mr-2" />
        Member Information
      </h3>
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-gray-500">Name</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.memberName}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Member ID</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.memberId}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Emirates ID</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.emiratesId}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Date of Birth</label>
          <p className="text-gray-900 dark:text-dark-text-primary">
            {new Date(request.dateOfBirth).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>

    {/* Provider Information */}
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <Building className="w-5 h-5 mr-2" />
        Provider Information
      </h3>
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-gray-500">Provider</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.providerName}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Type</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.providerType}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Facility</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.facility}</p>
        </div>
      </div>
    </div>

    {/* Clinical Information */}
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <Stethoscope className="w-5 h-5 mr-2" />
        Clinical Information
      </h3>
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-gray-500">Diagnosis</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.diagnosis}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Procedure</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.procedure}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-500">Service Description</label>
          <p className="text-gray-900 dark:text-dark-text-primary">{request.serviceDescription}</p>
        </div>
      </div>
    </div>

    {/* Financial Information */}
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <DollarSign className="w-5 h-5 mr-2" />
        Financial Information
      </h3>
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-gray-500">Requested Amount</label>
          <p className="text-gray-900 dark:text-dark-text-primary text-lg font-semibold">
            {new Intl.NumberFormat('en-AE', {
              style: 'currency',
              currency: request.currency,
            }).format(request.requestedAmount)}
          </p>
        </div>
      </div>
    </div>
  </div>
);

const ClinicalSummaryTab: React.FC<{ clinicalData: any }> = ({ clinicalData }) => (
  <div className="space-y-6">
    {clinicalData && Object.entries(clinicalData).map(([key, value]) => (
      <div key={key}>
        <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2 capitalize">
          {key.replace(/([A-Z])/g, ' $1').trim()}
        </h3>
        <p className="text-gray-700 dark:text-dark-text-secondary">{value as string}</p>
      </div>
    ))}
  </div>
);

const AIAnalysisTab: React.FC<{ analysis: any; reasoning: string }> = ({ analysis, reasoning }) => (
  <div className="space-y-8">
    {/* Key Metrics */}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
      <Card className="p-4 border-l-4 border-blue-500">
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600 mb-1">{analysis.confidence}%</div>
          <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">AI Confidence</div>
          <div className="text-xs text-gray-500 mt-1">Model certainty in recommendation</div>
        </div>
      </Card>
      <Card className="p-4 border-l-4 border-green-500">
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600 mb-1">{analysis.policyCompliance}%</div>
          <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Policy Compliance</div>
          <div className="text-xs text-gray-500 mt-1">Adherence to coverage criteria</div>
        </div>
      </Card>
      <Card className="p-4 border-l-4 border-orange-500">
        <div className="text-center">
          <div className="text-3xl font-bold text-orange-600 mb-1">{analysis.riskScore}/100</div>
          <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Risk Assessment</div>
          <div className="text-xs text-gray-500 mt-1">Clinical and financial risk</div>
        </div>
      </Card>
      <Card className="p-4 border-l-4 border-purple-500">
        <div className="text-center">
          <div className="text-3xl font-bold text-purple-600 mb-1">{analysis.clinicalNecessity}%</div>
          <div className="text-sm font-medium text-gray-600 dark:text-dark-text-secondary">Clinical Necessity</div>
          <div className="text-xs text-gray-500 mt-1">Medical appropriateness score</div>
        </div>
      </Card>
    </div>

    {/* AI Recommendation Summary */}
    <Card className="p-6 border-l-4 border-blue-600">
      <div className="flex items-start space-x-4">
        <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
          <Brain className="h-8 w-8 text-blue-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary mb-2">
            AI Recommendation: {analysis.recommendation.toUpperCase()}
          </h3>
          <p className="text-gray-700 dark:text-dark-text-secondary text-base">
            Based on comprehensive analysis of clinical data, policy criteria, and evidence-based guidelines, 
            the AI system recommends <strong>{analysis.recommendation}</strong> with {analysis.confidence}% confidence.
          </p>
        </div>
      </div>
    </Card>

    {/* Detailed Clinical Analysis */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
          <Stethoscope className="h-5 w-5 mr-2 text-green-600" />
          Clinical Decision Factors
        </h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 dark:text-dark-text-primary">Documented Coronary Stenosis</p>
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">80% LAD stenosis confirmed via cardiac catheterization</p>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                Meets Criteria • 95% Match
              </span>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 dark:text-dark-text-primary">Symptomatic Angina</p>
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">Progressive chest pain despite optimal medical therapy</p>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                Confirmed • 90% Match
              </span>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 dark:text-dark-text-primary">Intervention Candidacy</p>
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">Appropriate candidate with no contraindications</p>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                Verified • 100% Match
              </span>
            </div>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
          <Shield className="h-5 w-5 mr-2 text-blue-600" />
          Policy Analysis
        </h3>
        <div className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-dark-text-secondary">Coverage Criteria Match</span>
              <span className="text-lg font-bold text-blue-600">{analysis.policyCompliance}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{width: `${analysis.policyCompliance}%`}}></div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-dark-text-secondary">Prior Authorization Requirements</span>
              <span className="text-green-600 font-medium">✓ Satisfied</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-dark-text-secondary">Medical Necessity Criteria</span>
              <span className="text-green-600 font-medium">✓ Met</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-dark-text-secondary">Provider Network Status</span>
              <span className="text-green-600 font-medium">✓ In-Network</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-dark-text-secondary">Cost-Effectiveness</span>
              <span className="text-green-600 font-medium">✓ Appropriate</span>
            </div>
          </div>
        </div>
      </Card>
    </div>

    {/* Evidence-Based Reasoning */}
    <Card className="p-6">
      <h3 className="text-lg font-bold text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <Activity className="h-5 w-5 mr-2 text-purple-600" />
        Evidence-Based Clinical Reasoning
      </h3>
      <div className="bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 p-6 rounded-lg border-l-4 border-purple-500">
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-dark-text-primary mb-2">🔍 Clinical Assessment</h4>
              <p className="text-gray-700 dark:text-dark-text-secondary leading-relaxed">
                Patient presents with documented coronary artery disease affecting the left anterior descending (LAD) artery 
                with 80% stenosis confirmed via cardiac catheterization. The clinical presentation includes progressive 
                exertional chest pain and reduced exercise tolerance despite 3 months of optimal medical therapy.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-dark-text-primary mb-2">📋 Guideline Compliance</h4>
              <p className="text-gray-700 dark:text-dark-text-secondary leading-relaxed">
                This case aligns with AHA/ACC 2021 Guidelines (Class I recommendation) and ESC 2019 Guidelines 
                for percutaneous coronary intervention in stable coronary artery disease with significant stenosis 
                (&gt;70%) and persistent symptoms despite optimal medical therapy.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-dark-text-primary mb-2">⚖️ Risk-Benefit Analysis</h4>
              <p className="text-gray-700 dark:text-dark-text-secondary leading-relaxed">
                The intervention risk is low given the patient's age (39), preserved ejection fraction (55%), 
                and absence of contraindications. The potential benefit includes symptom relief, improved quality 
                of life, and prevention of future cardiac events.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-dark-text-primary mb-2">💰 Cost-Effectiveness</h4>
              <p className="text-gray-700 dark:text-dark-text-secondary leading-relaxed">
                The requested cost of AED 45,000 falls within the benchmark range (AED 42,000 ± 10%) for complex 
                PCI with drug-eluting stent placement. This represents appropriate resource utilization given the 
                clinical circumstances and expected outcomes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Card>

    {/* Technical AI Analysis Details */}
    <Card className="p-6">
      <h3 className="text-lg font-bold text-gray-900 dark:text-dark-text-primary mb-4 flex items-center">
        <Brain className="h-5 w-5 mr-2 text-indigo-600" />
        AI Model Technical Analysis
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-dark-text-primary mb-3">Model Performance Metrics</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-dark-text-secondary">Prediction Accuracy</span>
              <span className="font-medium text-green-600">94.7%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-dark-text-secondary">Feature Importance Score</span>
              <span className="font-medium text-blue-600">0.87</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-dark-text-secondary">Bias Detection</span>
              <span className="font-medium text-green-600">Low Risk</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-dark-text-secondary">Model Version</span>
              <span className="font-medium text-gray-700 dark:text-dark-text-primary">v2.3.1</span>
            </div>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-gray-900 dark:text-dark-text-primary mb-3">Decision Factors Weighting</h4>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-dark-text-secondary">Clinical Evidence</span>
                <span className="font-medium">40%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{width: '40%'}}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-dark-text-secondary">Policy Compliance</span>
                <span className="font-medium">30%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{width: '30%'}}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-dark-text-secondary">Cost Analysis</span>
                <span className="font-medium">20%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{width: '20%'}}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-dark-text-secondary">Risk Assessment</span>
                <span className="font-medium">10%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-orange-600 h-2 rounded-full" style={{width: '10%'}}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
);

const PolicyReviewTab: React.FC<{ policyData: any }> = ({ policyData }) => (
  <div className="space-y-6">
    {policyData?.criteria && (
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-4">Policy Criteria</h3>
        <div className="space-y-3">
          {policyData.criteria.map((criterion: any, index: number) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-dark-bg-tertiary rounded-lg">
              {criterion.status === 'met' ? (
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-dark-text-primary">{criterion.description}</p>
                <p className="text-sm text-gray-600 dark:text-dark-text-secondary mt-1">{criterion.evidence}</p>
                <div className="mt-2">
                  <span className="text-xs font-medium text-blue-600">Score: {criterion.score}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <h4 className="font-medium text-blue-900 dark:text-blue-300">Overall Assessment</h4>
          <p className="text-sm text-blue-800 dark:text-blue-200 mt-1">
            Score: {policyData.overallScore}% • {policyData.recommendation}
          </p>
        </div>
      </div>
    )}
  </div>
);

const ProfessionalDossierTab: React.FC<{ requestId: string }> = ({ requestId }) => (
  <div className="space-y-6">
    <div className="text-center">
      <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-lg">
        <Star className="w-5 h-5 mr-2" />
        Professional Medical Dossier
      </div>
    </div>
    
    <div className="text-center space-y-4">
      <p className="text-gray-600 dark:text-dark-text-secondary">
        Generate and view the complete professional dossier with clinical evidence, 
        policy evaluation, and recommendations.
      </p>
      
      <div className="flex justify-center space-x-3">
        <Button
          variant="primary"
          onClick={() => window.open(`/api/dossier/${requestId}`, '_blank')}
        >
          <Eye className="w-4 h-4 mr-2" />
          View Dossier
        </Button>
        <Button
          variant="secondary"
          onClick={() => window.open(`/api/dossier/${requestId}?format=pdf`, '_blank')}
        >
          <Download className="w-4 h-4 mr-2" />
          Download PDF
        </Button>
      </div>
    </div>
  </div>
);

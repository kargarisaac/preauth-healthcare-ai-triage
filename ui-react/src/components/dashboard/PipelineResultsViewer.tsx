import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import {
  X,
  Maximize2,
  Minimize2,
  Download,
  Copy,
  Search,
  FileText,
  Stethoscope,
  Brain,
  ClipboardList,
  Gavel,
  FileType,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  DollarSign,
  Target,
  TrendingUp,
  Users,
  Link,
  ExternalLink
} from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook';
import type { PipelineProcessResponse } from '@/types/api';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

interface PipelineResultsViewerProps {
  isOpen: boolean;
  onClose: () => void;
  results: PipelineProcessResponse;
}

type TabType = 'overview' | 'intake' | 'clinical' | 'evidence' | 'checklist' | 'decision' | 'metadata';

interface Tab {
  id: TabType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const tabs: Tab[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: TrendingUp,
    description: 'Pipeline summary and key metrics'
  },
  {
    id: 'intake',
    label: 'Data Intake',
    icon: FileText,
    description: 'Parsed patient and clinical data'
  },
  {
    id: 'clinical',
    label: 'Clinical Summary',
    icon: Stethoscope,
    description: 'Medical analysis and FHIR resources'
  },
  {
    id: 'evidence',
    label: 'Evidence',
    icon: Brain,
    description: 'Clinical guidelines and policy references'
  },
  {
    id: 'checklist',
    label: 'Policy Checklist',
    icon: ClipboardList,
    description: 'Criteria evaluation and compliance'
  },
  {
    id: 'decision',
    label: 'Decision',
    icon: Gavel,
    description: 'Authorization outcome and rationale'
  },
  {
    id: 'metadata',
    label: 'Metadata',
    icon: Clock,
    description: 'Processing details and performance'
  }
];

const PipelineResultsViewer: React.FC<PipelineResultsViewerProps> = ({
  isOpen,
  onClose,
  results
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Keyboard shortcuts
  useHotkeys('escape', onClose, { enabled: isOpen });
  useHotkeys('f11', () => setIsFullscreen(!isFullscreen), { enabled: isOpen });

  // Tab navigation
  useHotkeys('1', () => setActiveTab('overview'), { enabled: isOpen });
  useHotkeys('2', () => setActiveTab('intake'), { enabled: isOpen });
  useHotkeys('3', () => setActiveTab('clinical'), { enabled: isOpen });
  useHotkeys('4', () => setActiveTab('evidence'), { enabled: isOpen });
  useHotkeys('5', () => setActiveTab('checklist'), { enabled: isOpen });
  useHotkeys('6', () => setActiveTab('decision'), { enabled: isOpen });
  useHotkeys('7', () => setActiveTab('metadata'), { enabled: isOpen });

  const handleCopyResults = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(results, null, 2));
    } catch (error) {
      console.error('Failed to copy results:', error);
    }
  }, [results]);

  const getDecisionBadgeColor = (outcome: string) => {
    switch (outcome) {
      case 'APPROVE': return 'bg-green-100 text-green-800 border-green-200';
      case 'DENY': return 'bg-red-100 text-red-800 border-red-200';
      case 'REVIEW': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'met': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'unmet': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'uncertain': return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-600" />;
    }
  };

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Pipeline Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <Gavel className="w-8 h-8 text-blue-600" />
            <div className={clsx(
              'px-2 py-1 rounded-full text-xs font-medium border',
              getDecisionBadgeColor(results.decision.outcome)
            )}>
              {results.decision.outcome}
            </div>
          </div>
          <p className="text-sm font-medium text-gray-600">Authorization Decision</p>
          <p className="text-lg font-bold text-gray-900">
            {(results.decision.confidence * 100).toFixed(1)}% Confidence
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-sm font-medium text-gray-600">Processing Time</p>
          <p className="text-lg font-bold text-gray-900">
            {results.metadata.processing_time_seconds.toFixed(2)}s
          </p>
          <p className="text-xs text-gray-500">Mode: {results.metadata.mode}</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-purple-600" />
          </div>
          <p className="text-sm font-medium text-gray-600">Processing Cost</p>
          <p className="text-lg font-bold text-gray-900">
            ${results.metadata.cost_usd.toFixed(3)}
          </p>
          <p className="text-xs text-gray-500">
            {results.metadata.token_usage?.total_tokens || 0} tokens
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-8 h-8 text-orange-600" />
          </div>
          <p className="text-sm font-medium text-gray-600">Policy Compliance</p>
          <p className="text-lg font-bold text-gray-900">
            {(results.checklist.compliance_score * 100).toFixed(0)}%
          </p>
          <p className="text-xs text-gray-500">{results.checklist.policy_name}</p>
        </Card>
      </div>

      {/* Decision Summary */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Summary</h3>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-800">{results.decision.rationale}</p>
            </div>
            {results.decision.recommendations && results.decision.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Recommendations:</h4>
                <ul className="space-y-1">
                  {results.decision.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-gray-700 flex items-start">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Phase Timings */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Phase Performance</h3>
          <div className="space-y-3">
            {Object.entries(results.metadata.phase_timings || {}).map(([phase, timing]) => (
              <div key={phase} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {phase.replace('_', ' ')}
                </span>
                <span className="text-sm text-gray-900">{(timing as number).toFixed(3)}s</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );

  const IntakeTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Patient Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Patient ID</p>
              <p className="text-gray-900">{results.intake.patient_id}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Analysis ID</p>
              <p className="text-gray-900">{results.analysis_id}</p>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Canonical Data</h3>
          <div className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
            <pre className="text-sm">
              {JSON.stringify(results.intake.canonical_data, null, 2)}
            </pre>
          </div>
        </div>
      </Card>
    </div>
  );

  const ClinicalTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Clinical Summary</h3>
          <div className="prose max-w-none">
            <p className="text-gray-800">{results.clinical_summary.summary_text}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">FHIR Bundle</h3>
          <div className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
            <pre className="text-sm">
              {JSON.stringify(results.clinical_summary.fhir_bundle, null, 2)}
            </pre>
          </div>
        </div>
      </Card>
    </div>
  );

  const EvidenceTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Clinical Guidelines</h3>
          <div className="space-y-3">
            {results.evidence.clinical_guidelines.map((guideline, index) => (
              <div key={index} className="p-3 border border-gray-200 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-1">
                  {guideline.title || `Guideline ${index + 1}`}
                </h4>
                <p className="text-sm text-gray-600 mb-2">
                  {guideline.description || guideline.content}
                </p>
                {guideline.url && (
                  <a
                    href={guideline.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 text-sm flex items-center"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    View Source
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Citations</h3>
          <div className="space-y-2">
            {results.evidence.citations.map((citation, index) => (
              <div key={index} className="flex items-start space-x-2 text-sm">
                <span className="text-gray-500 font-mono">[{index + 1}]</span>
                <span className="text-gray-800">{citation.text || citation.reference}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );

  const ChecklistTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Policy Evaluation</h3>
            <div className="text-right">
              <p className="text-sm text-gray-600">Compliance Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {(results.checklist.compliance_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-4">Policy: {results.checklist.policy_name}</p>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Criteria Assessment</h3>
          <div className="space-y-3">
            {results.checklist.criteria.map((criterion, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900 flex-1 mr-3">
                    {criterion.criterion}
                  </h4>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(criterion.status)}
                    <span className={clsx(
                      'text-xs font-medium px-2 py-1 rounded',
                      criterion.status === 'met' ? 'bg-green-100 text-green-800' :
                      criterion.status === 'unmet' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    )}>
                      {criterion.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{criterion.rationale}</p>
                {criterion.evidence && (
                  <p className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                    Evidence: {criterion.evidence}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );

  const DecisionTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Authorization Decision</h3>
            <div className={clsx(
              'px-4 py-2 rounded-full text-lg font-bold border',
              getDecisionBadgeColor(results.decision.outcome)
            )}>
              {results.decision.outcome}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Confidence Level</p>
              <p className="text-xl font-bold text-gray-900">
                {(results.decision.confidence * 100).toFixed(1)}%
              </p>
            </div>
            {results.decision.cost_impact && (
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Cost Impact</p>
                <p className="text-xl font-bold text-gray-900">
                  ${results.decision.cost_impact.toLocaleString()}
                </p>
              </div>
            )}
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Rationale</h4>
            <p className="text-gray-800">{results.decision.rationale}</p>
          </div>
        </div>
      </Card>
    </div>
  );

  const MetadataTab = () => (
    <div className="space-y-6">
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Metadata</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Processing Mode</p>
              <p className="text-gray-900 capitalize">{results.metadata.mode}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Total Time</p>
              <p className="text-gray-900">{results.metadata.processing_time_seconds.toFixed(3)}s</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Cost (USD)</p>
              <p className="text-gray-900">${results.metadata.cost_usd.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Analysis ID</p>
              <p className="text-gray-900">{results.analysis_id}</p>
            </div>
          </div>
        </div>
      </Card>

      {results.metadata.token_usage && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Token Usage</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="text-sm">
                {JSON.stringify(results.metadata.token_usage, null, 2)}
              </pre>
            </div>
          </div>
        </Card>
      )}
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview': return <OverviewTab />;
      case 'intake': return <IntakeTab />;
      case 'clinical': return <ClinicalTab />;
      case 'evidence': return <EvidenceTab />;
      case 'checklist': return <ChecklistTab />;
      case 'decision': return <DecisionTab />;
      case 'metadata': return <MetadataTab />;
      default: return <OverviewTab />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div
        className={clsx(
          'bg-white rounded-lg shadow-2xl flex flex-col',
          isFullscreen
            ? 'w-full h-full rounded-none'
            : 'w-full max-w-7xl h-[90vh] mx-4'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Pipeline Results
            </h2>
            <span className="text-sm text-gray-500 bg-gray-200 px-2 py-1 rounded">
              {results.analysis_id}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="tertiary"
              size="sm"
              onClick={handleCopyResults}
              title="Copy Results"
            >
              <Copy className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title="Toggle Fullscreen"
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={onClose}
              title="Close"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center space-x-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                'hover:text-blue-600 hover:border-blue-300',
                activeTab === tab.id
                  ? 'text-blue-600 border-blue-500 bg-blue-50'
                  : 'text-gray-500 border-transparent'
              )}
              title={`${tab.description} (${index + 1})`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto p-6">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineResultsViewer;
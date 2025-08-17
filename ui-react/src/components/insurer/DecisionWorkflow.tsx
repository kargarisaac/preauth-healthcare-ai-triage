import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  MessageSquare,
  Send,
  X,
  AlertCircle,
  Info,
  Calendar,
  DollarSign,
  Edit,
  Save,
  Brain,
} from 'lucide-react';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import Modal from '@components/ui/Modal';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import type {
  InsurerRequest,
  MedicalDirectorDecision,
  DecisionType,
} from '@/types/insurer';

// Decision templates for common scenarios
const DECISION_TEMPLATES = {
  approve: {
    title: 'Standard Approval',
    reasoning: 'Request meets all clinical criteria and policy requirements. Medical necessity established through appropriate documentation.',
    conditions: [],
    limitations: [],
    followUpRequired: false,
  },
  approve_with_conditions: {
    title: 'Conditional Approval',
    reasoning: 'Request approved with specific conditions to ensure optimal outcomes and cost-effectiveness.',
    conditions: ['Pre-authorization valid for 30 days', 'Must be performed by certified provider'],
    limitations: ['Limited to specified procedure codes'],
    followUpRequired: true,
  },
  deny: {
    title: 'Standard Denial',
    reasoning: 'Request does not meet clinical criteria for medical necessity. Alternative treatments should be considered.',
    conditions: [],
    limitations: [],
    followUpRequired: false,
  },
  request_more_info: {
    title: 'Request Additional Information',
    reasoning: 'Insufficient documentation to make determination. Additional clinical information required.',
    conditions: [],
    limitations: [],
    followUpRequired: true,
  },
  partial_approve: {
    title: 'Partial Approval',
    reasoning: 'Partial approval for modified scope of services based on clinical necessity.',
    conditions: ['Approved for reduced scope'],
    limitations: ['Amount limited to essential components'],
    followUpRequired: true,
  },
};

// Communication templates
const COMMUNICATION_TEMPLATES = {
  approval: {
    subject: 'Pre-Authorization Approved - {requestNumber}',
    message: 'Your pre-authorization request has been approved. Please review the attached authorization details and any applicable conditions.',
  },
  denial: {
    subject: 'Pre-Authorization Denied - {requestNumber}',
    message: 'Your pre-authorization request has been denied. Please review the detailed reasoning and consider alternative treatment options. Appeal rights information is attached.',
  },
  more_info: {
    subject: 'Additional Information Required - {requestNumber}',
    message: 'Additional clinical documentation is required to complete the review of your pre-authorization request. Please provide the requested information within 14 days.',
  },
};

interface DecisionWorkflowProps {
  request: InsurerRequest;
  onDecisionSubmit: (decision: MedicalDirectorDecision) => Promise<void>;
  onClose: () => void;
  isSubmitting?: boolean;
}

export const DecisionWorkflow: React.FC<DecisionWorkflowProps> = ({
  request,
  onDecisionSubmit,
  onClose,
  isSubmitting = false,
}) => {
  const [currentStep, setCurrentStep] = useState<'decision' | 'details' | 'communication' | 'review'>('decision');
  const [selectedDecision, setSelectedDecision] = useState<DecisionType | null>(null);
  const [decisionData, setDecisionData] = useState<Partial<MedicalDirectorDecision>>({
    reasoning: '',
    conditions: [],
    limitations: [],
    followUpRequired: false,
    overrideAI: false,
    overrideReason: '',
    appealable: true,
  });
  const [communicationData, setCommunicationData] = useState({
    subject: '',
    message: '',
    sendToProvider: true,
    sendToMember: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Auto-populate based on AI recommendation
  useEffect(() => {
    if (request.aiAnalysis.recommendation) {
      const template = DECISION_TEMPLATES[request.aiAnalysis.recommendation as keyof typeof DECISION_TEMPLATES];
      if (template) {
        setDecisionData(prev => ({
          ...prev,
          reasoning: template.reasoning,
          conditions: [...template.conditions],
          limitations: [...template.limitations],
          followUpRequired: template.followUpRequired,
        }));
      }
    }
  }, [request.aiAnalysis.recommendation]);

  // Update communication template when decision changes
  useEffect(() => {
    if (selectedDecision) {
      const templateKey = selectedDecision === 'approve' ? 'approval' :
                         selectedDecision === 'deny' ? 'denial' : 'more_info';
      const template = COMMUNICATION_TEMPLATES[templateKey];
      
      setCommunicationData(prev => ({
        ...prev,
        subject: template.subject.replace('{requestNumber}', request.requestNumber),
        message: template.message,
      }));
    }
  }, [selectedDecision, request.requestNumber]);

  const validateStep = (step: string): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 'decision':
        if (!selectedDecision) {
          newErrors.decision = 'Please select a decision';
        }
        break;
        
      case 'details':
        if (!decisionData.reasoning?.trim()) {
          newErrors.reasoning = 'Reasoning is required';
        }
        if (decisionData.overrideAI && !decisionData.overrideReason?.trim()) {
          newErrors.overrideReason = 'Override reason is required when disagreeing with AI';
        }
        break;
        
      case 'communication':
        if (!communicationData.subject?.trim()) {
          newErrors.subject = 'Subject is required';
        }
        if (!communicationData.message?.trim()) {
          newErrors.message = 'Message is required';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleStepForward = () => {
    if (!validateStep(currentStep)) return;

    const steps = ['decision', 'details', 'communication', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex < steps.length - 1) {
      setCurrentStep(steps[currentIndex + 1] as any);
    }
  };

  const handleStepBack = () => {
    const steps = ['decision', 'details', 'communication', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(steps[currentIndex - 1] as any);
    }
  };

  const handleSubmitDecision = async () => {
    if (!validateStep('review') || !selectedDecision) return;

    const decision: MedicalDirectorDecision = {
      id: `DEC-${Date.now()}`,
      requestId: request.id,
      decision: selectedDecision,
      reasoning: decisionData.reasoning!,
      conditions: decisionData.conditions || [],
      limitations: decisionData.limitations || [],
      followUpRequired: decisionData.followUpRequired || false,
      followUpInstructions: decisionData.followUpInstructions,
      overrideAI: selectedDecision !== request.aiAnalysis.recommendation,
      overrideReason: decisionData.overrideReason,
      reviewedBy: 'Dr. Ahmed Al-Mansouri',
      reviewDate: new Date().toISOString(),
      effectiveDate: new Date().toISOString(),
      expirationDate: selectedDecision === 'approve' ? 
        new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() : undefined,
      appealable: decisionData.appealable || false,
    };

    try {
      await onDecisionSubmit(decision);
      onClose();
    } catch (error) {
      console.error('Failed to submit decision:', error);
    }
  };

  const addCondition = () => {
    setDecisionData(prev => ({
      ...prev,
      conditions: [...(prev.conditions || []), '']
    }));
  };

  const updateCondition = (index: number, value: string) => {
    setDecisionData(prev => ({
      ...prev,
      conditions: (prev.conditions || []).map((cond, i) => i === index ? value : cond)
    }));
  };

  const removeCondition = (index: number) => {
    setDecisionData(prev => ({
      ...prev,
      conditions: (prev.conditions || []).filter((_, i) => i !== index)
    }));
  };

  const getStepStatus = (step: string) => {
    const steps = ['decision', 'details', 'communication', 'review'];
    const currentIndex = steps.indexOf(currentStep);
    const stepIndex = steps.indexOf(step);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'upcoming';
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="" size="xl">
      <div className="max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-border-primary">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
              Make Decision: {request.requestNumber}
            </h2>
            <p className="text-sm text-gray-600 dark:text-dark-text-secondary mt-1">
              {request.procedure} • {request.memberName}
            </p>
          </div>
          <Button variant="tertiary" onClick={onClose} className="p-2">
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Step Indicator */}
        <div className="p-6 border-b border-gray-200 dark:border-dark-border-primary">
          <nav aria-label="Progress">
            <ol className="flex items-center justify-between">
              {[
                { id: 'decision', name: 'Decision Type', icon: CheckCircle },
                { id: 'details', name: 'Details & Reasoning', icon: FileText },
                { id: 'communication', name: 'Communication', icon: MessageSquare },
                { id: 'review', name: 'Review & Submit', icon: Send },
              ].map((step, stepIdx) => {
                const status = getStepStatus(step.id);
                const Icon = step.icon;
                
                return (
                  <li key={step.id} className="relative flex-1">
                    {stepIdx !== 3 && (
                      <div className="absolute top-4 left-1/2 w-full h-0.5 bg-gray-200 dark:bg-dark-border-primary" />
                    )}
                    <div className="relative flex flex-col items-center group">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        status === 'completed' ? 'bg-green-600 text-white' :
                        status === 'current' ? 'bg-blue-600 text-white' :
                        'bg-gray-200 text-gray-600'
                      }`}>
                        <Icon className="w-4 h-4" />
                      </span>
                      <span className={`mt-2 text-xs font-medium ${
                        status === 'current' ? 'text-blue-600' : 'text-gray-600 dark:text-dark-text-secondary'
                      }`}>
                        {step.name}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>

        {/* Step Content */}
        <div className="p-6">
          {currentStep === 'decision' && (
            <DecisionSelectionStep
              request={request}
              selectedDecision={selectedDecision}
              onDecisionChange={setSelectedDecision}
              error={errors.decision}
            />
          )}
          
          {currentStep === 'details' && (
            <DecisionDetailsStep
              decisionType={selectedDecision!}
              decisionData={decisionData}
              onDecisionDataChange={setDecisionData}
              onAddCondition={addCondition}
              onUpdateCondition={updateCondition}
              onRemoveCondition={removeCondition}
              errors={errors}
            />
          )}
          
          {currentStep === 'communication' && (
            <CommunicationStep
              communicationData={communicationData}
              onCommunicationDataChange={setCommunicationData}
              errors={errors}
            />
          )}
          
          {currentStep === 'review' && (
            <ReviewStep
              request={request}
              selectedDecision={selectedDecision!}
              decisionData={decisionData}
              communicationData={communicationData}
            />
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-dark-border-primary">
          <Button
            variant="tertiary"
            onClick={handleStepBack}
            disabled={currentStep === 'decision'}
          >
            Back
          </Button>
          
          <div className="flex space-x-3">
            {currentStep !== 'review' ? (
              <Button
                variant="primary"
                onClick={handleStepForward}
              >
                Next
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleSubmitDecision}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Submitting...
                  </>
                ) : (
                  'Submit Decision'
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

// Step Components
const DecisionSelectionStep: React.FC<{
  request: InsurerRequest;
  selectedDecision: DecisionType | null;
  onDecisionChange: (decision: DecisionType) => void;
  error?: string;
}> = ({ request, selectedDecision, onDecisionChange, error }) => {
  const decisions = [
    {
      type: 'approve' as DecisionType,
      title: 'Approve',
      description: 'Approve the request as submitted',
      icon: CheckCircle,
      color: 'green',
      recommended: request.aiAnalysis.recommendation === 'approve',
    },
    {
      type: 'partial_approve' as DecisionType,
      title: 'Partial Approve',
      description: 'Approve with modifications or limitations',
      icon: CheckCircle,
      color: 'yellow',
      recommended: request.aiAnalysis.recommendation === 'partial_approve',
    },
    {
      type: 'request_more_info' as DecisionType,
      title: 'Request More Info',
      description: 'Request additional documentation',
      icon: AlertTriangle,
      color: 'blue',
      recommended: request.aiAnalysis.recommendation === 'request_more_info',
    },
    {
      type: 'deny' as DecisionType,
      title: 'Deny',
      description: 'Deny the request',
      icon: XCircle,
      color: 'red',
      recommended: request.aiAnalysis.recommendation === 'deny',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
          Select Decision Type
        </h3>
        <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
          Choose the appropriate decision for this pre-authorization request.
        </p>
      </div>

      {/* AI Recommendation Banner */}
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center space-x-3">
          <Brain className="h-5 w-5 text-blue-600" />
          <div>
            <h4 className="font-medium text-blue-900 dark:text-blue-300">
              AI Recommendation: {request.aiAnalysis.recommendation.replace('_', ' ').toUpperCase()}
            </h4>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Confidence: {request.aiAnalysis.confidence}% • You can choose to follow or override this recommendation
            </p>
          </div>
        </div>
      </div>

      {/* Decision Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {decisions.map((decision) => {
          const Icon = decision.icon;
          const isSelected = selectedDecision === decision.type;
          const isRecommended = decision.recommended;
          
          return (
            <button
              key={decision.type}
              onClick={() => onDecisionChange(decision.type)}
              className={`relative p-4 rounded-lg border-2 text-left transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-dark-border-primary hover:border-gray-300'
              }`}
            >
              {isRecommended && (
                <div className="absolute top-2 right-2">
                  <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
                    AI Recommended
                  </span>
                </div>
              )}
              
              <div className="flex items-start space-x-3">
                <Icon className={`w-6 h-6 mt-1 ${
                  decision.color === 'green' ? 'text-green-600' :
                  decision.color === 'yellow' ? 'text-yellow-600' :
                  decision.color === 'blue' ? 'text-blue-600' :
                  'text-red-600'
                }`} />
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-dark-text-primary">
                    {decision.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-dark-text-secondary mt-1">
                    {decision.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {error && (
        <div className="text-red-600 text-sm mt-2">{error}</div>
      )}
    </div>
  );
};

const DecisionDetailsStep: React.FC<{
  decisionType: DecisionType;
  decisionData: Partial<MedicalDirectorDecision>;
  onDecisionDataChange: (data: Partial<MedicalDirectorDecision>) => void;
  onAddCondition: () => void;
  onUpdateCondition: (index: number, value: string) => void;
  onRemoveCondition: (index: number) => void;
  errors: Record<string, string>;
}> = ({ decisionType, decisionData, onDecisionDataChange, onAddCondition, onUpdateCondition, onRemoveCondition, errors }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
        Decision Details & Reasoning
      </h3>
      <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
        Provide detailed reasoning and any conditions for your decision.
      </p>
    </div>

    {/* Reasoning */}
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
        Medical Reasoning *
      </label>
      <textarea
        value={decisionData.reasoning || ''}
        onChange={(e) => onDecisionDataChange({ ...decisionData, reasoning: e.target.value })}
        rows={4}
        className="w-full border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
        placeholder="Provide detailed medical reasoning for your decision..."
      />
      {errors.reasoning && (
        <div className="text-red-600 text-sm mt-1">{errors.reasoning}</div>
      )}
    </div>

    {/* Conditions (for approvals) */}
    {(decisionType === 'approve' || decisionType === 'partial_approve') && (
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
          Conditions & Limitations
        </label>
        <div className="space-y-2">
          {(decisionData.conditions || []).map((condition, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={condition}
                onChange={(e) => onUpdateCondition(index, e.target.value)}
                className="flex-1 border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
                placeholder="Enter condition or limitation..."
              />
              <Button
                variant="tertiary"
                size="sm"
                onClick={() => onRemoveCondition(index)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="tertiary"
            size="sm"
            onClick={onAddCondition}
          >
            Add Condition
          </Button>
        </div>
      </div>
    )}

    {/* Follow-up Required */}
    <div>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={decisionData.followUpRequired || false}
          onChange={(e) => onDecisionDataChange({ ...decisionData, followUpRequired: e.target.checked })}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
        />
        <span className="text-sm text-gray-700 dark:text-dark-text-primary">
          Follow-up required
        </span>
      </label>
    </div>

    {/* Override AI */}
    <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
      <label className="flex items-start">
        <input
          type="checkbox"
          checked={decisionData.overrideAI || false}
          onChange={(e) => onDecisionDataChange({ ...decisionData, overrideAI: e.target.checked })}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2 mt-0.5"
        />
        <div>
          <span className="text-sm font-medium text-gray-700 dark:text-dark-text-primary">
            Override AI Recommendation
          </span>
          <p className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
            Check this if your decision differs from the AI recommendation
          </p>
        </div>
      </label>
      
      {decisionData.overrideAI && (
        <div className="mt-3">
          <textarea
            value={decisionData.overrideReason || ''}
            onChange={(e) => onDecisionDataChange({ ...decisionData, overrideReason: e.target.value })}
            rows={2}
            className="w-full border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
            placeholder="Explain why you're overriding the AI recommendation..."
          />
          {errors.overrideReason && (
            <div className="text-red-600 text-sm mt-1">{errors.overrideReason}</div>
          )}
        </div>
      )}
    </div>
  </div>
);

const CommunicationStep: React.FC<{
  communicationData: any;
  onCommunicationDataChange: (data: any) => void;
  errors: Record<string, string>;
}> = ({ communicationData, onCommunicationDataChange, errors }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
        Communication Settings
      </h3>
      <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
        Configure how the decision will be communicated to relevant parties.
      </p>
    </div>

    {/* Recipients */}
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
        Send Notification To
      </label>
      <div className="space-y-2">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={communicationData.sendToProvider}
            onChange={(e) => onCommunicationDataChange({ ...communicationData, sendToProvider: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
          />
          <span className="text-sm text-gray-700 dark:text-dark-text-primary">Healthcare Provider</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={communicationData.sendToMember}
            onChange={(e) => onCommunicationDataChange({ ...communicationData, sendToMember: e.target.checked })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
          />
          <span className="text-sm text-gray-700 dark:text-dark-text-primary">Patient/Member</span>
        </label>
      </div>
    </div>

    {/* Subject */}
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
        Subject Line *
      </label>
      <input
        type="text"
        value={communicationData.subject}
        onChange={(e) => onCommunicationDataChange({ ...communicationData, subject: e.target.value })}
        className="w-full border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
        placeholder="Enter email subject..."
      />
      {errors.subject && (
        <div className="text-red-600 text-sm mt-1">{errors.subject}</div>
      )}
    </div>

    {/* Message */}
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
        Message Content *
      </label>
      <textarea
        value={communicationData.message}
        onChange={(e) => onCommunicationDataChange({ ...communicationData, message: e.target.value })}
        rows={4}
        className="w-full border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
        placeholder="Enter notification message..."
      />
      {errors.message && (
        <div className="text-red-600 text-sm mt-1">{errors.message}</div>
      )}
    </div>
  </div>
);

const ReviewStep: React.FC<{
  request: InsurerRequest;
  selectedDecision: DecisionType;
  decisionData: Partial<MedicalDirectorDecision>;
  communicationData: any;
}> = ({ request, selectedDecision, decisionData, communicationData }) => (
  <div className="space-y-6">
    <div>
      <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
        Review & Submit Decision
      </h3>
      <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
        Please review your decision before submitting. This action cannot be undone.
      </p>
    </div>

    {/* Decision Summary */}
    <Card className="p-4">
      <h4 className="font-medium text-gray-900 dark:text-dark-text-primary mb-3">Decision Summary</h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <label className="text-gray-500">Request:</label>
          <p className="font-medium">{request.requestNumber}</p>
        </div>
        <div>
          <label className="text-gray-500">Decision:</label>
          <p className="font-medium capitalize">{selectedDecision.replace('_', ' ')}</p>
        </div>
        <div>
          <label className="text-gray-500">Patient:</label>
          <p className="font-medium">{request.memberName}</p>
        </div>
        <div>
          <label className="text-gray-500">Amount:</label>
          <p className="font-medium">
            {new Intl.NumberFormat('en-AE', { style: 'currency', currency: request.currency })
              .format(request.requestedAmount)}
          </p>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border-primary">
        <label className="text-gray-500 text-sm">Reasoning:</label>
        <p className="text-sm text-gray-700 dark:text-dark-text-secondary mt-1">
          {decisionData.reasoning}
        </p>
      </div>

      {decisionData.conditions && decisionData.conditions.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border-primary">
          <label className="text-gray-500 text-sm">Conditions:</label>
          <ul className="list-disc list-inside text-sm text-gray-700 dark:text-dark-text-secondary mt-1 space-y-1">
            {decisionData.conditions.map((condition, index) => (
              <li key={index}>{condition}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>

    {/* Communication Summary */}
    <Card className="p-4">
      <h4 className="font-medium text-gray-900 dark:text-dark-text-primary mb-3">Communication Settings</h4>
      <div className="text-sm space-y-2">
        <div>
          <label className="text-gray-500">Recipients:</label>
          <p className="font-medium">
            {[communicationData.sendToProvider && 'Provider', communicationData.sendToMember && 'Member']
              .filter(Boolean).join(', ')}
          </p>
        </div>
        <div>
          <label className="text-gray-500">Subject:</label>
          <p className="font-medium">{communicationData.subject}</p>
        </div>
      </div>
    </Card>

    {/* Warning for AI Override */}
    {decisionData.overrideAI && (
      <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-orange-900 dark:text-orange-300">
              AI Recommendation Override
            </h4>
            <p className="text-sm text-orange-800 dark:text-orange-200 mt-1">
              You are overriding the AI recommendation. Please ensure your reasoning is well documented.
            </p>
          </div>
        </div>
      </div>
    )}
  </div>
);

import React from 'react';
import { clsx } from 'clsx';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Loader2, 
  Upload, 
  Database, 
  BarChart3,
  FileCheck
} from 'lucide-react';
import { usePatient } from '@/contexts/PatientContext';
import type { ProcessingStep, PatientProcessingStatus } from '@/types/api';

interface ProcessingStatusProps {
  processingStep: ProcessingStep;
  progress: number;
  status: PatientProcessingStatus;
  error?: string;
  className?: string;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  processingStep,
  progress,
  status,
  error,
  className
}) => {
  const { selectedPatient } = usePatient();

  const steps = [
    {
      id: 'upload' as ProcessingStep,
      label: 'Upload XML',
      description: 'Upload patient XML file',
      icon: Upload,
      color: 'blue'
    },
    {
      id: 'process' as ProcessingStep,
      label: 'Process Data',
      description: 'Convert XML to FHIR JSON',
      icon: Database,
      color: 'indigo'
    },
    {
      id: 'analyze' as ProcessingStep,
      label: 'Generate Analysis',
      description: 'AI-powered insights and validation',
      icon: BarChart3,
      color: 'purple'
    }
  ];

  const getStepStatus = (stepId: ProcessingStep): PatientProcessingStatus => {
    const currentStepIndex = steps.findIndex(s => s.id === processingStep);
    const stepIndex = steps.findIndex(s => s.id === stepId);
    
    if (stepIndex < currentStepIndex) return 'success';
    if (stepIndex === currentStepIndex) return status;
    return 'idle';
  };

  const getStatusIcon = (stepStatus: PatientProcessingStatus) => {
    switch (stepStatus) {
      case 'loading':
        return <Loader2 className="w-5 h-5 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const getStatusColor = (stepStatus: PatientProcessingStatus, baseColor: string) => {
    switch (stepStatus) {
      case 'loading':
        return `text-${baseColor}-600 bg-${baseColor}-50 border-${baseColor}-200`;
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-400 bg-gray-50 border-gray-200';
    }
  };

  const getConnectorColor = (stepIndex: number) => {
    const stepStatus = getStepStatus(steps[stepIndex].id);
    const nextStepStatus = stepIndex < steps.length - 1 ? getStepStatus(steps[stepIndex + 1].id) : 'idle';
    
    if (stepStatus === 'success' && nextStepStatus !== 'idle') {
      return 'bg-green-400';
    } else if (stepStatus === 'success') {
      return 'bg-green-400';
    } else if (stepStatus === 'loading') {
      return 'bg-blue-400';
    }
    return 'bg-gray-300';
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Patient Info Header */}
      {selectedPatient && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <FileCheck className="w-5 h-5 text-blue-600" />
            <div>
              <h3 className="text-sm font-medium text-blue-900">
                Processing for {selectedPatient.full_name}
              </h3>
              <p className="text-xs text-blue-700">
                Patient ID: {selectedPatient.id} • {selectedPatient.insurance_plan}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Progress Steps */}
      <div className="relative">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.id);
          const isActive = step.id === processingStep;
          const IconComponent = step.icon;

          return (
            <div key={step.id} className="relative flex items-center">
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="absolute left-6 top-12 w-0.5 h-16 -ml-px">
                  <div className={clsx('w-full h-full', getConnectorColor(index))} />
                </div>
              )}

              {/* Step Content */}
              <div className="flex items-start space-x-4 w-full pb-8">
                {/* Step Icon */}
                <div className={clsx(
                  'flex items-center justify-center w-12 h-12 rounded-full border-2',
                  getStatusColor(stepStatus, step.color)
                )}>
                  {stepStatus === 'loading' ? (
                    getStatusIcon(stepStatus)
                  ) : stepStatus === 'success' ? (
                    getStatusIcon(stepStatus)
                  ) : stepStatus === 'error' ? (
                    getStatusIcon(stepStatus)
                  ) : (
                    <IconComponent className="w-5 h-5" />
                  )}
                </div>

                {/* Step Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className={clsx(
                      'text-sm font-medium',
                      stepStatus === 'success' ? 'text-green-900' :
                      stepStatus === 'error' ? 'text-red-900' :
                      stepStatus === 'loading' ? `text-${step.color}-900` :
                      'text-gray-900'
                    )}>
                      {step.label}
                    </h4>
                    
                    {/* Progress Percentage */}
                    {isActive && stepStatus === 'loading' && (
                      <span className="text-sm text-gray-600 font-medium">
                        {progress}%
                      </span>
                    )}
                  </div>

                  <p className={clsx(
                    'text-xs mt-1',
                    stepStatus === 'success' ? 'text-green-700' :
                    stepStatus === 'error' ? 'text-red-700' :
                    stepStatus === 'loading' ? `text-${step.color}-700` :
                    'text-gray-600'
                  )}>
                    {step.description}
                  </p>

                  {/* Progress Bar for Active Step */}
                  {isActive && stepStatus === 'loading' && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className={`bg-${step.color}-600 h-1.5 rounded-full transition-all duration-300`}
                          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Success Message */}
                  {stepStatus === 'success' && (
                    <div className="mt-2 text-xs text-green-700 font-medium">
                      ✓ Completed successfully
                    </div>
                  )}

                  {/* Error Message */}
                  {stepStatus === 'error' && error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                      <strong>Error:</strong> {error}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Status */}
      <div className={clsx(
        'p-4 rounded-lg border',
        status === 'loading' ? 'bg-blue-50 border-blue-200' :
        status === 'success' ? 'bg-green-50 border-green-200' :
        status === 'error' ? 'bg-red-50 border-red-200' :
        'bg-gray-50 border-gray-200'
      )}>
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <div className="flex-1">
            <p className={clsx(
              'text-sm font-medium',
              status === 'loading' ? 'text-blue-900' :
              status === 'success' ? 'text-green-900' :
              status === 'error' ? 'text-red-900' :
              'text-gray-900'
            )}>
              {status === 'loading' ? 'Processing in progress...' :
               status === 'success' ? 'Processing completed successfully!' :
               status === 'error' ? 'Processing failed' :
               'Ready to start processing'}
            </p>
            
            {status === 'loading' && (
              <p className={clsx(
                'text-xs mt-1',
                `text-blue-700`
              )}>
                {processingStep === 'upload' ? 'Uploading and validating XML file...' :
                 processingStep === 'process' ? 'Converting XML to FHIR JSON format...' :
                 processingStep === 'analyze' ? 'Generating AI-powered insights and validation...' :
                 'Processing...'}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingStatus;
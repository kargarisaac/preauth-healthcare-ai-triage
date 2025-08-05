import React from 'react';
import Button from '@/components/ui/Button';
import { User, FileCheck } from 'lucide-react';
import type { PatientInfo } from '@/types/api';

interface FileUploadProgressProps {
  progress: number;
  fileName?: string;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  error?: string;
  onCancel?: () => void;
  onRetry?: () => void;
  estimatedTimeRemaining?: number;
  uploadSpeed?: string;
  detectedSource?: string;
  selectedPatient?: PatientInfo | null;
}

const FileUploadProgress: React.FC<FileUploadProgressProps> = ({
  progress,
  fileName,
  status,
  error,
  onCancel,
  onRetry,
  estimatedTimeRemaining,
  uploadSpeed,
  detectedSource,
  selectedPatient,
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
        return (
          <div className="animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
        );
      case 'processing':
        return (
          <div className="animate-pulse w-4 h-4 bg-primary-600 rounded-full"></div>
        );
      case 'success':
        return (
          <svg className="w-4 h-4 text-success-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4 text-error-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing...';
      case 'success':
        return 'Complete';
      case 'error':
        return 'Failed';
      default:
        return 'Ready';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return 'text-primary-600';
      case 'success':
        return 'text-success-600';
      case 'error':
        return 'text-error-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className="space-y-4">
      {/* Patient Info */}
      {selectedPatient && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-blue-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">
                {selectedPatient.full_name}
              </p>
              <p className="text-xs text-blue-700">
                {selectedPatient.id} • {selectedPatient.insurance_plan}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h4 className="text-sm font-medium text-gray-900">
              {fileName || 'File Upload'}
            </h4>
            <p className={`text-xs ${getStatusColor()}`}>
              {getStatusText()}
            </p>
            {detectedSource && (
              <p className="text-xs text-blue-600 font-medium">
                Source: {detectedSource}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {status === 'uploading' && onCancel && (
            <Button
              variant="tertiary"
              size="sm"
              onClick={onCancel}
              className="text-xs"
            >
              Cancel
            </Button>
          )}
          {status === 'error' && onRetry && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onRetry}
              className="text-xs"
            >
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{Math.round(progress)}%</span>
          {uploadSpeed && status === 'uploading' && (
            <span>{uploadSpeed}</span>
          )}
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ease-out ${
              status === 'error'
                ? 'bg-error-500'
                : status === 'success'
                ? 'bg-success-500'
                : 'bg-primary-500'
            } ${
              status === 'uploading' || status === 'processing'
                ? 'bg-gradient-to-r from-primary-500 to-primary-600 animate-pulse'
                : ''
            }`}
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          >
            {(status === 'uploading' || status === 'processing') && (
              <div className="h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
            )}
          </div>
        </div>
      </div>

      {/* Additional Info */}
      {(estimatedTimeRemaining || error) && (
        <div className="space-y-2">
          {estimatedTimeRemaining && status === 'uploading' && (
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>Estimated time remaining:</span>
              <span className="font-medium">{formatTime(estimatedTimeRemaining)}</span>
            </div>
          )}

          {error && status === 'error' && (
            <div className="p-3 bg-error-50 border border-error-200 rounded-md">
              <div className="flex items-start space-x-2">
                <svg className="w-4 h-4 text-error-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <h5 className="text-sm font-medium text-error-900">Upload Failed</h5>
                  <p className="text-sm text-error-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Success Details */}
      {status === 'success' && (
        <div className="p-3 bg-success-50 border border-success-200 rounded-md">
          <div className="flex items-center space-x-2">
            <svg className="w-4 h-4 text-success-500" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-sm font-medium text-success-900">
              File uploaded successfully
            </span>
          </div>
        </div>
      )}

      {/* Processing Stages */}
      {status === 'processing' && (
        <div className="space-y-2">
          <div className="text-xs text-gray-600 font-medium">Processing stages:</div>
          <div className="space-y-1">
            {[
              { stage: 'XML validation', completed: progress > 10 },
              { stage: 'Source detection', completed: progress > 30 },
              { stage: 'Patient linking', completed: progress > 50 },
              { stage: 'FHIR conversion', completed: progress > 70 },
              { stage: 'Generate JSON', completed: progress > 90 },
            ].map((item, index) => (
              <div key={index} className="flex items-center space-x-2 text-xs">
                <div className={`w-2 h-2 rounded-full ${
                  item.completed ? 'bg-green-500' : 'bg-gray-300'
                }`}></div>
                <span className={item.completed ? 'text-green-700' : 'text-gray-600'}>
                  {item.stage}
                </span>
                {item.completed && (
                  <FileCheck className="w-3 h-3 text-green-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadProgress;

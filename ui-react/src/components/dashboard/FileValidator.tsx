import React from 'react';
import { useFileValidation, type ValidationResult } from '@hooks/forms/useFileValidation';

interface FileValidatorProps {
  file: File;
  onValidationComplete?: (result: ValidationResult & { file: File }) => void;
  showDetails?: boolean;
  className?: string;
}

const FileValidator: React.FC<FileValidatorProps> = ({
  file,
  onValidationComplete,
  showDetails = true,
  className = '',
}) => {
  const { validateFile, getFileTypeInfo } = useFileValidation();
  
  React.useEffect(() => {
    const result = validateFile(file);
    onValidationComplete?.({ ...result, file });
  }, [file, validateFile, onValidationComplete]);

  const validationResult = validateFile(file);
  const fileInfo = getFileTypeInfo(file);

  const getValidationIcon = () => {
    if (validationResult.isValid) {
      return (
        <svg className="w-5 h-5 text-success-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      );
    } else {
      return (
        <svg className="w-5 h-5 text-error-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      );
    }
  };

  if (!showDetails) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {getValidationIcon()}
        <span className={`text-sm font-medium ${
          validationResult.isValid ? 'text-success-700' : 'text-error-700'
        }`}>
          {validationResult.isValid ? 'Valid' : 'Invalid'}
        </span>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* File Info Header */}
      <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg border">
        <div className="text-2xl">{fileInfo.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-semibold text-gray-900 truncate">
              {file.name}
            </h4>
            {getValidationIcon()}
          </div>
          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-600">
            <span>{fileInfo.typeDescription}</span>
            <span>•</span>
            <span>{fileInfo.sizeFormatted}</span>
            <span>•</span>
            <span className={`font-medium ${
              fileInfo.isHealthcareFormat ? 'text-primary-600' : 'text-gray-600'
            }`}>
              {fileInfo.isHealthcareFormat ? 'Healthcare Format' : 'Standard Format'}
            </span>
          </div>
        </div>
      </div>

      {/* Validation Status */}
      <div className={`p-4 rounded-lg border ${
        validationResult.isValid
          ? 'bg-success-50 border-success-200'
          : 'bg-error-50 border-error-200'
      }`}>
        <div className="flex items-center space-x-2 mb-2">
          {getValidationIcon()}
          <h5 className={`text-sm font-semibold ${
            validationResult.isValid ? 'text-success-900' : 'text-error-900'
          }`}>
            {validationResult.isValid ? 'File Validation Passed' : 'File Validation Failed'}
          </h5>
        </div>
        
        <p className={`text-sm ${
          validationResult.isValid ? 'text-success-700' : 'text-error-700'
        }`}>
          {validationResult.isValid
            ? 'Your file meets all requirements and is ready for processing.'
            : 'Your file has validation errors that need to be resolved before processing.'
          }
        </p>
      </div>

      {/* Validation Errors */}
      {validationResult.errors.length > 0 && (
        <div className="space-y-2">
          <h6 className="text-sm font-medium text-error-900">
            Validation Errors ({validationResult.errors.length})
          </h6>
          <div className="space-y-1">
            {validationResult.errors.map((error, index) => (
              <div key={index} className="flex items-start space-x-2 p-2 bg-error-50 rounded border-l-4 border-error-400">
                <svg className="w-4 h-4 text-error-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-sm text-error-700">{error}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Warnings */}
      {validationResult.warnings.length > 0 && (
        <div className="space-y-2">
          <h6 className="text-sm font-medium text-warning-900">
            Warnings ({validationResult.warnings.length})
          </h6>
          <div className="space-y-1">
            {validationResult.warnings.map((warning, index) => (
              <div key={index} className="flex items-start space-x-2 p-2 bg-warning-50 rounded border-l-4 border-warning-400">
                <svg className="w-4 h-4 text-warning-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-sm text-warning-700">{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Healthcare-specific Tips */}
      {fileInfo.isHealthcareFormat && validationResult.isValid && (
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start space-x-2">
            <svg className="w-4 h-4 text-blue-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h6 className="text-sm font-medium text-blue-900">Healthcare Processing Tips</h6>
              <ul className="text-sm text-blue-700 mt-1 space-y-1">
                <li>• Ensure patient data is properly anonymized if required</li>
                <li>• Check that medical codes follow UAE healthcare standards</li>
                <li>• Verify all required fields are present for insurance processing</li>
                {fileInfo.extension === '.xml' && (
                  <li>• XML structure will be validated against healthcare schemas</li>
                )}
                {fileInfo.extension === '.csv' && (
                  <li>• Column headers will be automatically mapped to FHIR resources</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Technical Details */}
      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 flex items-center space-x-2">
          <svg className="w-4 h-4 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span>Technical Details</span>
        </summary>
        <div className="mt-2 p-3 bg-gray-50 rounded text-xs font-mono space-y-1">
          <div><strong>Name:</strong> {file.name}</div>
          <div><strong>Size:</strong> {file.size.toLocaleString()} bytes</div>
          <div><strong>Type:</strong> {file.type || 'Unknown'}</div>
          <div><strong>Last Modified:</strong> {new Date(file.lastModified).toLocaleString()}</div>
          <div><strong>Extension:</strong> {fileInfo.extension}</div>
        </div>
      </details>
    </div>
  );
};

export default FileValidator;
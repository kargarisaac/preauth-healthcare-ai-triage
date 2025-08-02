import React from 'react';
import Card from '@components/ui/Card';

export interface FileFormat {
  id: string;
  name: string;
  description: string;
  icon: string;
  supportedExtensions: string[];
  examples: string[];
}

export const FILE_FORMATS: FileFormat[] = [
  {
    id: 'eclaim',
    name: 'eClaimLink',
    description: 'Dubai Health Authority XML format for insurance claims and pre-authorization requests',
    icon: '🏥',
    supportedExtensions: ['.xml'],
    examples: ['prior_auth_request.xml', 'claim_submission.xml'],
  },
  {
    id: 'shafafiya',
    name: 'Shafafiya',
    description: 'Abu Dhabi Department of Health XML format for healthcare data exchange',
    icon: '🏛️',
    supportedExtensions: ['.xml'],
    examples: ['shafafiya_request.xml', 'health_record.xml'],
  },
  {
    id: 'csv',
    name: 'Healthcare CSV',
    description: 'Comma-separated values format with healthcare data columns',
    icon: '📊',
    supportedExtensions: ['.csv'],
    examples: ['clinical_data.csv', 'claims_data.csv', 'patient_records.csv'],
  },
  {
    id: 'auto',
    name: 'Auto-Detect',
    description: 'Automatically detect format based on file content and structure',
    icon: '🤖',
    supportedExtensions: ['.xml', '.csv', '.json'],
    examples: ['Any supported healthcare file'],
  },
];

interface FileTypeSelectorProps {
  selectedFormat: string;
  onFormatChange: (format: string) => void;
  disabled?: boolean;
  showDescription?: boolean;
}

const FileTypeSelector: React.FC<FileTypeSelectorProps> = ({
  selectedFormat,
  onFormatChange,
  disabled = false,
  showDescription = true,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Select File Format
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Choose the format that matches your healthcare data file
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {FILE_FORMATS.map((format) => (
          <div
            key={format.id}
            className={`
              relative cursor-pointer transition-all duration-200
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md'}
              ${selectedFormat === format.id
                ? 'ring-2 ring-primary-500 shadow-md'
                : 'ring-1 ring-gray-200 hover:ring-gray-300'
              }
              rounded-lg
            `}
            onClick={() => !disabled && onFormatChange(format.id)}
          >
            <Card className="h-full p-4">
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{format.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-semibold text-gray-900">
                      {format.name}
                    </h4>
                    <div className="flex-shrink-0">
                      <input
                        type="radio"
                        name="fileFormat"
                        value={format.id}
                        checked={selectedFormat === format.id}
                        onChange={() => onFormatChange(format.id)}
                        disabled={disabled}
                        className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                      />
                    </div>
                  </div>

                  {showDescription && (
                    <p className="text-sm text-gray-600 mt-1 mb-3">
                      {format.description}
                    </p>
                  )}

                  <div className="space-y-2">
                    <div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Supported Extensions
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {format.supportedExtensions.map((ext) => (
                          <span
                            key={ext}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700"
                          >
                            {ext}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Examples
                      </span>
                      <div className="mt-1">
                        {format.examples.map((example, index) => (
                          <div key={index} className="text-xs text-gray-600">
                            • {example}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {selectedFormat === format.id && (
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedFormat && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start space-x-3">
            <div className="text-blue-500">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div>
              <h5 className="text-sm font-medium text-blue-900">
                Format Selected: {FILE_FORMATS.find(f => f.id === selectedFormat)?.name}
              </h5>
              <p className="text-sm text-blue-700 mt-1">
                {selectedFormat === 'auto'
                  ? 'The system will automatically detect the format when you upload your file.'
                  : 'Make sure your file matches this format for optimal processing results.'
                }
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileTypeSelector;

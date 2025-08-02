import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import {
  Upload,
  FileText,
  Database,
  Zap,
  CheckCircle,
  Loader2,
  X,
  Play,
  Eye
} from 'lucide-react';
import { useProcessing } from '@/contexts/ProcessingContext';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import ResultsModal from './ResultsModal';

interface FileProcessingSectionProps {
  className?: string;
}

const supportedFormats = [
  {
    id: 'auto',
    name: 'Auto-detect',
    description: 'Automatically detect format from file extension',
    extensions: ['.xml', '.csv'],
    color: 'bg-blue-50 border-blue-200 text-blue-700'
  },
  {
    id: 'eclaim',
    name: 'eClaimLink (Dubai)',
    description: 'Dubai Health Authority XML format',
    extensions: ['.xml'],
    color: 'bg-green-50 border-green-200 text-green-700'
  },
  {
    id: 'shafafiya',
    name: 'Shafafiya (Abu Dhabi)',
    description: 'Abu Dhabi Department of Health XML format',
    extensions: ['.xml'],
    color: 'bg-purple-50 border-purple-200 text-purple-700'
  },
  {
    id: 'csv',
    name: 'Healthcare CSV',
    description: 'Healthcare data in CSV format with intelligent column detection',
    extensions: ['.csv'],
    color: 'bg-orange-50 border-orange-200 text-orange-700'
  }
];

const sampleFiles = [
  {
    id: 'eclaim-sample',
    name: 'eClaimLink Sample',
    description: 'Sample Dubai pre-authorization request',
    format: 'eclaim',
    size: '15.2 KB',
    icon: FileText
  },
  {
    id: 'shafafiya-sample',
    name: 'Shafafiya Sample',
    description: 'Sample Abu Dhabi healthcare data',
    format: 'shafafiya',
    size: '22.8 KB',
    icon: FileText
  },
  {
    id: 'csv-sample',
    name: 'Healthcare CSV Sample',
    description: 'Sample healthcare claims data',
    format: 'csv',
    size: '8.9 KB',
    icon: Database
  }
];

const FileProcessingSection: React.FC<FileProcessingSectionProps> = ({ className }) => {
  const {
    currentFile,
    processingResults,
    isProcessing,
    uploadProgress,
    setCurrentFile,
    processFile,
    processSampleFile,
    clearResults
  } = useProcessing();

  const [selectedFormat, setSelectedFormat] = useState('auto');
  const [dragOver, setDragOver] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleFileSelect = useCallback((file: File) => {
    setCurrentFile(file);
  }, [setCurrentFile]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const determineFormat = useCallback((file: File): string => {
    if (selectedFormat !== 'auto') return selectedFormat;

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension === 'csv') return 'csv';
    if (extension === 'xml') {
      // Could add more logic here to detect XML type
      return 'eclaim'; // Default to eclaim for XML files
    }
    return 'eclaim'; // Default fallback
  }, [selectedFormat]);

  const handleProcess = useCallback(async () => {
    if (!currentFile) return;

    const format = determineFormat(currentFile);
    await processFile(format);
  }, [currentFile, processFile, determineFormat]);

  const handleSampleProcess = useCallback(async (format: string) => {
    await processSampleFile(format);
  }, [processSampleFile]);

  const handleViewResults = useCallback(() => {
    setShowResults(true);
  }, []);

  const handleCloseResults = useCallback(() => {
    setShowResults(false);
  }, []);

  const getFileIcon = (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    return extension === 'csv' ? Database : FileText;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Process Healthcare Data
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload your XML or CSV healthcare files for AI-powered processing into FHIR-compliant format.
          Supports eClaimLink (Dubai), Shafafiya (Abu Dhabi), and Healthcare CSV formats.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Upload */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Upload File" className="h-fit">
            <div className="space-y-4">
              {/* Drag & Drop Area */}
              <div
                className={clsx(
                  'border-2 border-dashed rounded-lg p-8 text-center transition-all',
                  dragOver
                    ? 'border-blue-400 bg-blue-50'
                    : currentFile
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                )}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                {currentFile ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center">
                      {React.createElement(getFileIcon(currentFile), {
                        className: 'w-12 h-12 text-green-600'
                      })}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{currentFile.name}</p>
                      <p className="text-sm text-gray-600">
                        {formatFileSize(currentFile.size)} • Ready to process
                      </p>
                    </div>
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={() => setCurrentFile(null)}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        Drop your file here, or
                      </p>
                      <label className="inline-block">
                        <input
                          type="file"
                          className="hidden"
                          accept=".xml,.csv"
                          onChange={handleFileInput}
                        />
                        <span className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                          browse to upload
                        </span>
                      </label>
                    </div>
                    <p className="text-sm text-gray-500">
                      Supports XML and CSV files up to 10MB
                    </p>
                  </div>
                )}
              </div>

              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Processing Format
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {supportedFormats.map((format) => (
                    <label
                      key={format.id}
                      className={clsx(
                        'flex items-center p-3 border rounded-lg cursor-pointer transition-all',
                        selectedFormat === format.id
                          ? format.color
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      )}
                    >
                      <input
                        type="radio"
                        name="format"
                        value={format.id}
                        checked={selectedFormat === format.id}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="sr-only"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-sm">{format.name}</div>
                        <div className="text-xs text-gray-600">{format.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Process Button */}
              <div className="flex space-x-3">
                <Button
                  variant="primary"
                  onClick={handleProcess}
                  disabled={!currentFile || isProcessing}
                  className="flex-1"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Process File
                    </>
                  )}
                </Button>

                {processingResults && (
                  <Button
                    variant="secondary"
                    onClick={handleViewResults}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Results
                  </Button>
                )}
              </div>

              {/* Upload Progress */}
              {isProcessing && uploadProgress > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Processing...</span>
                    <span className="text-gray-900">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Results Summary */}
              {processingResults && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-900">Processing Complete</span>
                  </div>
                  <div className="text-sm text-green-800 space-y-1">
                    <p>
                      Processed in {processingResults.metadata?.processing_time_seconds?.toFixed(2) || 0}s
                    </p>
                    <p>
                      Generated {processingResults.data?.total || 0} FHIR resources
                    </p>
                    {processingResults.data?.authorization_id && (
                      <p>Authorization ID: {processingResults.data.authorization_id}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Sample Files */}
        <div className="space-y-6">
          <Card title="Try Sample Files" className="h-fit">
            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-4">
                Test the platform with sample healthcare data files.
              </p>

              {sampleFiles.map((sample) => (
                <div
                  key={sample.id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-all"
                >
                  <div className="flex items-center space-x-3">
                    <sample.icon className="w-5 h-5 text-gray-500" />
                    <div>
                      <div className="font-medium text-sm text-gray-900">
                        {sample.name}
                      </div>
                      <div className="text-xs text-gray-600">
                        {sample.description}
                      </div>
                      <div className="text-xs text-gray-500">
                        {sample.size}
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={() => handleSampleProcess(sample.format)}
                    disabled={isProcessing}
                  >
                    <Play className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          {/* Quick Actions */}
          <Card title="Quick Actions" className="h-fit">
            <div className="space-y-3">
              <Button variant="secondary" fullWidth>
                📄 View Processing History
              </Button>
              <Button variant="secondary" fullWidth>
                📊 Data Quality Reports
              </Button>
              <Button variant="secondary" fullWidth>
                ⚙️ Processing Settings
              </Button>
              <Button variant="secondary" fullWidth onClick={clearResults}>
                🗑️ Clear Current Results
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* Results Modal */}
      <ResultsModal
        isOpen={showResults}
        onClose={handleCloseResults}
        results={processingResults}
      />
    </div>
  );
};

export default FileProcessingSection;

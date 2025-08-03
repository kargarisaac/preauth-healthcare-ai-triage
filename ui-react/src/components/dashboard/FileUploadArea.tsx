import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import { Upload, FileText, Database, Zap, CheckCircle, X, Loader2 } from 'lucide-react';
import { useProcessing } from '@/contexts/ProcessingContext';
import Button from '@/components/ui/Button';
import { LLMValidationToggle, LLMValidationResultDisplay } from './LLMValidation';

const FileUploadArea: React.FC = () => {
  const {
    currentFile,
    processingResults,
    isProcessing,
    uploadProgress,
    enableLLMValidation,
    setCurrentFile,
    setEnableLLMValidation,
    processFile
  } = useProcessing();

  const [dragOver, setDragOver] = useState(false);

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

  const handleProcess = useCallback(async () => {
    if (!currentFile) return;

    // Auto-detect format based on file extension
    const extension = currentFile.name.split('.').pop()?.toLowerCase();
    const format = extension === 'csv' ? 'csv' : 'eclaim';

    await processFile(format);
  }, [currentFile, processFile]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    return extension === 'csv' ? Database : FileText;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center transition-all cursor-pointer',
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : currentFile
            ? 'border-green-300 bg-green-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-upload')?.click()}
      >
        {currentFile ? (
          <div className="space-y-2">
            <div className="flex items-center justify-center">
              {React.createElement(getFileIcon(currentFile), {
                className: 'w-8 h-8 text-green-600'
              })}
            </div>
            <div>
              <p className="font-medium text-gray-900">{currentFile.name}</p>
              <p className="text-sm text-gray-600">
                {formatFileSize(currentFile.size)}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-8 h-8 text-gray-400 mx-auto" />
            <div>
              <p className="font-medium text-gray-900">
                Drop files here or click to upload
              </p>
              <p className="text-sm text-gray-500">
                XML or CSV files up to 10MB
              </p>
            </div>
          </div>
        )}
      </div>

      <input
        id="file-upload"
        type="file"
        className="hidden"
        accept=".xml,.csv"
        onChange={handleFileInput}
      />

      {/* LLM Validation Toggle */}
      {currentFile && (
        <div className="border-t pt-4">
          <LLMValidationToggle
            enabled={enableLLMValidation}
            onChange={setEnableLLMValidation}
            disabled={isProcessing}
          />
        </div>
      )}

      {/* Actions */}
      {currentFile && (
        <div className="flex items-center space-x-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleProcess}
            disabled={isProcessing}
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
                Process
              </>
            )}
          </Button>
          <Button
            variant="tertiary"
            size="sm"
            onClick={() => setCurrentFile(null)}
            disabled={isProcessing}
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Progress */}
      {isProcessing && uploadProgress > 0 && (
        <div className="space-y-1">
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

      {/* Results */}
      {processingResults && (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-900">
                Processed successfully in {processingResults.metadata?.processing_time_seconds?.toFixed(2) || 0}s
              </span>
            </div>
          </div>

          {/* LLM Validation Results */}
          {processingResults.metadata?.llm_validation && (
            <LLMValidationResultDisplay
              validationResult={processingResults.metadata.llm_validation}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default FileUploadArea;

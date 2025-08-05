import React, { useState, useCallback } from 'react';
import { clsx } from 'clsx';
import { Upload, FileText, Zap, CheckCircle, X, Loader2, User } from 'lucide-react';
import Button from '@/components/ui/Button';
import { LLMValidationToggle, LLMValidationResultDisplay } from './LLMValidation';
import type { PatientInfo, XMLProcessResponse } from '@/types/api';
import { useProcessing } from '@/contexts/ProcessingContext';

interface FileUploadAreaProps {
  selectedPatient: PatientInfo | null;
  onUploadComplete: (response: XMLProcessResponse) => void;
  onUploadError: (error: string) => void;
}

const FileUploadArea: React.FC<FileUploadAreaProps> = ({
  selectedPatient,
  onUploadComplete,
  onUploadError
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedSource, setSelectedSource] = useState<'eclaim' | 'shafafiya' | null>(null);
  const [enableLLMValidation, setEnableLLMValidation] = useState(false);
  
  const { 
    currentFile, 
    setCurrentFile, 
    isProcessing, 
    uploadProgress, 
    uploadFileForPatient 
  } = useProcessing();

  // Suggest source based on filename patterns (user still needs to confirm)
  const suggestSourceFromFilename = (filename: string): 'eclaim' | 'shafafiya' | null => {
    const name = filename.toLowerCase();
    if (name.includes('eclaim') || name.includes('dubai')) {
      return 'eclaim';
    } else if (name.includes('shafafiya') || name.includes('abudhabi') || name.includes('abu_dhabi')) {
      return 'shafafiya';
    }
    return null;
  };

  const handleFileSelect = useCallback(async (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xml') {
      onUploadError('Only XML files are supported for patient-specific uploads');
      return;
    }

    setCurrentFile(file);
    
    // Suggest source based on filename, but user must confirm
    const suggestedSource = suggestSourceFromFilename(file.name);
    setSelectedSource(suggestedSource);
  }, [onUploadError, setCurrentFile]);

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
    if (!currentFile || !selectedPatient || !selectedSource) return;

    try {
      const result = await uploadFileForPatient(currentFile, selectedSource, selectedPatient.patient_id);
      if (result) {
        onUploadComplete(result);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onUploadError(errorMessage);
    }
  }, [currentFile, selectedPatient, selectedSource, uploadFileForPatient, onUploadComplete, onUploadError]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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
              <FileText className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">{currentFile.name}</p>
              <p className="text-sm text-gray-600">
                {formatFileSize(currentFile.size)}
              </p>
              {selectedSource && (
                <p className="text-xs text-blue-600 font-medium">
                  Source: {selectedSource === 'eclaim' ? 'eClaimLink (Dubai)' : 'Shafafiya (Abu Dhabi)'}
                </p>
              )}
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
                XML files only (eClaimLink or Shafafiya)
              </p>
            </div>
          </div>
        )}
      </div>

      <input
        id="file-upload"
        type="file"
        className="hidden"
        accept=".xml"
        onChange={handleFileInput}
      />

      {/* Selected Patient Info */}
      {selectedPatient && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-blue-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">
                {selectedPatient.folder_name}
              </p>
              <p className="text-xs text-blue-700">
                {selectedPatient.patient_id} • {selectedPatient.xml_files} XML files • {selectedPatient.processed_json_files} processed
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Source Selection */}
      {currentFile && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              XML Source Type *
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="source"
                  value="eclaim"
                  checked={selectedSource === 'eclaim'}
                  onChange={(e) => setSelectedSource(e.target.value as 'eclaim')}
                  className="mr-2"
                  disabled={isProcessing}
                />
                <span className="text-sm">eClaimLink (Dubai Health Authority)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="source"
                  value="shafafiya"
                  checked={selectedSource === 'shafafiya'}
                  onChange={(e) => setSelectedSource(e.target.value as 'shafafiya')}
                  className="mr-2"
                  disabled={isProcessing}
                />
                <span className="text-sm">Shafafiya (Abu Dhabi Department of Health)</span>
              </label>
            </div>
            {!selectedSource && (
              <p className="text-xs text-red-600 mt-1">
                Please select the XML source type before processing
              </p>
            )}
          </div>

          {/* LLM Validation Toggle */}
          <div className="border-t pt-4">
            <LLMValidationToggle
              enabled={enableLLMValidation}
              onChange={setEnableLLMValidation}
              disabled={isProcessing}
            />
          </div>
        </div>
      )}

      {/* Actions */}
      {currentFile && (
        <div className="flex items-center space-x-2">
          <Button
            variant="primary"
            size="sm"
            onClick={handleProcess}
            disabled={isProcessing || !selectedPatient || !selectedSource}
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

      {/* Processing Stages */}
      {isProcessing && (
        <div className="space-y-2">
          <div className="text-xs text-gray-600 font-medium">Processing stages:</div>
          <div className="space-y-1">
            {[
              { stage: 'File upload', completed: uploadProgress > 10 },
              { stage: 'XML validation', completed: uploadProgress > 30 },
              { stage: 'Source detection', completed: uploadProgress > 50 },
              { stage: 'Patient linking', completed: uploadProgress > 70 },
              { stage: 'Data processing', completed: uploadProgress > 90 },
            ].map((item, index) => (
              <div key={index} className="flex items-center space-x-2 text-xs">
                <div className={`w-2 h-2 rounded-full ${
                  item.completed ? 'bg-green-500' : 'bg-gray-300'
                }`}></div>
                <span className={item.completed ? 'text-green-700' : 'text-gray-600'}>
                  {item.stage}
                </span>
                {item.completed && (
                  <CheckCircle className="w-3 h-3 text-green-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadArea;
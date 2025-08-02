import { createContext, useContext, useState, ReactNode } from 'react';
import type { ApiResponse } from '@/types/api';
import { useToast } from './ToastContext';

interface ProcessingContextValue {
  currentFile: File | null;
  processingResults: ApiResponse | null;
  isProcessing: boolean;
  uploadProgress: number;
  setCurrentFile: (file: File | null) => void;
  setProcessingResults: (results: ApiResponse | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setUploadProgress: (progress: number) => void;
  processFile: (format: string) => Promise<void>;
  processSampleFile: (format: string) => Promise<void>;
  clearResults: () => void;
}

const ProcessingContext = createContext<ProcessingContextValue | undefined>(undefined);

interface ProcessingProviderProps {
  children: ReactNode;
}

export function ProcessingProvider({ children }: ProcessingProviderProps) {
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [processingResults, setProcessingResults] = useState<ApiResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { showToast } = useToast();

  const processFile = async (format: string) => {
    if (!currentFile) {
      showToast({
        type: 'error',
        title: 'No file selected',
        message: 'Please select a file first.',
      });
      return;
    }

    setIsProcessing(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', currentFile);

      // Determine endpoint based on file type and format
      const fileExtension = currentFile.name.split('.').pop()?.toLowerCase();
      let endpoint: string;

      if (fileExtension === 'csv') {
        endpoint = '/api/process/csv';
      } else if (format === 'eclaim') {
        endpoint = '/api/process/eclaim';
      } else if (format === 'shafafiya') {
        endpoint = '/api/process/shafafiya';
      } else {
        throw new Error('Invalid format selected');
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setProcessingResults(result);

      showToast({
        type: 'success',
        title: 'Processing Complete',
        message: `File processed successfully in ${result.metadata?.processing_time_seconds || 0}s`,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      showToast({
        type: 'error',
        title: 'Processing Failed',
        message: errorMessage,
      });
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  };

  const processSampleFile = async (format: string) => {
    setIsProcessing(true);

    try {
      const endpoint = format === 'eclaim' 
        ? '/api/process/sample/eclaim' 
        : '/api/process/sample/shafafiya';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setProcessingResults(result);

      showToast({
        type: 'success',
        title: 'Sample Processed',
        message: `Sample ${format} file processed successfully`,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      showToast({
        type: 'error',
        title: 'Processing Failed',
        message: errorMessage,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const clearResults = () => {
    setProcessingResults(null);
    setCurrentFile(null);
    setUploadProgress(0);
  };

  return (
    <ProcessingContext.Provider value={{
      currentFile,
      processingResults,
      isProcessing,
      uploadProgress,
      setCurrentFile,
      setProcessingResults,
      setIsProcessing,
      setUploadProgress,
      processFile,
      processSampleFile,
      clearResults,
    }}>
      {children}
    </ProcessingContext.Provider>
  );
}

export function useProcessing() {
  const context = useContext(ProcessingContext);
  if (context === undefined) {
    throw new Error('useProcessing must be used within a ProcessingProvider');
  }
  return context;
}
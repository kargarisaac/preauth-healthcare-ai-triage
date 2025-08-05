import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { ApiResponse, ProcessingStep, PatientProcessingStatus, XMLProcessResponse, AnalysisResponse } from '@/types/api';
import { patientApi } from '@/services/apiService';
import { useToast } from './ToastContext';

interface ProcessingContextValue {
  // Original state
  currentFile: File | null;
  processingResults: ApiResponse | null;
  isProcessing: boolean;
  uploadProgress: number;
  enableLLMValidation: boolean;
  
  // Patient-specific processing state
  patientId: string | null;
  processingStep: ProcessingStep;
  processingStatus: PatientProcessingStatus;
  processingError: string | null;
  
  // Processing results
  uploadResult: XMLProcessResponse | null;
  analysisResult: AnalysisResponse | null;
  
  // Original actions
  setCurrentFile: (file: File | null) => void;
  setProcessingResults: (results: ApiResponse | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setEnableLLMValidation: (enabled: boolean) => void;
  processFile: (format: string) => Promise<void>;
  processSampleFile: (format: string) => Promise<void>;
  clearResults: () => void;
  
  // Patient-specific actions
  startProcessing: (patientId: string, step: ProcessingStep) => void;
  updateProgress: (progress: number) => void;
  completeProcessing: (step: ProcessingStep) => void;
  setProcessingError: (error: string) => void;
  resetProcessing: () => void;
  
  // New patient workflow actions
  uploadFileForPatient: (file: File, source: 'eclaim' | 'shafafiya', patientId?: string) => Promise<XMLProcessResponse | null>;
  processPatientData: (patientId: string) => Promise<XMLProcessResponse | null>;
  analyzePatient: (patientId: string) => Promise<AnalysisResponse | null>;
}

const ProcessingContext = createContext<ProcessingContextValue | undefined>(undefined);

interface ProcessingProviderProps {
  children: ReactNode;
}

export function ProcessingProvider({ children }: ProcessingProviderProps) {
  // Original state
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [processingResults, setProcessingResults] = useState<ApiResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [enableLLMValidation, setEnableLLMValidation] = useState(false);
  
  // Patient-specific processing state
  const [patientId, setPatientId] = useState<string | null>(null);
  const [processingStep, setProcessingStep] = useState<ProcessingStep>('upload');
  const [processingStatus, setProcessingStatus] = useState<PatientProcessingStatus>('idle');
  const [processingError, setProcessingError] = useState<string | null>(null);
  
  // Processing results
  const [uploadResult, setUploadResult] = useState<XMLProcessResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  
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

      // Add LLM validation parameter if enabled
      if (enableLLMValidation) {
        formData.append('enable_llm_validation', 'true');
      }

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

  // Patient-specific processing functions
  const startProcessing = (newPatientId: string, step: ProcessingStep) => {
    setPatientId(newPatientId);
    setProcessingStep(step);
    setProcessingStatus('loading');
    setProcessingError(null);
    setUploadProgress(0);
  };

  const updateProgress = (progress: number) => {
    setUploadProgress(progress);
  };

  const completeProcessing = (step: ProcessingStep) => {
    setProcessingStep(step);
    setProcessingStatus('success');
    setUploadProgress(100);
  };

  const setProcessingErrorState = (error: string) => {
    setProcessingError(error);
    setProcessingStatus('error');
  };

  const resetProcessing = useCallback(() => {
    setPatientId(null);
    setProcessingStep('upload');
    setProcessingStatus('idle');
    setProcessingError(null);
    setUploadProgress(0);
    setCurrentFile(null);
    setProcessingResults(null);
    setUploadResult(null);
    setAnalysisResult(null);
  }, []);
  
  // New patient workflow functions
  const uploadFileForPatient = useCallback(async (
    file: File,
    source: 'eclaim' | 'shafafiya',
    targetPatientId?: string
  ): Promise<XMLProcessResponse | null> => {
    try {
      setIsProcessing(true);
      setUploadProgress(0);
      setProcessingError(null);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);
      
      const response = await patientApi.uploadXml(file, source, targetPatientId);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success && response.data) {
        setUploadResult(response.data);
        setPatientId(response.data.patient_id || targetPatientId || null);
        setProcessingStep('process');
        setProcessingStatus('success');
        
        showToast({
          type: 'success',
          title: 'Upload Successful',
          message: `File uploaded successfully for patient ${response.data.patient_id}`,
        });
        
        return response.data;
      } else {
        throw new Error(response.data?.error || 'Upload failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Upload failed';
      setProcessingError(errorMessage);
      setProcessingStatus('error');
      
      showToast({
        type: 'error',
        title: 'Upload Failed',
        message: errorMessage,
      });
      
      return null;
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
    }
  }, [showToast]);
  
  const processPatientData = useCallback(async (
    targetPatientId: string
  ): Promise<XMLProcessResponse | null> => {
    try {
      setIsProcessing(true);
      setProcessingError(null);
      setProcessingStep('process');
      setProcessingStatus('loading');
      
      const response = await patientApi.processPatient(targetPatientId);
      
      if (response.success && response.data) {
        setUploadResult(response.data);
        setProcessingStep('analyze');
        setProcessingStatus('success');
        
        showToast({
          type: 'success',
          title: 'Processing Complete',
          message: `Data processed successfully for patient ${targetPatientId}`,
        });
        
        return response.data;
      } else {
        throw new Error(response.data?.error || 'Processing failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Processing failed';
      setProcessingError(errorMessage);
      setProcessingStatus('error');
      
      showToast({
        type: 'error',
        title: 'Processing Failed',
        message: errorMessage,
      });
      
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, [showToast]);
  
  const analyzePatient = useCallback(async (
    targetPatientId: string
  ): Promise<AnalysisResponse | null> => {
    try {
      setIsProcessing(true);
      setProcessingError(null);
      setProcessingStep('analyze');
      setProcessingStatus('loading');
      
      const response = await patientApi.analyzePatient(targetPatientId);
      
      if (response.success && response.data) {
        setAnalysisResult(response.data);
        setProcessingStatus('success');
        
        showToast({
          type: 'success',
          title: 'Analysis Complete',
          message: `Claude analysis completed for patient ${targetPatientId}`,
        });
        
        return response.data;
      } else {
        throw new Error(response.data?.error || 'Analysis failed');
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Analysis failed';
      setProcessingError(errorMessage);
      setProcessingStatus('error');
      
      showToast({
        type: 'error',
        title: 'Analysis Failed',
        message: errorMessage,
      });
      
      return null;
    } finally {
      setIsProcessing(false);
    }
  }, [showToast]);

  return (
    <ProcessingContext.Provider value={{
      // Original state
      currentFile,
      processingResults,
      isProcessing,
      uploadProgress,
      enableLLMValidation,
      
      // Patient-specific state
      patientId,
      processingStep,
      processingStatus,
      processingError,
      
      // Processing results
      uploadResult,
      analysisResult,
      
      // Original actions
      setCurrentFile,
      setProcessingResults,
      setIsProcessing,
      setUploadProgress,
      setEnableLLMValidation,
      processFile,
      processSampleFile,
      clearResults,
      
      // Patient-specific actions
      startProcessing,
      updateProgress,
      completeProcessing,
      setProcessingError: setProcessingErrorState,
      resetProcessing,
      
      // New patient workflow actions
      uploadFileForPatient,
      processPatientData,
      analyzePatient,
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

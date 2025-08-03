import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import {
  processFileAsync,
  setCurrentFile,
  resetProcessing,
  clearResults,
  setError,
} from '../store/slices/fileProcessingSlice';
import {
  validateWithLLMAsync,
} from '../store/slices/validationSlice';
import { showToast } from '../store/slices/notificationSlice';
import type { UploadedFile } from '../types/ui';
import type { ApiResponse } from '../types/api';

/**
 * Redux-based processing hook that provides backward compatibility
 * with the original ProcessingContext interface
 */
export function useProcessing() {
  const dispatch = useAppDispatch();
  
  // Select state from Redux store
  const currentFile = useAppSelector(state => state.fileProcessing.currentFile);
  const isProcessing = useAppSelector(state => state.fileProcessing.isProcessing);
  const uploadProgress = useAppSelector(state => state.fileProcessing.uploadProgress);
  const fhirBundle = useAppSelector(state => state.fileProcessing.fhirBundle);
  const error = useAppSelector(state => state.fileProcessing.error);
  const enableLLMValidation = useAppSelector(state => state.userPreferences.autoValidation);

  // Transform FHIR bundle to legacy ApiResponse format for backward compatibility
  const processingResults: ApiResponse | null = fhirBundle ? {
    data: fhirBundle,
    success: true,
    timestamp: Date.now(),
  } : null;

  // Action creators
  const setCurrentFileHandler = useCallback((file: File | null) => {
    if (file) {
      const uploadedFile: UploadedFile = {
        ...file,
        id: Date.now().toString(),
        status: 'idle',
        progress: 0,
      };
      dispatch(setCurrentFile(uploadedFile));
    } else {
      dispatch(setCurrentFile(null));
    }
  }, [dispatch]);

  const setProcessingResults = useCallback((results: ApiResponse | null) => {
    if (results) {
      // Transform ApiResponse back to FHIR bundle if needed
      // This is mainly for backward compatibility
      console.debug('Setting processing results:', results);
    } else {
      dispatch(clearResults());
    }
  }, [dispatch]);

  const setIsProcessing = useCallback((processing: boolean) => {
    // This is handled automatically by async thunks
    console.debug('Setting processing state:', processing);
  }, []);

  const setUploadProgress = useCallback((progress: number) => {
    // This is handled automatically by the upload process
    console.debug('Setting upload progress:', progress);
  }, []);

  const setEnableLLMValidation = useCallback((enabled: boolean) => {
    // Update user preferences
    dispatch({
      type: 'userPreferences/setAutoValidation',
      payload: enabled,
    });
  }, [dispatch]);

  const processFile = useCallback(async (format: string) => {
    if (!currentFile) {
      dispatch(showToast({
        type: 'error',
        title: 'No file selected',
        message: 'Please select a file first.',
      }));
      return;
    }

    try {
      // Convert format string to expected type
      let apiFormat: 'eclaim' | 'shafafiya' | 'csv';
      
      const fileExtension = currentFile.name.split('.').pop()?.toLowerCase();
      
      if (fileExtension === 'csv') {
        apiFormat = 'csv';
      } else if (format === 'eclaim') {
        apiFormat = 'eclaim';
      } else if (format === 'shafafiya') {
        apiFormat = 'shafafiya';
      } else {
        throw new Error('Invalid format selected');
      }

      // Convert UploadedFile back to File for the API
      const file = new File([currentFile], currentFile.name, {
        type: currentFile.type,
        lastModified: currentFile.lastModified,
      });

      await dispatch(processFileAsync({ file, format: apiFormat })).unwrap();

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      dispatch(setError(errorMessage));
    }
  }, [currentFile, dispatch]);

  const processSampleFile = useCallback(async (format: string) => {
    try {
      // For sample files, we create a mock file and process it
      const mockFileName = format === 'eclaim' ? 'sample_eclaim.xml' : 'sample_shafafiya.xml';
      const mockFile = new File([''], mockFileName, { type: 'application/xml' });
      
      let apiFormat: 'eclaim' | 'shafafiya';
      if (format === 'eclaim') {
        apiFormat = 'eclaim';
      } else if (format === 'shafafiya') {
        apiFormat = 'shafafiya';
      } else {
        throw new Error('Invalid sample format');
      }

      await dispatch(processFileAsync({ 
        file: mockFile, 
        format: apiFormat 
      })).unwrap();

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sample processing failed';
      dispatch(setError(errorMessage));
    }
  }, [dispatch]);

  const clearResultsHandler = useCallback(() => {
    dispatch(resetProcessing());
  }, [dispatch]);

  // Additional Redux-specific methods
  const processFileWithValidation = useCallback(async (format: string, functionIds: string[]) => {
    await processFile(format);
    
    if (fhirBundle && functionIds.length > 0) {
      await dispatch(validateWithLLMAsync({
        fileId: fhirBundle.id,
        functionIds,
        realTimeUpdates: true,
      })).unwrap();
    }
  }, [processFile, fhirBundle, dispatch]);

  const retryProcessing = useCallback(async () => {
    if (currentFile) {
      // Determine format from file extension or previous processing
      const fileExtension = currentFile.name.split('.').pop()?.toLowerCase();
      const format = fileExtension === 'csv' ? 'csv' : 'eclaim'; // Default to eclaim for XML
      await processFile(format);
    }
  }, [currentFile, processFile]);

  return {
    // Original ProcessingContext interface
    currentFile: currentFile ? new File([currentFile], currentFile.name, {
      type: currentFile.type,
      lastModified: currentFile.lastModified,
    }) : null,
    processingResults,
    isProcessing,
    uploadProgress,
    enableLLMValidation,
    setCurrentFile: setCurrentFileHandler,
    setProcessingResults,
    setIsProcessing,
    setUploadProgress,
    setEnableLLMValidation,
    processFile,
    processSampleFile,
    clearResults: clearResultsHandler,

    // Additional Redux-powered features
    error,
    fhirBundle,
    processFileWithValidation,
    retryProcessing,
    
    // State helpers
    hasFile: !!currentFile,
    hasResults: !!fhirBundle,
    hasError: !!error,
  };
}

export default useProcessing;
import { createListenerMiddleware, isAnyOf } from '@reduxjs/toolkit';
import type { RootState } from '../index';
import { 
  processFileAsync, 
  fetchRequestHistoryAsync,
  setError as setProcessingError,
  updateUploadProgress,
  setProcessingProgress,
} from '../slices/fileProcessingSlice';
import {
  validateWithLLMAsync,
  fetchValidationFunctionsAsync,
  fetchValidationHistoryAsync,
  setError as setValidationError,
} from '../slices/validationSlice';
import { showToast } from '../slices/notificationSlice';

// Create the middleware
export const apiMiddleware = createListenerMiddleware();

// File upload progress tracking
apiMiddleware.startListening({
  matcher: isAnyOf(processFileAsync.pending),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    // Show processing notification
    dispatch(showToast({
      type: 'info',
      title: 'Processing File',
      message: 'Your file is being processed...',
      category: 'processing',
      persistent: true,
    }));

    // Simulate upload progress (in real implementation, this would come from the actual upload)
    for (let progress = 0; progress <= 100; progress += 10) {
      dispatch(updateUploadProgress(progress));
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  },
});

// Handle successful file processing
apiMiddleware.startListening({
  matcher: isAnyOf(processFileAsync.fulfilled),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    dispatch(showToast({
      type: 'success',
      title: 'File Processed Successfully',
      message: 'Your file has been converted to FHIR format.',
      category: 'processing',
      duration: 5000,
    }));

    // Auto-trigger validation if enabled
    const state = listenerApi.getState() as RootState;
    if (state.userPreferences.autoValidation && 
        state.userPreferences.defaultValidationFunctions.length > 0 &&
        action.payload?.fhirBundle?.id) {
      dispatch(validateWithLLMAsync({
        fileId: action.payload.fhirBundle.id,
        functionIds: state.userPreferences.defaultValidationFunctions,
        realTimeUpdates: state.userPreferences.realTimeUpdates,
      }));
    }
  },
});

// Handle file processing errors
apiMiddleware.startListening({
  matcher: isAnyOf(processFileAsync.rejected),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    const errorMessage = action.payload as string || 'File processing failed';
    
    dispatch(showToast({
      type: 'error',
      title: 'Processing Failed',
      message: errorMessage,
      category: 'processing',
      duration: 10000,
    }));
  },
});

// Handle validation start
apiMiddleware.startListening({
  matcher: isAnyOf(validateWithLLMAsync.pending),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    dispatch(showToast({
      type: 'info',
      title: 'Starting LLM Validation',
      message: 'Running quality checks on your data...',
      category: 'validation',
      persistent: true,
    }));
  },
});

// Handle validation completion
apiMiddleware.startListening({
  matcher: isAnyOf(validateWithLLMAsync.fulfilled),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    dispatch(showToast({
      type: 'success',
      title: 'Validation Complete',
      message: 'LLM validation has finished successfully.',
      category: 'validation',
      duration: 5000,
    }));
  },
});

// Handle validation errors
apiMiddleware.startListening({
  matcher: isAnyOf(validateWithLLMAsync.rejected),
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    const errorMessage = action.payload as string || 'Validation failed';
    
    dispatch(showToast({
      type: 'error',
      title: 'Validation Failed',
      message: errorMessage,
      category: 'validation',
      duration: 10000,
    }));
  },
});

// Auto-retry mechanism for failed API calls
apiMiddleware.startListening({
  matcher: isAnyOf(
    processFileAsync.rejected,
    fetchRequestHistoryAsync.rejected,
    validateWithLLMAsync.rejected,
    fetchValidationFunctionsAsync.rejected
  ),
  effect: async (action, listenerApi) => {
    const { dispatch, getState } = listenerApi;
    const state = getState() as RootState;
    
    // Only retry on network errors, not client errors
    if (action.payload && typeof action.payload === 'string' && 
        action.payload.includes('NetworkError')) {
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Retry the original action
      if (action.type.includes('processFile')) {
        // Don't auto-retry file processing due to potential side effects
        dispatch(showToast({
          type: 'warning',
          title: 'Network Error',
          message: 'Please check your connection and try again.',
          category: 'system',
        }));
      } else {
        // Retry other operations
        if (action.meta && 'originalAction' in action.meta) {
          dispatch(action.meta.originalAction as any);
        }
      }
    }
  },
});

// Cache management
apiMiddleware.startListening({
  matcher: isAnyOf(fetchRequestHistoryAsync.fulfilled),
  effect: async (action, listenerApi) => {
    const { getState } = listenerApi;
    const state = getState() as RootState;
    
    // Update cache timestamp if using cache
    if (state.userPreferences.cacheTimeout > 0) {
      // Store cache metadata in localStorage
      localStorage.setItem('nazmito_request_history_cache', JSON.stringify({
        timestamp: Date.now(),
        data: action.payload,
      }));
    }
  },
});

// Offline support
apiMiddleware.startListening({
  predicate: (action) => {
    return action.type.endsWith('/pending') && 
           action.type.includes('Async') &&
           !navigator.onLine;
  },
  effect: async (action, listenerApi) => {
    const { dispatch } = listenerApi;
    
    dispatch(showToast({
      type: 'warning',
      title: 'Offline Mode',
      message: 'You are currently offline. Some features may be limited.',
      category: 'system',
      duration: 8000,
    }));
  },
});

// Performance monitoring
apiMiddleware.startListening({
  matcher: isAnyOf(
    processFileAsync.fulfilled,
    validateWithLLMAsync.fulfilled
  ),
  effect: async (action, listenerApi) => {
    const state = listenerApi.getState() as RootState;
    
    if (state.userPreferences.debugMode) {
      const endTime = Date.now();
      const startTime = action.meta?.startedTimeStamp || endTime;
      const duration = endTime - startTime;
      
      console.debug(`Operation ${action.type} completed in ${duration}ms`);
      
      // Show performance notification in debug mode
      if (duration > 5000) { // If operation took more than 5 seconds
        listenerApi.dispatch(showToast({
          type: 'info',
          title: 'Performance Notice',
          message: `Operation took ${Math.round(duration / 1000)}s to complete`,
          category: 'system',
          duration: 3000,
        }));
      }
    }
  },
});

// Auto-save processed data
apiMiddleware.startListening({
  matcher: isAnyOf(processFileAsync.fulfilled),
  effect: async (action, listenerApi) => {
    const state = listenerApi.getState() as RootState;
    
    if (state.userPreferences.autoSave) {
      try {
        // Save to local storage as backup
        const saveData = {
          fhirBundle: action.payload?.fhirBundle,
          timestamp: Date.now(),
          fileName: state.fileProcessing.currentFile?.name,
        };
        
        localStorage.setItem('nazmito_last_processed', JSON.stringify(saveData));
        
        console.debug('Auto-saved processed data');
      } catch (error) {
        console.warn('Failed to auto-save data:', error);
      }
    }
  },
});

export default apiMiddleware;
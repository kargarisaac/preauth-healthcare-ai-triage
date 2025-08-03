import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiService } from '../../services/apiService';
import type { FHIRBundle, ProcessingRequest, FileValidationResult } from '../../types/healthcare';
import type { UploadedFile } from '../../types/ui';

// Types
interface FileProcessingState {
  // Current file state
  currentFile: UploadedFile | null;
  isProcessing: boolean;
  uploadProgress: number;
  validationResults: FileValidationResult | null;
  
  // Processing results
  fhirBundle: FHIRBundle | null;
  processingStatus: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  processingProgress: number;
  
  // Error handling
  error: string | null;
  
  // History
  processingHistory: ProcessingRequest[];
  
  // Optimistic updates
  optimisticRequests: ProcessingRequest[];
}

const initialState: FileProcessingState = {
  currentFile: null,
  isProcessing: false,
  uploadProgress: 0,
  validationResults: null,
  fhirBundle: null,
  processingStatus: 'idle',
  processingProgress: 0,
  error: null,
  processingHistory: [],
  optimisticRequests: [],
};

// Async thunks
export const processFileAsync = createAsyncThunk(
  'fileProcessing/processFile',
  async (params: { file: File; format: 'eclaim' | 'shafafiya' | 'csv' }, { rejectWithValue, dispatch }) => {
    try {
      const { file, format } = params;
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Determine endpoint based on format
      const endpoint = `/process/${format}`;
      
      // Upload and process file
      const response = await fetch(`/api${endpoint}`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Create processing request for history
      const processingRequest: ProcessingRequest = {
        id: Date.now().toString(),
        memberName: result.data.member_name || 'Unknown',
        memberId: result.data.member_id || 'Unknown',
        provider: result.data.provider || 'Unknown',
        service: result.data.service_type || 'Unknown',
        amount: result.data.amount || '0',
        status: 'Approved',
        date: new Date().toISOString(),
        format: format === 'eclaim' ? 'eClaimLink' : format === 'shafafiya' ? 'Shafafiya' : 'CSV',
      };
      
      // Add to history
      dispatch(addToHistory(processingRequest));
      
      return {
        fhirBundle: result.data as FHIRBundle,
        processingRequest,
      };
    } catch (error: any) {
      return rejectWithValue(error.message || 'File processing failed');
    }
  }
);

export const fetchRequestHistoryAsync = createAsyncThunk(
  'fileProcessing/fetchHistory',
  async (params: { page?: number; limit?: number } = {}, { rejectWithValue }) => {
    try {
      const { page = 1, limit = 50 } = params;
      const response = await apiService.get<ProcessingRequest[]>(
        `/requests?page=${page}&limit=${limit}`
      );
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch request history');
    }
  }
);

// Slice
const fileProcessingSlice = createSlice({
  name: 'fileProcessing',
  initialState,
  reducers: {
    // File upload management
    setCurrentFile: (state, action: PayloadAction<UploadedFile>) => {
      state.currentFile = action.payload;
      state.error = null;
    },
    
    updateUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
      if (state.currentFile) {
        state.currentFile.progress = action.payload;
      }
    },
    
    setValidationResults: (state, action: PayloadAction<FileValidationResult>) => {
      state.validationResults = action.payload;
    },
    
    // Processing management
    setProcessingProgress: (state, action: PayloadAction<number>) => {
      state.processingProgress = action.payload;
    },
    
    setProcessingStatus: (state, action: PayloadAction<FileProcessingState['processingStatus']>) => {
      state.processingStatus = action.payload;
      
      // Update current file status if exists
      if (state.currentFile) {
        switch (action.payload) {
          case 'uploading':
            state.currentFile.status = 'uploading';
            break;
          case 'processing':
            state.currentFile.status = 'processing';
            break;
          case 'completed':
            state.currentFile.status = 'success';
            break;
          case 'error':
            state.currentFile.status = 'error';
            break;
          default:
            state.currentFile.status = 'idle';
        }
      }
    },
    
    // Results management
    setFhirBundle: (state, action: PayloadAction<FHIRBundle>) => {
      state.fhirBundle = action.payload;
    },
    
    // History management
    addToHistory: (state, action: PayloadAction<ProcessingRequest>) => {
      state.processingHistory.unshift(action.payload);
      // Keep only last 100 items
      if (state.processingHistory.length > 100) {
        state.processingHistory = state.processingHistory.slice(0, 100);
      }
    },
    
    // Optimistic updates
    addOptimisticRequest: (state, action: PayloadAction<ProcessingRequest>) => {
      state.optimisticRequests.push(action.payload);
    },
    
    removeOptimisticRequest: (state, action: PayloadAction<string>) => {
      state.optimisticRequests = state.optimisticRequests.filter(
        req => req.id !== action.payload
      );
    },
    
    // Error management
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      if (action.payload && state.currentFile) {
        state.currentFile.error = action.payload;
        state.currentFile.status = 'error';
      }
    },
    
    clearError: (state) => {
      state.error = null;
      if (state.currentFile) {
        state.currentFile.error = undefined;
      }
    },
    
    // Reset operations
    resetProcessing: (state) => {
      state.currentFile = null;
      state.isProcessing = false;
      state.uploadProgress = 0;
      state.validationResults = null;
      state.fhirBundle = null;
      state.processingStatus = 'idle';
      state.processingProgress = 0;
      state.error = null;
      state.optimisticRequests = [];
    },
    
    clearResults: (state) => {
      state.fhirBundle = null;
      state.validationResults = null;
      state.processingProgress = 0;
    },
  },
  extraReducers: (builder) => {
    // Process file async
    builder
      .addCase(processFileAsync.pending, (state) => {
        state.isProcessing = true;
        state.processingStatus = 'processing';
        state.error = null;
      })
      .addCase(processFileAsync.fulfilled, (state, action) => {
        state.isProcessing = false;
        state.processingStatus = 'completed';
        state.fhirBundle = action.payload.fhirBundle;
        state.processingProgress = 100;
        state.error = null;
      })
      .addCase(processFileAsync.rejected, (state, action) => {
        state.isProcessing = false;
        state.processingStatus = 'error';
        state.error = action.payload as string;
      });
    
    // Fetch history async
    builder
      .addCase(fetchRequestHistoryAsync.fulfilled, (state, action) => {
        state.processingHistory = action.payload;
      });
  },
});

// Export actions
export const {
  setCurrentFile,
  updateUploadProgress,
  setValidationResults,
  setProcessingProgress,
  setProcessingStatus,
  setFhirBundle,
  addToHistory,
  addOptimisticRequest,
  removeOptimisticRequest,
  setError,
  clearError,
  resetProcessing,
  clearResults,
} = fileProcessingSlice.actions;

// Export reducer
export default fileProcessingSlice.reducer;
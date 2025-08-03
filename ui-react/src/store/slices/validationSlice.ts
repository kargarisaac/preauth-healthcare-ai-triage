import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiService } from '../../services/apiService';
import type { 
  LLMValidationResult, 
  LLMValidationSummary, 
  LLMValidationFunction,
  LLMValidationProgress,
  LLMFinding 
} from '../../types/llm';

// Types
interface ValidationState {
  // Validation configuration
  availableFunctions: LLMValidationFunction[];
  selectedFunctions: string[];
  
  // Validation execution
  isValidating: boolean;
  validationResults: Record<string, LLMValidationResult>;
  validationProgress: Record<string, LLMValidationProgress>;
  
  // Summary and metrics
  summary: LLMValidationSummary | null;
  qualityScore: number | null;
  
  // Real-time updates
  webSocketConnected: boolean;
  
  // Error handling
  error: string | null;
  
  // History
  validationHistory: Array<{
    id: string;
    timestamp: Date;
    summary: LLMValidationSummary;
    fileId: string;
    fileName: string;
  }>;
}

const initialState: ValidationState = {
  availableFunctions: [],
  selectedFunctions: [],
  isValidating: false,
  validationResults: {},
  validationProgress: {},
  summary: null,
  qualityScore: null,
  webSocketConnected: false,
  error: null,
  validationHistory: [],
};

// Async thunks
export const validateWithLLMAsync = createAsyncThunk(
  'validation/validateWithLLM',
  async (params: { 
    fileId: string; 
    functionIds: string[];
    realTimeUpdates?: boolean;
  }, { rejectWithValue, dispatch }) => {
    try {
      const { fileId, functionIds, realTimeUpdates = true } = params;
      
      // Start validation request
      const response = await apiService.post<{ validationId: string }>('/validate/llm', {
        fileId,
        functionIds,
        realTimeUpdates,
      });
      
      const { validationId } = response.data;
      
      // Set up WebSocket for real-time updates if enabled
      if (realTimeUpdates) {
        dispatch(setupWebSocketConnection(validationId));
      }
      
      return { validationId, functionIds };
    } catch (error: any) {
      return rejectWithValue(error.message || 'LLM validation failed');
    }
  }
);

export const fetchValidationFunctionsAsync = createAsyncThunk(
  'validation/fetchFunctions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiService.get<LLMValidationFunction[]>('/validate/functions');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch validation functions');
    }
  }
);

export const fetchValidationHistoryAsync = createAsyncThunk(
  'validation/fetchHistory',
  async (params: { limit?: number } = {}, { rejectWithValue }) => {
    try {
      const { limit = 50 } = params;
      const response = await apiService.get(`/validate/history?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch validation history');
    }
  }
);

// WebSocket management thunk
const setupWebSocketConnection = createAsyncThunk(
  'validation/setupWebSocket',
  async (validationId: string, { dispatch }) => {
    return new Promise<void>((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/validate/ws/${validationId}`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        dispatch(setWebSocketConnected(true));
        resolve();
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'progress':
              dispatch(updateValidationProgress(message.data));
              break;
            case 'result':
              dispatch(updateValidationResult(message.data));
              break;
            case 'summary':
              dispatch(updateValidationSummary(message.data));
              break;
            case 'error':
              dispatch(setError(message.data.error));
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        dispatch(setWebSocketConnected(false));
        reject(error);
      };
      
      ws.onclose = () => {
        dispatch(setWebSocketConnected(false));
      };
    });
  }
);

// Slice
const validationSlice = createSlice({
  name: 'validation',
  initialState,
  reducers: {
    // Function selection
    setSelectedFunctions: (state, action: PayloadAction<string[]>) => {
      state.selectedFunctions = action.payload;
    },
    
    toggleFunction: (state, action: PayloadAction<string>) => {
      const functionId = action.payload;
      const index = state.selectedFunctions.indexOf(functionId);
      
      if (index > -1) {
        state.selectedFunctions.splice(index, 1);
      } else {
        state.selectedFunctions.push(functionId);
      }
    },
    
    selectAllFunctions: (state) => {
      state.selectedFunctions = state.availableFunctions.map(f => f.id);
    },
    
    clearFunctionSelection: (state) => {
      state.selectedFunctions = [];
    },
    
    // Validation execution
    setValidating: (state, action: PayloadAction<boolean>) => {
      state.isValidating = action.payload;
      if (!action.payload) {
        // Reset progress when validation ends
        state.validationProgress = {};
      }
    },
    
    updateValidationProgress: (state, action: PayloadAction<LLMValidationProgress>) => {
      const progress = action.payload;
      state.validationProgress[progress.functionId] = progress;
    },
    
    updateValidationResult: (state, action: PayloadAction<LLMValidationResult>) => {
      const result = action.payload;
      state.validationResults[result.functionId] = result;
      
      // Remove from progress tracking when completed
      delete state.validationProgress[result.functionId];
    },
    
    updateValidationSummary: (state, action: PayloadAction<LLMValidationSummary>) => {
      state.summary = action.payload;
      
      // Calculate quality score based on findings
      const totalFindings = action.payload.totalFindings;
      const criticalFindings = action.payload.criticalFindings;
      const warningFindings = action.payload.warningFindings;
      
      if (totalFindings === 0) {
        state.qualityScore = 100;
      } else {
        // Quality score calculation: penalize critical more than warnings
        const criticalPenalty = criticalFindings * 20;
        const warningPenalty = warningFindings * 10;
        const totalPenalty = criticalPenalty + warningPenalty;
        state.qualityScore = Math.max(0, 100 - totalPenalty);
      }
      
      // Mark validation as completed
      if (action.payload.overallStatus === 'completed') {
        state.isValidating = false;
      }
    },
    
    // WebSocket management
    setWebSocketConnected: (state, action: PayloadAction<boolean>) => {
      state.webSocketConnected = action.payload;
    },
    
    // Error management
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    clearError: (state) => {
      state.error = null;
    },
    
    // History management
    addToValidationHistory: (state, action: PayloadAction<{
      id: string;
      timestamp: Date;
      summary: LLMValidationSummary;
      fileId: string;
      fileName: string;
    }>) => {
      state.validationHistory.unshift(action.payload);
      // Keep only last 50 items
      if (state.validationHistory.length > 50) {
        state.validationHistory = state.validationHistory.slice(0, 50);
      }
    },
    
    // Reset operations
    resetValidation: (state) => {
      state.isValidating = false;
      state.validationResults = {};
      state.validationProgress = {};
      state.summary = null;
      state.qualityScore = null;
      state.error = null;
    },
    
    clearResults: (state) => {
      state.validationResults = {};
      state.summary = null;
      state.qualityScore = null;
    },
    
  },
  extraReducers: (builder) => {
    // Validate with LLM async
    builder
      .addCase(validateWithLLMAsync.pending, (state) => {
        state.isValidating = true;
        state.error = null;
        state.validationResults = {};
        state.validationProgress = {};
      })
      .addCase(validateWithLLMAsync.fulfilled, (state, action) => {
        // Validation started successfully
        // Real updates will come through WebSocket
      })
      .addCase(validateWithLLMAsync.rejected, (state, action) => {
        state.isValidating = false;
        state.error = action.payload as string;
      });
    
    // Fetch validation functions async
    builder
      .addCase(fetchValidationFunctionsAsync.fulfilled, (state, action) => {
        state.availableFunctions = action.payload;
      });
    
    // Fetch validation history async
    builder
      .addCase(fetchValidationHistoryAsync.fulfilled, (state, action) => {
        state.validationHistory = action.payload;
      });
  },
});

// Export actions
export const {
  setSelectedFunctions,
  toggleFunction,
  selectAllFunctions,
  clearFunctionSelection,
  setValidating,
  updateValidationProgress,
  updateValidationResult,
  updateValidationSummary,
  setWebSocketConnected,
  setError,
  clearError,
  addToValidationHistory,
  resetValidation,
  clearResults,
} = validationSlice.actions;

// Export reducer
export default validationSlice.reducer;
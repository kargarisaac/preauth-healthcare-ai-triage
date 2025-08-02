import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import type { ProcessingRequest, DashboardMetrics } from '@/types/healthcare';

// State interface
interface AppState {
  currentView: string;
  requests: ProcessingRequest[];
  metrics: DashboardMetrics;
  loading: boolean;
  error: string | null;
}

// Action types
type AppAction =
  | { type: 'SET_VIEW'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_REQUEST'; payload: ProcessingRequest }
  | { type: 'UPDATE_REQUESTS'; payload: ProcessingRequest[] }
  | { type: 'UPDATE_METRICS'; payload: Partial<DashboardMetrics> }
  | { type: 'CLEAR_ERROR' };

// Context interface
interface AppContextValue extends AppState {
  dispatch: React.Dispatch<AppAction>;
  switchView: (view: string) => void;
  addRequest: (request: ProcessingRequest) => void;
  updateMetrics: (metrics: Partial<DashboardMetrics>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

// Initial state
const initialState: AppState = {
  currentView: 'overview',
  requests: [],
  metrics: {
    activeRequests: 247,
    autoApproved: 89,
    avgResponseTime: '2.3min',
    costSavings: '$1.2M',
    approvedCount: 189,
    pendingCount: 42,
    deniedCount: 16,
  },
  loading: false,
  error: null,
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_VIEW':
      return { ...state, currentView: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'ADD_REQUEST':
      return {
        ...state,
        requests: [action.payload, ...state.requests],
      };
    case 'UPDATE_REQUESTS':
      return { ...state, requests: action.payload };
    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: { ...state.metrics, ...action.payload },
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
}

// Context
const AppContext = createContext<AppContextValue | undefined>(undefined);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Action creators
  const switchView = (view: string) => {
    dispatch({ type: 'SET_VIEW', payload: view });
  };

  const addRequest = (request: ProcessingRequest) => {
    dispatch({ type: 'ADD_REQUEST', payload: request });
  };

  const updateMetrics = (metrics: Partial<DashboardMetrics>) => {
    dispatch({ type: 'UPDATE_METRICS', payload: metrics });
  };

  const setLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  const value: AppContextValue = {
    ...state,
    dispatch,
    switchView,
    addRequest,
    updateMetrics,
    setLoading,
    setError,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook
export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
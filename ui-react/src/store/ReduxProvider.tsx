import React, { useEffect } from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './index';
import { useAppDispatch, useAppSelector } from './hooks';
import { 
  playNotificationSound, 
  requestDesktopPermission,
  showDesktopNotification 
} from './slices/notificationSlice';
import { selectNotificationSettings, selectActiveToasts, selectIsLoading, selectProcessingState, selectProcessingHistory } from './hooks';

// Notification middleware component
function NotificationHandler() {
  const dispatch = useAppDispatch();
  const settings = useAppSelector(selectNotificationSettings);
  const toasts = useAppSelector(selectActiveToasts);

  useEffect(() => {
    // Request desktop notification permission on first load
    if (settings.desktop && 'Notification' in window) {
      requestDesktopPermission();
    }
  }, [settings.desktop]);

  useEffect(() => {
    // Handle sound and desktop notifications for new toasts
    toasts.forEach(toast => {
      // Play sound if enabled
      if (settings.sound) {
        playNotificationSound(toast.type);
      }

      // Show desktop notification if enabled
      if (settings.desktop) {
        showDesktopNotification(toast);
      }
    });
  }, [toasts, settings.sound, settings.desktop]);

  return null;
}

// Auto-save middleware component
function AutoSaveHandler() {
  const preferences = useAppSelector(state => state.userPreferences);
  
  useEffect(() => {
    if (!preferences.autoSave) return;

    const interval = setInterval(() => {
      // Auto-save logic could be implemented here
      // For now, persistence is handled by redux-persist
      console.debug('Auto-save triggered');
    }, preferences.autoSaveInterval * 1000);

    return () => clearInterval(interval);
  }, [preferences.autoSave, preferences.autoSaveInterval]);

  return null;
}

// Note: Theme handling is now managed by ThemeContext
// This component is kept for backward compatibility
function ThemeHandler() {
  return null;
}

// Performance monitoring component
function PerformanceMonitor() {
  const isLoading = useAppSelector(selectIsLoading);
  const debugMode = useAppSelector(state => state.userPreferences.debugMode);

  useEffect(() => {
    if (!debugMode) return;

    // Log state changes in debug mode
    console.debug('Loading state changed:', isLoading);
  }, [isLoading, debugMode]);

  return null;
}

// Toast auto-removal handler
function ToastAutoRemover() {
  const dispatch = useAppDispatch();
  const toasts = useAppSelector(selectActiveToasts);

  useEffect(() => {
    toasts.forEach(toast => {
      if (toast.duration && toast.duration > 0) {
        const timeout = setTimeout(() => {
          dispatch({ type: 'notifications/removeToast', payload: toast.id });
        }, toast.duration);

        return () => clearTimeout(timeout);
      }
    });
  }, [toasts, dispatch]);

  return null;
}

// Loading fallback component
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading Nazmito...</p>
      </div>
    </div>
  );
}

// Main Redux Provider component
interface ReduxProviderProps {
  children: React.ReactNode;
}

export function ReduxProvider({ children }: ReduxProviderProps) {
  return (
    <Provider store={store}>
      <PersistGate loading={<LoadingFallback />} persistor={persistor}>
        <NotificationHandler />
        <AutoSaveHandler />
        <ThemeHandler />
        <PerformanceMonitor />
        <ToastAutoRemover />
        {children}
      </PersistGate>
    </Provider>
  );
}

// Legacy context compatibility hooks
// These help with gradual migration from Context API
export function useApp() {
  const dispatch = useAppDispatch();
  const processingState = useAppSelector(selectProcessingState);
  const processingHistory = useAppSelector(selectProcessingHistory);
  const preferences = useAppSelector(selectUserPreferences);

  return {
    // Current view management
    currentView: 'overview', // This would need to be added to state if needed
    
    // Processing state
    ...processingState,
    requests: processingHistory,
    
    // Actions - mapped to Redux actions
    switchView: (view: string) => {
      // This would need to be implemented if view state is needed
      console.log('Switch view:', view);
    },
    
    addRequest: (request: any) => {
      dispatch({ type: 'fileProcessing/addToHistory', payload: request });
    },
    
    updateMetrics: (metrics: any) => {
      // This would need to be implemented based on requirements
      console.log('Update metrics:', metrics);
    },
    
    setLoading: (loading: boolean) => {
      dispatch({ type: 'fileProcessing/setProcessingStatus', payload: loading ? 'processing' : 'idle' });
    },
    
    setError: (error: string | null) => {
      dispatch({ type: 'fileProcessing/setError', payload: error });
    },
    
    // Metrics - derived from state
    metrics: {
      activeRequests: processingHistory.length,
      autoApproved: processingHistory.filter(r => r.status === 'Approved').length,
      avgResponseTime: '2.3min', // This would need to be calculated
      costSavings: '$1.2M', // This would need to be calculated
      approvedCount: processingHistory.filter(r => r.status === 'Approved').length,
      pendingCount: processingHistory.filter(r => r.status === 'Pending').length,
      deniedCount: processingHistory.filter(r => r.status === 'Denied').length,
    },
  };
}

export function useToast() {
  const dispatch = useAppDispatch();
  const toasts = useAppSelector(selectActiveToasts);

  return {
    toasts,
    showToast: (toast: any) => {
      dispatch({ type: 'notifications/showToast', payload: toast });
    },
    removeToast: (id: string) => {
      dispatch({ type: 'notifications/removeToast', payload: id });
    },
    clearToasts: () => {
      dispatch({ type: 'notifications/clearToasts' });
    },
  };
}

// Export utility function to get store instance
export function getStore() {
  return store;
}

// Export types for external use
export type { RootState, AppDispatch } from './index';
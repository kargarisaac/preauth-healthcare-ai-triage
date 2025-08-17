import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { insurerApi } from '@/services/apiService';
import { useToast } from './ToastContext';
import type {
  InsurerRequest,
  InsurerMetrics,
  InsurerDashboardFilters,
  MedicalDirectorDecision,
  PatientHistoryEntry,
  MobileNotification
} from '@/types/insurer';

interface InsurerContextValue {
  // State
  requests: InsurerRequest[];
  selectedRequest: InsurerRequest | null;
  patientHistory: PatientHistoryEntry[];
  metrics: InsurerMetrics | null;
  notifications: MobileNotification[];
  filters: InsurerDashboardFilters;
  isLoading: boolean;
  error: string | null;
  
  // Request Management
  loadRequests: (refresh?: boolean) => Promise<void>;
  selectRequest: (requestId: string) => Promise<void>;
  clearSelection: () => void;
  
  // Decision Management
  submitDecision: (requestId: string, decision: MedicalDirectorDecision) => Promise<boolean>;
  assignRequest: (requestId: string, assignee: string) => Promise<boolean>;
  
  // Patient History
  loadPatientHistory: (patientId: string) => Promise<void>;
  
  // Filters and Search
  updateFilters: (newFilters: Partial<InsurerDashboardFilters>) => void;
  clearFilters: () => void;
  
  // Metrics and Analytics
  refreshMetrics: () => Promise<void>;
  
  // Notifications
  loadNotifications: () => Promise<void>;
  markNotificationRead: (notificationId: string) => void;
  
  // Real-time Updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
}

const InsurerContext = createContext<InsurerContextValue | undefined>(undefined);

interface InsurerProviderProps {
  children: ReactNode;
}

const defaultFilters: InsurerDashboardFilters = {
  status: [],
  urgency: [],
  riskLevel: [],
  aiRecommendation: [],
  hasRiskFlags: false,
  requiresEscalation: false,
};

export function InsurerProvider({ children }: InsurerProviderProps) {
  // State
  const [requests, setRequests] = useState<InsurerRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<InsurerRequest | null>(null);
  const [patientHistory, setPatientHistory] = useState<PatientHistoryEntry[]>([]);
  const [metrics, setMetrics] = useState<InsurerMetrics | null>(null);
  const [notifications, setNotifications] = useState<MobileNotification[]>([]);
  const [filters, setFilters] = useState<InsurerDashboardFilters>(defaultFilters);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { showToast } = useToast();

  // Load requests with filters
  const loadRequests = useCallback(async (refresh = false) => {
    if (isLoading && !refresh) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await insurerApi.getRequests(filters);
      
      if (response.success) {
        setRequests(response.data);
      } else {
        throw new Error('Failed to load requests');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load requests';
      setError(errorMessage);
      
      showToast({
        type: 'error',
        title: 'Loading Failed',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  }, [filters, isLoading, showToast]);

  // Select and load specific request
  const selectRequest = useCallback(async (requestId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await insurerApi.getRequest(requestId);
      
      if (response.success) {
        setSelectedRequest(response.data);
        
        // Also load patient history if available
        if (response.data.patientId) {
          await loadPatientHistory(response.data.patientId);
        }
      } else {
        throw new Error('Failed to load request details');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load request';
      setError(errorMessage);
      
      showToast({
        type: 'error',
        title: 'Request Loading Failed',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  // Clear request selection
  const clearSelection = useCallback(() => {
    setSelectedRequest(null);
    setPatientHistory([]);
  }, []);

  // Submit decision
  const submitDecision = useCallback(async (
    requestId: string, 
    decision: MedicalDirectorDecision
  ): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      const response = await insurerApi.submitDecision(requestId, decision);
      
      if (response.success) {
        showToast({
          type: 'success',
          title: 'Decision Submitted',
          message: `${decision.decision} decision has been processed successfully.`,
        });
        
        // Refresh requests to show updated status
        await loadRequests(true);
        
        return true;
      } else {
        throw new Error(response.data?.error || 'Failed to submit decision');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to submit decision';
      
      showToast({
        type: 'error',
        title: 'Decision Submission Failed',
        message: errorMessage,
      });
      
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [loadRequests, showToast]);

  // Assign request
  const assignRequest = useCallback(async (
    requestId: string, 
    assignee: string
  ): Promise<boolean> => {
    try {
      const response = await insurerApi.assignRequest(requestId, assignee);
      
      if (response.success) {
        showToast({
          type: 'success',
          title: 'Request Assigned',
          message: `Request assigned to ${assignee} successfully.`,
        });
        
        // Update local state
        setRequests(prev => prev.map(req => 
          req.id === requestId 
            ? { ...req, assignedReviewer: assignee, assignedDate: new Date().toISOString() }
            : req
        ));
        
        return true;
      } else {
        throw new Error('Failed to assign request');
      }
    } catch (err: any) {
      showToast({
        type: 'error',
        title: 'Assignment Failed',
        message: err.message || 'Failed to assign request',
      });
      
      return false;
    }
  }, [showToast]);

  // Load patient history
  const loadPatientHistory = useCallback(async (patientId: string) => {
    try {
      const response = await insurerApi.getPatientHistory(patientId);
      
      if (response.success) {
        setPatientHistory(response.data);
      }
    } catch (err: any) {
      console.error('Failed to load patient history:', err);
      // Don't show toast for this - it's supplementary data
    }
  }, []);

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<InsurerDashboardFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Clear filters
  const clearFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, []);

  // Refresh metrics
  const refreshMetrics = useCallback(async () => {
    try {
      const response = await insurerApi.getDashboardMetrics();
      
      if (response.success) {
        setMetrics(response.data);
      }
    } catch (err: any) {
      console.error('Failed to load metrics:', err);
    }
  }, []);

  // Load notifications
  const loadNotifications = useCallback(async () => {
    try {
      const response = await insurerApi.getNotifications();
      
      if (response.success) {
        setNotifications(response.data);
      }
    } catch (err: any) {
      console.error('Failed to load notifications:', err);
    }
  }, []);

  // Mark notification as read
  const markNotificationRead = useCallback((notificationId: string) => {
    setNotifications(prev => prev.map(notif => 
      notif.id === notificationId 
        ? { ...notif, read: true }
        : notif
    ));
  }, []);

  // Real-time updates (WebSocket connection)
  const subscribeToUpdates = useCallback(() => {
    // TODO: Implement WebSocket connection for real-time updates
    console.log('Subscribing to real-time updates');
  }, []);

  const unsubscribeFromUpdates = useCallback(() => {
    // TODO: Cleanup WebSocket connection
    console.log('Unsubscribing from real-time updates');
  }, []);

  // Auto-refresh requests when filters change
  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  // Load initial data
  useEffect(() => {
    refreshMetrics();
    loadNotifications();
    subscribeToUpdates();
    
    return () => {
      unsubscribeFromUpdates();
    };
  }, [refreshMetrics, loadNotifications, subscribeToUpdates, unsubscribeFromUpdates]);

  // Periodic refresh of metrics and notifications
  useEffect(() => {
    const interval = setInterval(() => {
      refreshMetrics();
      loadNotifications();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [refreshMetrics, loadNotifications]);

  return (
    <InsurerContext.Provider value={{
      // State
      requests,
      selectedRequest,
      patientHistory,
      metrics,
      notifications,
      filters,
      isLoading,
      error,
      
      // Request Management
      loadRequests,
      selectRequest,
      clearSelection,
      
      // Decision Management
      submitDecision,
      assignRequest,
      
      // Patient History
      loadPatientHistory,
      
      // Filters and Search
      updateFilters,
      clearFilters,
      
      // Metrics and Analytics
      refreshMetrics,
      
      // Notifications
      loadNotifications,
      markNotificationRead,
      
      // Real-time Updates
      subscribeToUpdates,
      unsubscribeFromUpdates,
    }}>
      {children}
    </InsurerContext.Provider>
  );
}

export function useInsurer() {
  const context = useContext(InsurerContext);
  if (context === undefined) {
    throw new Error('useInsurer must be used within an InsurerProvider');
  }
  return context;
}
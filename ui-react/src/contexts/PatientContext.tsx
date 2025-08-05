import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { PatientInfo, DashboardData } from '@/types/api';
import { patientApi } from '@/services/apiService';
import { useToast } from './ToastContext';

interface PatientContextValue {
  // State
  selectedPatient: PatientInfo | null;
  patientsList: PatientInfo[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  selectPatient: (patient: PatientInfo | null) => void;
  fetchPatients: () => Promise<void>;
  clearSelection: () => void;
  
  // Dashboard data
  dashboardData: DashboardData | null;
  fetchPatientDashboard: (patientId: string) => Promise<void>;
}

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

interface PatientProviderProps {
  children: ReactNode;
}

export function PatientProvider({ children }: PatientProviderProps) {
  const [selectedPatient, setSelectedPatient] = useState<PatientInfo | null>(null);
  const [patientsList, setPatientsList] = useState<PatientInfo[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { showToast } = useToast();

  const selectPatient = useCallback((patient: PatientInfo | null) => {
    setSelectedPatient(patient);
    if (!patient) {
      setDashboardData(null);
    }
  }, []);

  const fetchPatients = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await patientApi.getPatients();
      if (response.success && response.data) {
        setPatientsList(response.data);
      } else {
        throw new Error('Failed to fetch patients');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch patients';
      setError(errorMessage);
      showToast({
        type: 'error',
        title: 'Error',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  const fetchPatientDashboard = useCallback(async (patientId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await patientApi.getPatientDashboard(patientId);
      if (response.success && response.data) {
        setDashboardData(response.data);
      } else {
        throw new Error('Failed to fetch patient dashboard data');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch patient dashboard data';
      setError(errorMessage);
      showToast({
        type: 'error',
        title: 'Error',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  const clearSelection = useCallback(() => {
    setSelectedPatient(null);
    setDashboardData(null);
    setError(null);
  }, []);

  const value: PatientContextValue = {
    selectedPatient,
    patientsList,
    isLoading,
    error,
    selectPatient,
    fetchPatients,
    clearSelection,
    dashboardData,
    fetchPatientDashboard,
  };

  return (
    <PatientContext.Provider value={value}>
      {children}
    </PatientContext.Provider>
  );
}

export function usePatient() {
  const context = useContext(PatientContext);
  if (context === undefined) {
    throw new Error('usePatient must be used within a PatientProvider');
  }
  return context;
}
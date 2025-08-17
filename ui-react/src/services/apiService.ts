// Import the updated API types
import type { PatientInfo, DashboardData, XMLProcessResponse, AnalysisResponse } from '@/types/api';

// API configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Request types
interface RequestOptions extends RequestInit {
  cache?: 'no-cache' | 'short' | 'medium' | 'long';
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

// Response wrapper
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  cached?: boolean;
  timestamp?: number;
}

// Error types
class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

// Memory cache for in-memory caching
const memoryCache = new Map<string, { data: any; timestamp: number; duration: number }>();

// Main API service class
class ApiService {
  private abortControllers = new Map<string, AbortController>();

  // Generic request method
  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const {
      timeout = 10000,
      retries = 3,
      retryDelay = 1000,
      cache: customCache,
      ...fetchOptions
    } = options;

    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

    // Convert custom cache values to standard RequestCache values
    let standardCache: RequestCache = 'default';
    if (customCache) {
      switch (customCache) {
        case 'no-cache':
          standardCache = 'no-cache';
          break;
        case 'short':
          standardCache = 'no-store'; // No caching for short-lived data
          break;
        case 'medium':
          standardCache = 'default';
          break;
        case 'long':
          standardCache = 'force-cache';
          break;
        default:
          standardCache = 'default';
      }
    }

    // Prepare request
    const requestOptions: RequestInit = {
      ...fetchOptions,
      cache: standardCache,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
    };

    let lastError: Error;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, requestOptions);

        if (!response.ok) {
          throw new ApiError(
            `HTTP error! status: ${response.status}`,
            response.status
          );
        }

        const data = await response.json();
        const result: ApiResponse<T> = {
          data,
          success: true,
          timestamp: Date.now()
        };

        return result;

      } catch (error: any) {
        lastError = error;

        // Don't retry on client errors
        if (error.status && error.status < 500) {
          break;
        }

        // Wait before retry
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
        }
      }
    }

    if (!navigator.onLine) {
      throw new NetworkError('No internet connection');
    }

    throw lastError;
  }

  // GET request
  async get<T>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  // POST request
  async post<T>(endpoint: string, data?: any, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // File upload with FormData
  async uploadFile<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>,
    options: Omit<RequestOptions, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value.toString());
      });
    }

    const { headers, ...restOptions } = options;
    return this.request<T>(endpoint, {
      ...restOptions,
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData, let browser set it with boundary
        // Remove any Content-Type header that might be set
        ...Object.fromEntries(
          Object.entries(headers || {}).filter(([key]) => key.toLowerCase() !== 'content-type')
        ),
      },
    });
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Patient API endpoints
export const patientApi = {
  // Get all patients for dropdown
  getPatients: () => apiService.get<PatientInfo[]>('/patients'),
  
  // Upload XML file for patient
  uploadXml: (file: File, source: 'eclaim' | 'shafafiya', patientId?: string) => {
    const additionalData: Record<string, any> = { source };
    if (patientId) {
      additionalData.patient_id = patientId;
    }
    return apiService.uploadFile<XMLProcessResponse>('/upload-xml', file, additionalData);
  },
  
  // Process XML for specific patient
  processPatient: (patientId: string) => 
    apiService.post<XMLProcessResponse>(`/process/${patientId}`),
  
  // Run Claude analysis
  analyzePatient: (patientId: string, costLimit: number = 1.0, includeHistory: boolean = true) => 
    apiService.post<AnalysisResponse>(`/analyze/${patientId}`, {
      cost_limit_usd: costLimit,
      include_history: includeHistory
    }),
  
  // Get patient dashboard data
  getPatientDashboard: (patientId: string) => 
    apiService.get<DashboardData>(`/patient/${patientId}/dashboard`),
  
  // Health check endpoint
  getHealthStatus: () => apiService.get('/health'),
};

// Export error types
export { ApiError, NetworkError };

// Insurer API endpoints
export const insurerApi = {
  // Request management
  getRequests: (filters?: any) => 
    apiService.get<any[]>('/insurer/requests', { cache: 'short' }),
  
  getRequest: (requestId: string) => 
    apiService.get<any>(`/insurer/requests/${requestId}`),
  
  submitDecision: (requestId: string, decision: any) => 
    apiService.post<any>(`/insurer/requests/${requestId}/decision`, decision),
  
  assignRequest: (requestId: string, assignee: string) => 
    apiService.put<any>(`/insurer/requests/${requestId}/assign`, { assignee }),
  
  markCommunicated: (requestId: string) => 
    apiService.post<any>(`/insurer/requests/${requestId}/communicate`, {}),
  
  // Patient history
  getPatientHistory: (patientId: string) => 
    apiService.get<any>(`/insurer/patients/${patientId}/history`),
  
  // Analytics and metrics
  getDashboardMetrics: () => 
    apiService.get<any>('/insurer/dashboard/metrics', { cache: 'short' }),
  
  // Real-time notifications
  getNotifications: () => 
    apiService.get<any[]>('/insurer/notifications'),
};

// Pipeline processing with automatic request creation
export const pipelineApi = {
  // Process file and automatically create insurer request
  processFileWithRequest: (file: File, source: string, mode: string = 'hybrid') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source', source);
    formData.append('mode', mode);
    formData.append('create_request', 'true'); // Flag to create insurer request
    
    return apiService.request<any>('/pipeline/process', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set content-type for FormData
    });
  },
  
  // Process sample with request creation
  processSampleWithRequest: (sampleType: string, mode: string = 'hybrid') => 
    apiService.post<any>(`/process/sample/${sampleType}`, { 
      mode, 
      create_request: true 
    }),
  
  // Get processing status
  getProcessingStatus: (analysisId: string) => 
    apiService.get<any>(`/process/status/${analysisId}`),
};

// Export types
export type { ApiResponse, RequestOptions };

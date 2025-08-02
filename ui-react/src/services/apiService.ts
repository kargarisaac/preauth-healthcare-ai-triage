// API configuration
const API_BASE_URL = '/api';

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
      ...fetchOptions
    } = options;
    
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    
    // Prepare request
    const requestOptions: RequestInit = {
      ...fetchOptions,
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
}

// Create singleton instance
export const apiService = new ApiService();

// Export error types
export { ApiError, NetworkError };

// Export types
export type { ApiResponse, RequestOptions };
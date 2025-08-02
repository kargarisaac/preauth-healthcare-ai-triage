import type {
  RequestHistoryItem,
  RequestFilters,
  RequestHistoryResponse,
  RequestExportOptions,
  BulkOperationPayload,
} from '@/types/requests';

// API endpoints
const API_BASE = '/api';
const ENDPOINTS = {
  REQUESTS: `${API_BASE}/requests`,
  REQUEST_DETAILS: (id: string) => `${API_BASE}/requests/${id}`,
  EXPORT: `${API_BASE}/requests/export`,
  BULK_OPERATIONS: `${API_BASE}/requests/bulk`,
  SEARCH: `${API_BASE}/requests/search`,
  FACETS: `${API_BASE}/requests/facets`,
} as const;

// Request timeout
const REQUEST_TIMEOUT = 30000; // 30 seconds

// Helper function to create AbortController with timeout
function createTimeoutController(timeoutMs = REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  // Clear timeout if request completes
  const originalSignal = controller.signal;
  const cleanup = () => clearTimeout(timeoutId);
  originalSignal.addEventListener('abort', cleanup);
  
  return { controller, cleanup };
}

// Helper function to handle API responses
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${response.status}: ${errorText}`);
  }
  
  const contentType = response.headers.get('content-type');
  if (contentType?.includes('application/json')) {
    return response.json();
  }
  
  throw new Error('Invalid response format');
}

// Helper function to build query parameters
function buildQueryParams(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, String(item)));
      } else if (typeof value === 'object') {
        searchParams.append(key, JSON.stringify(value));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  return searchParams.toString();
}

class RequestHistoryService {
  // Get paginated request history
  async getRequests(filters: RequestFilters): Promise<RequestHistoryResponse> {
    const { controller, cleanup } = createTimeoutController();
    
    try {
      const queryParams = buildQueryParams({
        page: filters.pagination.page,
        pageSize: filters.pagination.pageSize,
        sortField: filters.sort.field,
        sortDirection: filters.sort.direction,
        ...filters.search,
      });
      
      const response = await fetch(`${ENDPOINTS.REQUESTS}?${queryParams}`, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      return await handleApiResponse<RequestHistoryResponse>(response);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Get detailed request information
  async getRequestDetails(requestId: string): Promise<RequestHistoryItem> {
    const { controller, cleanup } = createTimeoutController();
    
    try {
      const response = await fetch(ENDPOINTS.REQUEST_DETAILS(requestId), {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await handleApiResponse<{ data: RequestHistoryItem }>(response);
      return result.data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Search requests with advanced criteria
  async searchRequests(
    query: string,
    filters: RequestFilters,
    signal?: AbortSignal
  ): Promise<RequestHistoryResponse> {
    const { controller, cleanup } = createTimeoutController();
    const combinedSignal = signal || controller.signal;
    
    try {
      const body = {
        query,
        filters: filters.search,
        sort: filters.sort,
        pagination: filters.pagination,
      };
      
      const response = await fetch(ENDPOINTS.SEARCH, {
        method: 'POST',
        signal: combinedSignal,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      return await handleApiResponse<RequestHistoryResponse>(response);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Search timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Export requests
  async exportRequests(
    filters: RequestFilters,
    options: RequestExportOptions
  ): Promise<Blob> {
    const { controller, cleanup } = createTimeoutController(60000); // 1 minute for exports
    
    try {
      const body = {
        filters: filters.search,
        sort: filters.sort,
        options,
      };
      
      const response = await fetch(ENDPOINTS.EXPORT, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }
      
      return await response.blob();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Export timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Bulk operations (approve, deny, assign, etc.)
  async performBulkOperation(payload: BulkOperationPayload): Promise<void> {
    const { controller, cleanup } = createTimeoutController();
    
    try {
      const response = await fetch(ENDPOINTS.BULK_OPERATIONS, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      await handleApiResponse(response);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Bulk operation timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Get faceted search data for filters
  async getFacets(filters?: Partial<RequestFilters['search']>): Promise<{
    status: Record<string, number>;
    priority: Record<string, number>;
    providers: Array<{ id: string; name: string; count: number }>;
    assignees: Array<{ id: string; name: string; count: number }>;
  }> {
    const { controller, cleanup } = createTimeoutController();
    
    try {
      const queryParams = filters ? buildQueryParams(filters) : '';
      const response = await fetch(`${ENDPOINTS.FACETS}?${queryParams}`, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await handleApiResponse<{ data: any }>(response);
      return result.data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Facets request timeout');
      }
      throw error;
    } finally {
      cleanup();
    }
  }

  // Download exported file
  async downloadExport(blob: Blob, filename: string): Promise<void> {
    try {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw new Error('Failed to download export file');
    }
  }

  // Cache management
  private cache = new Map<string, { data: any; timestamp: number }>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  private getCacheKey(filters: RequestFilters): string {
    return JSON.stringify(filters);
  }

  private isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < this.CACHE_TTL;
  }

  // Get cached requests or fetch new ones
  async getCachedRequests(filters: RequestFilters): Promise<RequestHistoryResponse> {
    const cacheKey = this.getCacheKey(filters);
    const cached = this.cache.get(cacheKey);
    
    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.data;
    }
    
    const data = await this.getRequests(filters);
    this.cache.set(cacheKey, { data, timestamp: Date.now() });
    
    return data;
  }

  // Clear cache
  clearCache(): void {
    this.cache.clear();
  }

  // Remove expired cache entries
  cleanupCache(): void {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (!this.isCacheValid(value.timestamp)) {
        this.cache.delete(key);
      }
    }
  }
}

// Create singleton instance
export const requestHistoryService = new RequestHistoryService();

// Auto cleanup cache every 10 minutes
setInterval(() => {
  requestHistoryService.cleanupCache();
}, 10 * 60 * 1000);
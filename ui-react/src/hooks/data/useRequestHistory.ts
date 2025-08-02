import { useState, useEffect, useCallback, useMemo } from 'react';
import { useToast } from '@/contexts/ToastContext';
import type {
  RequestHistoryItem,
  RequestHistoryResponse,
  RequestDetailsResponse,
  RequestFilters,
  RequestSearchCriteria,
  RequestSortOptions,
  BulkOperationPayload,
  RequestCacheEntry,
  RequestExportOptions,
} from '@/types/requests';

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const cache = new Map<string, RequestCacheEntry>();

// Generate cache key from filters
const generateCacheKey = (filters: RequestFilters): string => {
  return JSON.stringify(filters);
};

// Check if cache entry is valid
const isCacheValid = (entry: RequestCacheEntry): boolean => {
  return Date.now() - entry.timestamp < CACHE_DURATION;
};

export function useRequestHistory() {
  const [requests, setRequests] = useState<RequestHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<RequestFilters>({
    search: {},
    sort: { field: 'submissionDate', direction: 'desc' },
    pagination: { page: 1, pageSize: 25 },
  });

  const { showToast } = useToast();

  // Fetch requests with caching
  const fetchRequests = useCallback(async (newFilters?: Partial<RequestFilters>) => {
    const currentFilters = newFilters ? { ...filters, ...newFilters } : filters;
    const cacheKey = generateCacheKey(currentFilters);
    
    // Check cache first
    const cachedEntry = cache.get(cacheKey);
    if (cachedEntry && isCacheValid(cachedEntry)) {
      setRequests(cachedEntry.data);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      
      // Add pagination
      queryParams.append('page', currentFilters.pagination.page.toString());
      queryParams.append('page_size', currentFilters.pagination.pageSize.toString());
      
      // Add sorting
      queryParams.append('sort_field', currentFilters.sort.field as string);
      queryParams.append('sort_direction', currentFilters.sort.direction);
      
      // Add search criteria
      const { search } = currentFilters;
      if (search.query) queryParams.append('query', search.query);
      if (search.status?.length) queryParams.append('status', search.status.join(','));
      if (search.type?.length) queryParams.append('type', search.type.join(','));
      if (search.priority?.length) queryParams.append('priority', search.priority.join(','));
      if (search.providerId?.length) queryParams.append('provider_id', search.providerId.join(','));
      if (search.assignedTo?.length) queryParams.append('assigned_to', search.assignedTo.join(','));
      if (search.tags?.length) queryParams.append('tags', search.tags.join(','));
      if (search.hasDocuments !== undefined) queryParams.append('has_documents', search.hasDocuments.toString());
      
      // Add date range
      if (search.dateRange?.from) queryParams.append('date_from', search.dateRange.from);
      if (search.dateRange?.to) queryParams.append('date_to', search.dateRange.to);
      
      // Add amount range
      if (search.amountRange?.min) queryParams.append('amount_min', search.amountRange.min.toString());
      if (search.amountRange?.max) queryParams.append('amount_max', search.amountRange.max.toString());

      const response = await fetch(`/api/requests/history?${queryParams}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: RequestHistoryResponse = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch request history');
      }

      const { requests: fetchedRequests, total: fetchedTotal } = result.data;
      
      setRequests(fetchedRequests);
      setTotal(fetchedTotal);
      
      // Cache the results
      cache.set(cacheKey, {
        key: cacheKey,
        data: fetchedRequests,
        timestamp: Date.now(),
        filters: currentFilters,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch requests';
      setError(errorMessage);
      showToast({
        type: 'error',
        title: 'Error Loading Requests',
        message: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  }, [filters, showToast]);

  // Fetch request details
  const fetchRequestDetails = useCallback(async (requestId: string) => {
    try {
      const response = await fetch(`/api/requests/${requestId}/details`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: RequestDetailsResponse = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch request details');
      }

      return result.data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch request details';
      showToast({
        type: 'error',
        title: 'Error Loading Request Details',
        message: errorMessage,
      });
      throw err;
    }
  }, [showToast]);

  // Update filters and refresh data
  const updateFilters = useCallback((newFilters: Partial<RequestFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    fetchRequests(newFilters);
  }, [filters, fetchRequests]);

  // Update search criteria
  const updateSearch = useCallback((search: Partial<RequestSearchCriteria>) => {
    updateFilters({
      search: { ...filters.search, ...search },
      pagination: { ...filters.pagination, page: 1 }, // Reset to first page
    });
  }, [filters, updateFilters]);

  // Update sorting
  const updateSort = useCallback((sort: RequestSortOptions) => {
    updateFilters({ sort });
  }, [updateFilters]);

  // Update pagination
  const updatePagination = useCallback((pagination: Partial<{ page: number; pageSize: number }>) => {
    updateFilters({
      pagination: { ...filters.pagination, ...pagination },
    });
  }, [filters, updateFilters]);

  // Perform bulk operations
  const performBulkOperation = useCallback(async (payload: BulkOperationPayload) => {
    try {
      const response = await fetch('/api/requests/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Bulk operation failed');
      }

      // Clear cache to force refresh
      cache.clear();
      
      showToast({
        type: 'success',
        title: 'Bulk Operation Complete',
        message: `Successfully processed ${payload.requestIds.length} requests`,
      });

      // Refresh data
      await fetchRequests();

      return result;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bulk operation failed';
      showToast({
        type: 'error',
        title: 'Bulk Operation Failed',
        message: errorMessage,
      });
      throw err;
    }
  }, [fetchRequests, showToast]);

  // Export requests
  const exportRequests = useCallback(async (options: RequestExportOptions) => {
    try {
      const response = await fetch('/api/requests/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...options,
          filters: filters.search,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle file download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `requests_export_${new Date().toISOString().split('T')[0]}.${options.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast({
        type: 'success',
        title: 'Export Complete',
        message: 'Requests exported successfully',
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      showToast({
        type: 'error',
        title: 'Export Failed',
        message: errorMessage,
      });
      throw err;
    }
  }, [filters, showToast]);

  // Clear cache
  const clearCache = useCallback(() => {
    cache.clear();
  }, []);

  // Computed values
  const hasFilters = useMemo(() => {
    const { search } = filters;
    return !!(
      search.query ||
      search.status?.length ||
      search.type?.length ||
      search.priority?.length ||
      search.providerId?.length ||
      search.assignedTo?.length ||
      search.tags?.length ||
      search.dateRange?.from ||
      search.dateRange?.to ||
      search.amountRange?.min ||
      search.amountRange?.max ||
      search.hasDocuments !== undefined
    );
  }, [filters]);

  const totalPages = useMemo(() => {
    return Math.ceil(total / filters.pagination.pageSize);
  }, [total, filters.pagination.pageSize]);

  // Initial fetch
  useEffect(() => {
    fetchRequests();
  }, []); // Only run on mount

  return {
    // State
    requests,
    total,
    totalPages,
    isLoading,
    error,
    filters,
    hasFilters,

    // Actions
    fetchRequests,
    fetchRequestDetails,
    updateFilters,
    updateSearch,
    updateSort,
    updatePagination,
    performBulkOperation,
    exportRequests,
    clearCache,

    // Utilities
    refresh: () => {
      clearCache();
      fetchRequests();
    },
  };
}
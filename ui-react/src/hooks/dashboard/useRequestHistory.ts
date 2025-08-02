import { useState, useEffect, useCallback, useMemo } from 'react';
import { useDebounce } from 'use-debounce';
import type {
  RequestHistoryItem,
  RequestFilters,
  RequestExportOptions,
  BulkOperationPayload,
} from '@/types/requests';
import { requestHistoryService } from '@/services/requestHistoryService';

// Mock data generator for development
const generateMockRequests = (count: number): RequestHistoryItem[] => {
  const statuses: Array<RequestHistoryItem['status']> = ['approved', 'pending', 'denied', 'under_review'];
  const priorities: Array<RequestHistoryItem['priority']> = ['low', 'medium', 'high', 'urgent'];
  const formats: Array<RequestHistoryItem['format']> = ['eClaimLink', 'Shafafiya', 'CSV', 'Manual'];

  const providers = [
    'Emirates Hospital', 'Dubai Hospital', 'American Hospital Dubai',
    'Mediclinic City Hospital', 'NMC Royal Hospital', 'Aster Hospital',
    'Saudi German Hospital', 'Zulekha Hospital', 'Al Zahra Hospital'
  ];

  const services = [
    'MRI Brain Scan', 'Cardiac Catheterization', 'Orthopedic Surgery',
    'Emergency Room Visit', 'Laboratory Tests', 'Physiotherapy Session',
    'Dental Treatment', 'Eye Surgery', 'Dermatology Consultation'
  ];

  const members = [
    'Ahmed Al Rashid', 'Fatima Al Zahra', 'Mohammed Hassan', 'Aisha Abdullah',
    'Omar Al Maktoum', 'Noura Al Qasimi', 'Khaled Al Mansouri', 'Sarah Al Najjar'
  ];

  return Array.from({ length: count }, (_, index) => {
    const submissionDate = new Date();
    submissionDate.setDate(submissionDate.getDate() - Math.floor(Math.random() * 90));

    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const requestedAmount = Math.floor(Math.random() * 50000) + 1000;
    const approvedAmount = status === 'approved' ?
      Math.floor(requestedAmount * (0.8 + Math.random() * 0.2)) : undefined;

    return {
      id: `req-${String(index + 1).padStart(6, '0')}`,
      requestNumber: `REQ-${new Date().getFullYear()}-${String(index + 1).padStart(6, '0')}`,
      memberId: `MEM-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`,
      memberName: members[Math.floor(Math.random() * members.length)],
      dateOfBirth: new Date(1970 + Math.floor(Math.random() * 40), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0],
      emiratesId: `784-${Math.floor(Math.random() * 9000) + 1000}-${Math.floor(Math.random() * 9000000) + 1000000}-${Math.floor(Math.random() * 90) + 10}`,

      providerId: `PROV-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      providerName: providers[Math.floor(Math.random() * providers.length)],
      providerType: Math.random() > 0.5 ? 'Hospital' : 'Clinic',
      facility: 'Main Campus',

      type: Math.random() > 0.3 ? 'authorization' : 'claim',
      status,
      priority: priorities[Math.floor(Math.random() * priorities.length)],
      submissionDate: submissionDate.toISOString(),
      processedDate: status !== 'pending' ? new Date(submissionDate.getTime() + Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : undefined,
      expiryDate: new Date(submissionDate.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString(),

      diagnosis: 'Primary diagnosis code',
      diagnosisCodes: [`ICD-${Math.floor(Math.random() * 900) + 100}`],
      procedure: services[Math.floor(Math.random() * services.length)],
      procedureCodes: [`CPT-${Math.floor(Math.random() * 90000) + 10000}`],
      serviceDescription: services[Math.floor(Math.random() * services.length)],

      requestedAmount,
      approvedAmount,
      currency: 'AED',

      format: formats[Math.floor(Math.random() * formats.length)],
      processingTime: Math.floor(Math.random() * 300) + 30,
      assignedTo: Math.random() > 0.5 ? 'Dr. Sarah Ahmed' : undefined,
      reviewedBy: status !== 'pending' ? 'Dr. Ahmed Hassan' : undefined,

      documents: [],

      createdAt: submissionDate.toISOString(),
      updatedAt: new Date().toISOString(),
      tags: [],
      notes: Math.random() > 0.7 ? 'Additional notes for this request' : '',
    };
  });
};

interface UseRequestHistoryReturn {
  requests: RequestHistoryItem[];
  total: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  filters: RequestFilters;
  hasFilters: boolean;
  updateSearch: (search: string) => void;
  updateFilters: (filters: Partial<RequestFilters['search']>) => void;
  updateSort: (sort: RequestFilters['sort']) => void;
  updatePagination: (pagination: Partial<RequestFilters['pagination']>) => void;
  clearFilters: () => void;
  exportRequests: (options: RequestExportOptions) => Promise<void>;
  performBulkOperation: (payload: BulkOperationPayload) => Promise<void>;
  fetchRequestDetails: (requestId: string) => Promise<any>;
  refresh: () => void;
}

const defaultFilters: RequestFilters = {
  search: {
    query: '',
  },
  sort: {
    field: 'submissionDate',
    direction: 'desc',
  },
  pagination: {
    page: 1,
    pageSize: 25,
  },
};

export function useRequestHistory(): UseRequestHistoryReturn {
  const [requests, setRequests] = useState<RequestHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<RequestFilters>(defaultFilters);

  // Debounce search query
  const [debouncedQuery] = useDebounce(filters.search.query, 300);

  // Calculate derived values
  const totalPages = useMemo(() => {
    return Math.ceil(total / filters.pagination.pageSize);
  }, [total, filters.pagination.pageSize]);

  const hasFilters = useMemo(() => {
    return !!(
      filters.search.query ||
      filters.search.status?.length ||
      filters.search.type?.length ||
      filters.search.priority?.length ||
      filters.search.dateRange ||
      filters.search.amountRange ||
      filters.search.providerId?.length ||
      filters.search.assignedTo?.length ||
      filters.search.tags?.length
    );
  }, [filters.search]);

  // Fetch requests function
  const fetchRequests = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // For development, use mock data
      const mockData = generateMockRequests(500);

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 300));

      // Apply client-side filtering for mock data
      let filteredData = mockData;

      // Search filter
      if (debouncedQuery) {
        const query = debouncedQuery.toLowerCase();
        filteredData = filteredData.filter(req =>
          req.requestNumber.toLowerCase().includes(query) ||
          req.memberName.toLowerCase().includes(query) ||
          req.providerName.toLowerCase().includes(query) ||
          req.serviceDescription.toLowerCase().includes(query) ||
          req.diagnosis.toLowerCase().includes(query)
        );
      }

      // Status filter
      if (filters.search.status?.length) {
        filteredData = filteredData.filter(req =>
          filters.search.status!.includes(req.status)
        );
      }

      // Type filter
      if (filters.search.type?.length) {
        filteredData = filteredData.filter(req =>
          filters.search.type!.includes(req.type)
        );
      }

      // Priority filter
      if (filters.search.priority?.length) {
        filteredData = filteredData.filter(req =>
          filters.search.priority!.includes(req.priority)
        );
      }

      // Date range filter
      if (filters.search.dateRange) {
        const { from, to } = filters.search.dateRange;
        filteredData = filteredData.filter(req => {
          const reqDate = new Date(req.submissionDate);
          return (!from || reqDate >= new Date(from)) && (!to || reqDate <= new Date(to));
        });
      }

      // Amount range filter
      if (filters.search.amountRange) {
        const { min, max } = filters.search.amountRange;
        filteredData = filteredData.filter(req =>
          (!min || req.requestedAmount >= min) && (!max || req.requestedAmount <= max)
        );
      }

      // Sort data
      filteredData.sort((a, b) => {
        const { field, direction } = filters.sort;
        const aValue = a[field];
        const bValue = b[field];

        let comparison = 0;
        if (aValue && bValue) {
          if (aValue < bValue) comparison = -1;
          if (aValue > bValue) comparison = 1;
        }

        return direction === 'desc' ? -comparison : comparison;
      });

      // Paginate data
      const startIndex = (filters.pagination.page - 1) * filters.pagination.pageSize;
      const paginatedData = filteredData.slice(startIndex, startIndex + filters.pagination.pageSize);

      setRequests(paginatedData);
      setTotal(filteredData.length);

      // In production, replace with actual API call:
      // const response = await requestHistoryService.getRequests(filters);
      // setRequests(response.data.requests);
      // setTotal(response.data.total);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch requests');
    } finally {
      setIsLoading(false);
    }
  }, [filters, debouncedQuery]);

  // Fetch requests when filters change
  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  // Update functions
  const updateSearch = useCallback((query: string) => {
    setFilters(prev => ({
      ...prev,
      search: { ...prev.search, query },
      pagination: { ...prev.pagination, page: 1 }, // Reset to first page
    }));
  }, []);

  const updateFilters = useCallback((newFilters: Partial<RequestFilters['search']>) => {
    setFilters(prev => ({
      ...prev,
      search: { ...prev.search, ...newFilters },
      pagination: { ...prev.pagination, page: 1 },
    }));
  }, []);

  const updateSort = useCallback((sort: RequestFilters['sort']) => {
    setFilters(prev => ({
      ...prev,
      sort,
      pagination: { ...prev.pagination, page: 1 },
    }));
  }, []);

  const updatePagination = useCallback((pagination: Partial<RequestFilters['pagination']>) => {
    setFilters(prev => ({
      ...prev,
      pagination: { ...prev.pagination, ...pagination },
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, []);

  const exportRequests = useCallback(async (options: RequestExportOptions) => {
    try {
      setIsLoading(true);
      await requestHistoryService.exportRequests(filters, options);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const performBulkOperation = useCallback(async (payload: BulkOperationPayload) => {
    try {
      setIsLoading(true);
      await requestHistoryService.performBulkOperation(payload);
      // Refresh data after bulk operation
      await fetchRequests();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bulk operation failed');
    } finally {
      setIsLoading(false);
    }
  }, [fetchRequests]);

  const fetchRequestDetails = useCallback(async (requestId: string) => {
    try {
      const request = await requestHistoryService.getRequestDetails(requestId);
      // Mock additional data for compatibility
      return {
        request,
        statusHistory: [],
        auditTrail: [],
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to fetch request details');
    }
  }, []);

  const refresh = useCallback(() => {
    fetchRequests();
  }, [fetchRequests]);

  return {
    requests,
    total,
    totalPages,
    isLoading,
    error,
    filters,
    hasFilters,
    updateSearch,
    updateFilters,
    updateSort,
    updatePagination,
    clearFilters,
    exportRequests,
    performBulkOperation,
    fetchRequestDetails,
    refresh,
  };
}

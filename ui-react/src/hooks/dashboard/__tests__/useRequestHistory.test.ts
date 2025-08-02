import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@/test/utils'
import { useRequestHistory } from '../useRequestHistory'
import { server, enableNetworkError, resetToDefaultHandlers } from '@/test/msw'

// Mock the service
const mockRequestHistoryService = {
  getRequests: vi.fn(),
  exportRequests: vi.fn(),
  performBulkOperation: vi.fn(),
  getRequestDetails: vi.fn()
}

vi.mock('@/services/requestHistoryService', () => ({
  requestHistoryService: mockRequestHistoryService
}))

// Start MSW server
import { beforeAll, afterAll } from 'vitest'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  vi.clearAllMocks()
})
afterAll(() => server.close())

describe('useRequestHistory Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    resetToDefaultHandlers()
  })

  it('initializes with default state', () => {
    const { result } = renderHook(() => useRequestHistory())

    expect(result.current.requests).toEqual([])
    expect(result.current.total).toBe(0)
    expect(result.current.totalPages).toBe(0)
    expect(result.current.isLoading).toBe(true) // Loading initially
    expect(result.current.error).toBe(null)
    expect(result.current.hasFilters).toBe(false)
  })

  it('loads mock data successfully', async () => {
    const { result } = renderHook(() => useRequestHistory())

    expect(result.current.isLoading).toBe(true)

    // Fast forward past the simulated API delay
    vi.advanceTimersByTime(300)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.requests).toHaveLength(25) // Default page size
    expect(result.current.total).toBe(500) // Total mock data count
    expect(result.current.totalPages).toBe(20) // 500 / 25
    expect(result.current.error).toBe(null)
  })

  it('updates search query and resets pagination', async () => {
    const { result } = renderHook(() => useRequestHistory())

    // Wait for initial load
    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Update search
    result.current.updateSearch('Ahmed')

    expect(result.current.filters.search.query).toBe('Ahmed')
    expect(result.current.filters.pagination.page).toBe(1)
    expect(result.current.hasFilters).toBe(true)
  })

  it('debounces search query', async () => {
    const { result } = renderHook(() => useRequestHistory())

    // Multiple rapid search updates
    result.current.updateSearch('A')
    result.current.updateSearch('Ah')
    result.current.updateSearch('Ahmed')

    // Only the last search should be applied after debounce
    expect(result.current.filters.search.query).toBe('Ahmed')

    // Fast forward past debounce delay
    vi.advanceTimersByTime(300)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('updates filters correctly', async () => {
    const { result } = renderHook(() => useRequestHistory())

    result.current.updateFilters({
      status: ['approved', 'pending'],
      type: ['authorization'],
      priority: ['high']
    })

    expect(result.current.filters.search.status).toEqual(['approved', 'pending'])
    expect(result.current.filters.search.type).toEqual(['authorization'])
    expect(result.current.filters.search.priority).toEqual(['high'])
    expect(result.current.filters.pagination.page).toBe(1)
    expect(result.current.hasFilters).toBe(true)
  })

  it('updates sorting', async () => {
    const { result } = renderHook(() => useRequestHistory())

    result.current.updateSort({
      field: 'requestedAmount',
      direction: 'asc'
    })

    expect(result.current.filters.sort.field).toBe('requestedAmount')
    expect(result.current.filters.sort.direction).toBe('asc')
    expect(result.current.filters.pagination.page).toBe(1)
  })

  it('updates pagination', () => {
    const { result } = renderHook(() => useRequestHistory())

    result.current.updatePagination({
      page: 3,
      pageSize: 50
    })

    expect(result.current.filters.pagination.page).toBe(3)
    expect(result.current.filters.pagination.pageSize).toBe(50)
  })

  it('clears all filters', () => {
    const { result } = renderHook(() => useRequestHistory())

    // Set some filters first
    result.current.updateSearch('test')
    result.current.updateFilters({ status: ['approved'] })

    expect(result.current.hasFilters).toBe(true)

    // Clear filters
    result.current.clearFilters()

    expect(result.current.filters.search.query).toBe('')
    expect(result.current.filters.search.status).toBeUndefined()
    expect(result.current.filters.pagination.page).toBe(1)
    expect(result.current.hasFilters).toBe(false)
  })

  it('calculates totalPages correctly', async () => {
    const { result } = renderHook(() => useRequestHistory())

    // Wait for initial load
    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.totalPages).toBe(20) // 500 / 25

    // Change page size
    result.current.updatePagination({ pageSize: 10 })

    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.totalPages).toBe(50) // 500 / 10
  })

  it('handles export requests', async () => {
    mockRequestHistoryService.exportRequests.mockResolvedValue(undefined)
    const { result } = renderHook(() => useRequestHistory())

    const exportOptions = {
      format: 'excel' as const,
      includeColumns: ['requestNumber', 'memberName'],
      includeFilters: true
    }

    await result.current.exportRequests(exportOptions)

    expect(mockRequestHistoryService.exportRequests).toHaveBeenCalledWith(
      result.current.filters,
      exportOptions
    )
  })

  it('handles export requests error', async () => {
    mockRequestHistoryService.exportRequests.mockRejectedValue(new Error('Export failed'))
    const { result } = renderHook(() => useRequestHistory())

    await result.current.exportRequests({
      format: 'csv',
      includeColumns: ['requestNumber'],
      includeFilters: false
    })

    expect(result.current.error).toBe('Export failed')
  })

  it('handles bulk operations', async () => {
    mockRequestHistoryService.performBulkOperation.mockResolvedValue(undefined)
    const { result } = renderHook(() => useRequestHistory())

    const bulkPayload = {
      action: 'approve' as const,
      requestIds: ['req-1', 'req-2'],
      data: { reason: 'Approved in bulk' }
    }

    await result.current.performBulkOperation(bulkPayload)

    expect(mockRequestHistoryService.performBulkOperation).toHaveBeenCalledWith(bulkPayload)
  })

  it('handles bulk operation errors', async () => {
    mockRequestHistoryService.performBulkOperation.mockRejectedValue(new Error('Bulk operation failed'))
    const { result } = renderHook(() => useRequestHistory())

    await result.current.performBulkOperation({
      action: 'deny',
      requestIds: ['req-1'],
      data: {}
    })

    expect(result.current.error).toBe('Bulk operation failed')
  })

  it('fetches request details', async () => {
    const mockRequest = { id: 'req-1', requestNumber: 'REQ-001' }
    mockRequestHistoryService.getRequestDetails.mockResolvedValue(mockRequest)

    const { result } = renderHook(() => useRequestHistory())

    const details = await result.current.fetchRequestDetails('req-1')

    expect(mockRequestHistoryService.getRequestDetails).toHaveBeenCalledWith('req-1')
    expect(details).toEqual({
      request: mockRequest,
      statusHistory: [],
      auditTrail: []
    })
  })

  it('handles request details error', async () => {
    mockRequestHistoryService.getRequestDetails.mockRejectedValue(new Error('Not found'))
    const { result } = renderHook(() => useRequestHistory())

    await expect(result.current.fetchRequestDetails('invalid-id')).rejects.toThrow('Not found')
  })

  it('refreshes data', async () => {
    const { result } = renderHook(() => useRequestHistory())

    // Wait for initial load
    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    const initialTotal = result.current.total

    // Call refresh
    result.current.refresh()

    expect(result.current.isLoading).toBe(true)

    vi.advanceTimersByTime(300)
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    // Data should be reloaded
    expect(result.current.total).toBe(initialTotal)
  })

  describe('filtering functionality', () => {
    it('filters by date range', async () => {
      const { result } = renderHook(() => useRequestHistory())

      const today = new Date()
      const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

      result.current.updateFilters({
        dateRange: {
          from: lastWeek.toISOString(),
          to: today.toISOString()
        }
      })

      expect(result.current.hasFilters).toBe(true)
    })

    it('filters by amount range', async () => {
      const { result } = renderHook(() => useRequestHistory())

      result.current.updateFilters({
        amountRange: {
          min: 1000,
          max: 10000
        }
      })

      expect(result.current.hasFilters).toBe(true)
    })
  })

  describe('error handling', () => {
    it('handles network errors gracefully', async () => {
      enableNetworkError()
      
      const { result } = renderHook(() => useRequestHistory())

      vi.advanceTimersByTime(300)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBeTruthy()
      })
    })
  })
})
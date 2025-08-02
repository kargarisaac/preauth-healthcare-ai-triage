import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { mockApiResponses, mockRequestHistoryItem, mockProcessingMetrics } from './mockData'

const API_BASE_URL = 'http://localhost:8000/api'

export const handlers = [
  // File processing endpoints
  http.post(`${API_BASE_URL}/process/eclaim`, async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return HttpResponse.json(mockApiResponses.processFile.error, { status: 400 })
    }

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 100))

    return HttpResponse.json(mockApiResponses.processFile.success)
  }),

  http.post(`${API_BASE_URL}/process/shafafiya`, async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return HttpResponse.json(mockApiResponses.processFile.error, { status: 400 })
    }

    return HttpResponse.json({
      ...mockApiResponses.processFile.success,
      result: {
        ...mockRequestHistoryItem,
        fileType: 'shafafiya'
      }
    })
  }),

  http.post(`${API_BASE_URL}/process/csv`, async ({ request }) => {
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return HttpResponse.json(mockApiResponses.processFile.error, { status: 400 })
    }

    return HttpResponse.json({
      ...mockApiResponses.processFile.success,
      result: {
        ...mockRequestHistoryItem,
        fileType: 'csv'
      }
    })
  }),

  // Request history endpoints
  http.get(`${API_BASE_URL}/requests`, ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const limit = parseInt(url.searchParams.get('limit') || '10')
    const search = url.searchParams.get('search')
    const status = url.searchParams.get('status')

    let items = [mockRequestHistoryItem]

    // Filter by search
    if (search) {
      items = items.filter(item =>
        item.fileName.toLowerCase().includes(search.toLowerCase()) ||
        item.metadata?.sender?.toLowerCase().includes(search.toLowerCase())
      )
    }

    // Filter by status
    if (status && status !== 'all') {
      items = items.filter(item => item.status === status)
    }

    return HttpResponse.json({
      items: items.slice((page - 1) * limit, page * limit),
      total: items.length,
      page,
      limit
    })
  }),

  http.get(`${API_BASE_URL}/requests/:id`, ({ params }) => {
    const { id } = params

    if (id === mockRequestHistoryItem.id) {
      return HttpResponse.json(mockRequestHistoryItem)
    }

    return HttpResponse.json({ error: 'Request not found' }, { status: 404 })
  }),

  // Analytics endpoints
  http.get(`${API_BASE_URL}/analytics/metrics`, () => {
    return HttpResponse.json(mockProcessingMetrics)
  }),

  http.get(`${API_BASE_URL}/analytics/charts`, () => {
    return HttpResponse.json(mockApiResponses.analytics.charts)
  }),

  // Member search endpoints
  http.get(`${API_BASE_URL}/members/search`, ({ request }) => {
    const url = new URL(request.url)
    const query = url.searchParams.get('q')

    if (!query) {
      return HttpResponse.json({ members: [] })
    }

    // Simulate member search results
    const members = [
      {
        id: 'member-1',
        name: 'Ahmed Al-Mansouri',
        emiratesId: '784-1990-1234567-1',
        policyNumber: 'POL-2024-001'
      }
    ].filter(member =>
      member.name.toLowerCase().includes(query.toLowerCase()) ||
      member.emiratesId.includes(query) ||
      member.policyNumber.includes(query)
    )

    return HttpResponse.json({ members })
  }),

  // Health check
  http.get(`${API_BASE_URL}/health`, () => {
    return HttpResponse.json({ status: 'healthy', timestamp: new Date().toISOString() })
  })
]

// Error handlers for testing error scenarios
export const errorHandlers = [
  http.post(`${API_BASE_URL}/process/eclaim`, () => {
    return HttpResponse.json(
      { error: 'Internal server error', code: 'INTERNAL_ERROR' },
      { status: 500 }
    )
  }),

  http.get(`${API_BASE_URL}/requests`, () => {
    return HttpResponse.json(
      { error: 'Service unavailable' },
      { status: 503 }
    )
  })
]

// Setup MSW server
export const server = setupServer(...handlers)

// Utility functions for tests
export const enableNetworkError = () => {
  server.use(...errorHandlers)
}

export const resetToDefaultHandlers = () => {
  server.resetHandlers(...handlers)
}

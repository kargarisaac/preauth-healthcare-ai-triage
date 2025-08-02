import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server, resetToDefaultHandlers, enableNetworkError } from './msw'

// Start server for integration tests
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('API Integration Tests', () => {
  describe('File Processing API', () => {
    it('should process eClaimLink XML file successfully', async () => {
      const formData = new FormData()
      const testFile = new File(['<test>data</test>'], 'test-claim.xml', { type: 'text/xml' })
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('status', 'completed')
      expect(result).toHaveProperty('result')
      expect(result.result).toHaveProperty('fileType', 'xml')
    })

    it('should process Shafafiya XML file successfully', async () => {
      const formData = new FormData()
      const testFile = new File(['<shafafiya>data</shafafiya>'], 'test-shafafiya.xml', { type: 'text/xml' })
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/process/shafafiya', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('status', 'completed')
      expect(result.result).toHaveProperty('fileType', 'shafafiya')
    })

    it('should process CSV file successfully', async () => {
      const formData = new FormData()
      const testFile = new File(['name,age\nJohn,30'], 'test-data.csv', { type: 'text/csv' })
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/process/csv', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('status', 'completed')
      expect(result.result).toHaveProperty('fileType', 'csv')
    })

    it('should return error for missing file', async () => {
      const formData = new FormData()
      // Don't append file

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(false)
      expect(response.status).toBe(400)

      const result = await response.json()
      expect(result).toHaveProperty('error')
    })

    it('should handle server errors gracefully', async () => {
      enableNetworkError()

      const formData = new FormData()
      const testFile = new File(['<test>data</test>'], 'test.xml', { type: 'text/xml' })
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)

      resetToDefaultHandlers()
    })
  })

  describe('Request History API', () => {
    it('should fetch request history with pagination', async () => {
      const response = await fetch('http://localhost:8000/api/requests?page=1&limit=10')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('total')
      expect(result).toHaveProperty('page', 1)
      expect(result).toHaveProperty('limit', 10)
      expect(Array.isArray(result.items)).toBe(true)
    })

    it('should search requests by query', async () => {
      const response = await fetch('http://localhost:8000/api/requests?search=ahmed')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('items')
      expect(Array.isArray(result.items)).toBe(true)
    })

    it('should filter requests by status', async () => {
      const response = await fetch('http://localhost:8000/api/requests?status=approved')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('items')
      expect(Array.isArray(result.items)).toBe(true)
    })

    it('should fetch individual request details', async () => {
      const response = await fetch('http://localhost:8000/api/requests/test-request-1')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('id', 'test-request-1')
      expect(result).toHaveProperty('fileName')
      expect(result).toHaveProperty('status')
    })

    it('should return 404 for non-existent request', async () => {
      const response = await fetch('http://localhost:8000/api/requests/non-existent-id')

      expect(response.ok).toBe(false)
      expect(response.status).toBe(404)
    })

    it('should handle service unavailable errors', async () => {
      enableNetworkError()

      const response = await fetch('http://localhost:8000/api/requests')

      expect(response.ok).toBe(false)
      expect(response.status).toBe(503)

      resetToDefaultHandlers()
    })
  })

  describe('Analytics API', () => {
    it('should fetch processing metrics', async () => {
      const response = await fetch('http://localhost:8000/api/analytics/metrics')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('totalFiles')
      expect(result).toHaveProperty('successfulFiles')
      expect(result).toHaveProperty('failedFiles')
      expect(result).toHaveProperty('averageProcessingTime')
    })

    it('should fetch chart data', async () => {
      const response = await fetch('http://localhost:8000/api/analytics/charts')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('dailyProcessing')
      expect(result).toHaveProperty('processingTimes')
      expect(result).toHaveProperty('errorDistribution')
      expect(Array.isArray(result.dailyProcessing)).toBe(true)
    })
  })

  describe('Member Search API', () => {
    it('should search members by query', async () => {
      const response = await fetch('http://localhost:8000/api/members/search?q=ahmed')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('members')
      expect(Array.isArray(result.members)).toBe(true)
    })

    it('should return empty results for no query', async () => {
      const response = await fetch('http://localhost:8000/api/members/search')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('members', [])
    })

    it('should search by Emirates ID', async () => {
      const response = await fetch('http://localhost:8000/api/members/search?q=784-1990')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('members')
      expect(Array.isArray(result.members)).toBe(true)
    })

    it('should search by policy number', async () => {
      const response = await fetch('http://localhost:8000/api/members/search?q=POL-2024')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('members')
      expect(Array.isArray(result.members)).toBe(true)
    })
  })

  describe('Health Check API', () => {
    it('should return healthy status', async () => {
      const response = await fetch('http://localhost:8000/api/health')

      expect(response.ok).toBe(true)
      const result = await response.json()

      expect(result).toHaveProperty('status', 'healthy')
      expect(result).toHaveProperty('timestamp')
    })
  })

  describe('Error Handling', () => {
    it('should handle network timeouts', async () => {
      // Simulate timeout by using an invalid URL
      const timeoutPromise = fetch('http://localhost:9999/api/timeout', {
        signal: AbortSignal.timeout(1000)
      })

      await expect(timeoutPromise).rejects.toThrow()
    })

    it('should handle malformed responses', async () => {
      // Test with endpoint that returns invalid JSON
      server.use(
        http.get('http://localhost:8000/api/malformed', () => {
          return new Response('invalid json response', {
            headers: { 'Content-Type': 'application/json' }
          })
        })
      )

      const response = await fetch('http://localhost:8000/api/malformed')
      expect(response.ok).toBe(true)

      // Should throw when trying to parse invalid JSON
      await expect(response.json()).rejects.toThrow()
    })

    it('should handle CORS errors', async () => {
      // Test cross-origin request
      const response = await fetch('http://different-origin.com/api/test')
        .catch(error => error)

      expect(response).toBeInstanceOf(Error)
    })
  })

  describe('File Upload Edge Cases', () => {
    it('should handle empty files', async () => {
      const formData = new FormData()
      const emptyFile = new File([''], 'empty.xml', { type: 'text/xml' })
      formData.append('file', emptyFile)

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      // Should still process successfully (handled by backend)
      expect(response.ok).toBe(true)
    })

    it('should handle large files', async () => {
      const formData = new FormData()
      const largeContent = 'x'.repeat(1024 * 1024) // 1MB file
      const largeFile = new File([largeContent], 'large.xml', { type: 'text/xml' })
      formData.append('file', largeFile)

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(true)
    })

    it('should handle special characters in filenames', async () => {
      const formData = new FormData()
      const testFile = new File(['<test>data</test>'], 'test-file-with-spaces and 特殊字符.xml', { type: 'text/xml' })
      formData.append('file', testFile)

      const response = await fetch('http://localhost:8000/api/process/eclaim', {
        method: 'POST',
        body: formData,
      })

      expect(response.ok).toBe(true)
    })
  })
})

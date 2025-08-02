import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import Toast from '../Toast'
import type { ToastMessage } from '@/types/ui'

// Mock the ToastContext
const mockRemoveToast = vi.fn()
vi.mock('@contexts/ToastContext', () => ({
  useToast: () => ({
    removeToast: mockRemoveToast
  })
}))

describe('Toast Component', () => {
  let mockToast: ToastMessage

  beforeEach(() => {
    vi.useFakeTimers()
    mockToast = {
      id: 'test-toast-1',
      type: 'info',
      title: 'Test Title',
      message: 'Test message content',
      duration: 5000
    }
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('renders toast with title and message', () => {
    render(<Toast toast={mockToast} />)
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test message content')).toBeInTheDocument()
  })

  it('has proper ARIA role', () => {
    render(<Toast toast={mockToast} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('renders close button', () => {
    render(<Toast toast={mockToast} />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('calls removeToast when close button is clicked', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    render(<Toast toast={mockToast} />)

    await user.click(screen.getByRole('button'))
    expect(mockRemoveToast).toHaveBeenCalledWith('test-toast-1')
  })

  it('auto-removes toast after duration', async () => {
    render(<Toast toast={mockToast} />)

    vi.advanceTimersByTime(5000)

    await waitFor(() => {
      expect(mockRemoveToast).toHaveBeenCalledWith('test-toast-1')
    })
  })

  it('uses custom duration when provided', async () => {
    const customToast = { ...mockToast, duration: 3000 }
    render(<Toast toast={customToast} />)

    vi.advanceTimersByTime(2999)
    expect(mockRemoveToast).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)

    await waitFor(() => {
      expect(mockRemoveToast).toHaveBeenCalledWith('test-toast-1')
    })
  })

  it('uses default duration when not provided', async () => {
    const { duration, ...toastWithoutDuration } = mockToast
    render(<Toast toast={toastWithoutDuration} />)

    vi.advanceTimersByTime(4999)
    expect(mockRemoveToast).not.toHaveBeenCalled()

    vi.advanceTimersByTime(1)

    await waitFor(() => {
      expect(mockRemoveToast).toHaveBeenCalledWith('test-toast-1')
    })
  })

  describe('toast types and icons', () => {
    it('renders success toast with check icon', () => {
      const successToast = { ...mockToast, type: 'success' as const }
      render(<Toast toast={successToast} />)

      const toast = screen.getByRole('alert')
      expect(toast).toHaveClass('toast-success')

      // CheckCircle icon should be present
      const icon = document.querySelector('.text-success-500')
      expect(icon).toBeInTheDocument()
    })

    it('renders error toast with alert icon', () => {
      const errorToast = { ...mockToast, type: 'error' as const }
      render(<Toast toast={errorToast} />)

      const toast = screen.getByRole('alert')
      expect(toast).toHaveClass('toast-error')

      // AlertCircle icon should be present
      const icon = document.querySelector('.text-error-500')
      expect(icon).toBeInTheDocument()
    })

    it('renders warning toast with triangle icon', () => {
      const warningToast = { ...mockToast, type: 'warning' as const }
      render(<Toast toast={warningToast} />)

      const toast = screen.getByRole('alert')
      expect(toast).toHaveClass('toast-warning')

      // AlertTriangle icon should be present
      const icon = document.querySelector('.text-warning-500')
      expect(icon).toBeInTheDocument()
    })

    it('renders info toast with info icon', () => {
      const infoToast = { ...mockToast, type: 'info' as const }
      render(<Toast toast={infoToast} />)

      const toast = screen.getByRole('alert')
      expect(toast).toHaveClass('toast-info')

      // Info icon should be present
      const icon = document.querySelector('.text-blue-500')
      expect(icon).toBeInTheDocument()
    })
  })

  it('applies proper CSS classes', () => {
    render(<Toast toast={mockToast} />)
    const toast = screen.getByRole('alert')
    expect(toast).toHaveClass('toast', 'animate-slide-in', 'toast-info')
  })

  it('has proper layout structure', () => {
    render(<Toast toast={mockToast} />)

    // Check for flex container
    const flexContainer = document.querySelector('.flex.items-start')
    expect(flexContainer).toBeInTheDocument()

    // Check for icon container
    const iconContainer = document.querySelector('.flex-shrink-0')
    expect(iconContainer).toBeInTheDocument()

    // Check for content container
    const contentContainer = document.querySelector('.ml-3.flex-1')
    expect(contentContainer).toBeInTheDocument()
  })

  describe('accessibility', () => {
    it('has proper focus management on close button', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
      render(<Toast toast={mockToast} />)

      const closeButton = screen.getByRole('button')
      expect(closeButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-gray-500')

      await user.tab()
      expect(closeButton).toHaveFocus()
    })

    it('provides semantic structure for screen readers', () => {
      render(<Toast toast={mockToast} />)

      const title = screen.getByText('Test Title')
      expect(title).toHaveClass('text-sm', 'font-medium', 'text-gray-900')

      const message = screen.getByText('Test message content')
      expect(message).toHaveClass('text-sm', 'text-gray-600', 'mt-1')
    })
  })

  describe('cleanup', () => {
    it('clears timeout when component unmounts', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')
      const { unmount } = render(<Toast toast={mockToast} />)

      unmount()
      expect(clearTimeoutSpy).toHaveBeenCalled()
    })

    it('resets timer when toast changes', () => {
      const { rerender } = render(<Toast toast={mockToast} />)

      const newToast = { ...mockToast, id: 'new-toast', duration: 3000 }
      rerender(<Toast toast={newToast} />)

      vi.advanceTimersByTime(3000)

      await waitFor(() => {
        expect(mockRemoveToast).toHaveBeenCalledWith('new-toast')
      })
    })
  })
})

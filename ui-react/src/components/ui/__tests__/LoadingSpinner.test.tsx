import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import LoadingSpinner from '../LoadingSpinner'

describe('LoadingSpinner Component', () => {
  it('renders without message', () => {
    render(<LoadingSpinner />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toBeInTheDocument()
  })

  it('renders with message', () => {
    render(<LoadingSpinner message="Loading data..." />)
    expect(screen.getByText('Loading data...')).toBeInTheDocument()
  })

  it('applies default medium size', () => {
    render(<LoadingSpinner />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveClass('w-8', 'h-8')
  })

  it('applies small size when specified', () => {
    render(<LoadingSpinner size="sm" />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveClass('w-4', 'h-4')
  })

  it('applies large size when specified', () => {
    render(<LoadingSpinner size="lg" />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveClass('w-12', 'h-12')
  })

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-spinner" />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveClass('custom-spinner')
  })

  it('has proper spinner classes', () => {
    render(<LoadingSpinner />)
    const spinner = screen.getByTestId('loading-spinner')
    expect(spinner).toHaveClass('spinner', 'border-2', 'border-gray-200', 'border-t-primary-500')
  })

  it('renders message with correct styling', () => {
    render(<LoadingSpinner message="Please wait..." />)
    const message = screen.getByText('Please wait...')
    expect(message).toHaveClass('mt-4', 'text-sm', 'text-gray-600', 'text-center')
  })

  it('centers content properly', () => {
    render(<LoadingSpinner message="Loading..." />)
    const container = document.querySelector('.flex.flex-col.items-center.justify-center.p-8')
    expect(container).toBeInTheDocument()
  })

  it('does not render message element when no message provided', () => {
    render(<LoadingSpinner />)
    expect(screen.queryByText(/./)).not.toBeInTheDocument()
    expect(document.querySelector('p')).not.toBeInTheDocument()
  })

  describe('accessibility', () => {
    it('provides appropriate loading indication', () => {
      render(<LoadingSpinner message="Loading content..." />)
      const spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveAttribute('role', 'status')
      expect(spinner).toHaveAttribute('aria-label', 'Loading')
    })

    it('message is readable by screen readers', () => {
      render(<LoadingSpinner message="Processing your request..." />)
      const message = screen.getByText('Processing your request...')
      expect(message).toBeInTheDocument()
    })
  })

  describe('size variations', () => {
    it('maintains aspect ratio across all sizes', () => {
      const { rerender } = render(<LoadingSpinner size="sm" />)
      let spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('w-4', 'h-4')

      rerender(<LoadingSpinner size="md" />)
      spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('w-8', 'h-8')

      rerender(<LoadingSpinner size="lg" />)
      spinner = screen.getByTestId('loading-spinner')
      expect(spinner).toHaveClass('w-12', 'h-12')
    })
  })
})
import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import Card from '../Card'

describe('Card Component', () => {
  it('renders children content', () => {
    render(
      <Card>
        <div>Card Content</div>
      </Card>
    )
    expect(screen.getByText('Card Content')).toBeInTheDocument()
  })

  it('renders with title only', () => {
    render(
      <Card title="Test Card">
        <div>Content</div>
      </Card>
    )
    expect(screen.getByText('Test Card')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test Card' })).toBeInTheDocument()
  })

  it('renders with subtitle only', () => {
    render(
      <Card subtitle="Test Subtitle">
        <div>Content</div>
      </Card>
    )
    expect(screen.getByText('Test Subtitle')).toBeInTheDocument()
  })

  it('renders with both title and subtitle', () => {
    render(
      <Card title="Test Card" subtitle="Test Subtitle">
        <div>Content</div>
      </Card>
    )
    expect(screen.getByText('Test Card')).toBeInTheDocument()
    expect(screen.getByText('Test Subtitle')).toBeInTheDocument()
  })

  it('does not render header when no title or subtitle', () => {
    render(
      <Card>
        <div>Content only</div>
      </Card>
    )
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    expect(document.querySelector('.card-header')).not.toBeInTheDocument()
  })

  it('applies base card classes', () => {
    render(
      <Card>
        <div>Content</div>
      </Card>
    )
    const cardElement = document.querySelector('.card')
    expect(cardElement).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(
      <Card className="custom-card-class">
        <div>Content</div>
      </Card>
    )
    const cardElement = document.querySelector('.card')
    expect(cardElement).toHaveClass('custom-card-class')
  })

  it('applies default medium padding', () => {
    render(
      <Card>
        <div>Content</div>
      </Card>
    )
    const cardBody = document.querySelector('.card-body')
    expect(cardBody).toHaveClass('p-6')
  })

  it('applies small padding when specified', () => {
    render(
      <Card padding="sm">
        <div>Content</div>
      </Card>
    )
    const cardBody = document.querySelector('.card-body')
    expect(cardBody).toHaveClass('p-4')
  })

  it('applies large padding when specified', () => {
    render(
      <Card padding="lg">
        <div>Content</div>
      </Card>
    )
    const cardBody = document.querySelector('.card-body')
    expect(cardBody).toHaveClass('p-8')
  })

  it('renders header with proper structure', () => {
    render(
      <Card title="Test Title" subtitle="Test Subtitle">
        <div>Content</div>
      </Card>
    )
    
    const header = document.querySelector('.card-header')
    expect(header).toBeInTheDocument()
    
    const title = screen.getByRole('heading')
    expect(title).toHaveClass('text-lg', 'font-semibold', 'text-gray-900')
    
    const subtitle = screen.getByText('Test Subtitle')
    expect(subtitle).toHaveClass('text-sm', 'text-gray-600', 'mt-1')
  })

  it('maintains proper content structure', () => {
    render(
      <Card title="Card Title">
        <p>Paragraph content</p>
        <button>Action Button</button>
      </Card>
    )
    
    const cardBody = document.querySelector('.card-body')
    expect(cardBody).toBeInTheDocument()
    expect(screen.getByText('Paragraph content')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Action Button' })).toBeInTheDocument()
  })

  describe('responsive behavior', () => {
    it('handles long titles appropriately', () => {
      const longTitle = 'This is a very long title that should wrap properly on smaller screens'
      render(
        <Card title={longTitle}>
          <div>Content</div>
        </Card>
      )
      expect(screen.getByText(longTitle)).toBeInTheDocument()
    })

    it('handles complex content structures', () => {
      render(
        <Card title="Complex Card">
          <div className="grid grid-cols-2 gap-4">
            <div>Left content</div>
            <div>Right content</div>
          </div>
          <div className="mt-4">
            <button>Primary Action</button>
            <button>Secondary Action</button>
          </div>
        </Card>
      )
      
      expect(screen.getByText('Left content')).toBeInTheDocument()
      expect(screen.getByText('Right content')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Primary Action' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Secondary Action' })).toBeInTheDocument()
    })
  })
})
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Accordion from '../Accordion'
import type { AccordionItem } from '../Accordion'
import { Heart, Pill, AlertTriangle } from 'lucide-react'

describe('Accordion Component', () => {
  let mockItems: AccordionItem[]
  let mockOnExpandedChange: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnExpandedChange = vi.fn()
    mockItems = [
      {
        id: 'conditions',
        title: 'Active Conditions',
        content: <div>Condition details</div>,
        icon: Heart,
        badge: 3,
        badgeVariant: 'error' as const,
        metadata: {
          priority: 'high' as const,
          status: 'current' as const,
          category: 'condition' as const,
          lastUpdated: new Date('2023-01-01')
        }
      },
      {
        id: 'medications',
        title: 'Current Medications',
        content: <div>Medication list</div>,
        icon: Pill,
        badge: 5,
        defaultExpanded: true,
        metadata: {
          priority: 'medium' as const,
          status: 'current' as const,
          category: 'medication' as const
        }
      },
      {
        id: 'allergies',
        title: 'Known Allergies',
        content: <div>Allergy information</div>,
        disabled: true,
        metadata: {
          priority: 'critical' as const,
          status: 'requires_review' as const,
          category: 'allergy' as const
        }
      }
    ]
  })

  it('renders accordion items with titles', () => {
    render(<Accordion items={mockItems} />)
    
    expect(screen.getByText('Active Conditions')).toBeInTheDocument()
    expect(screen.getByText('Current Medications')).toBeInTheDocument()
    expect(screen.getByText('Known Allergies')).toBeInTheDocument()
  })

  it('shows content when expanded', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} />)
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    await user.click(conditionsButton)
    
    expect(screen.getByText('Condition details')).toBeInTheDocument()
  })

  it('hides content when collapsed', () => {
    render(<Accordion items={mockItems} />)
    
    expect(screen.queryByText('Condition details')).not.toBeInTheDocument()
  })

  it('handles default expanded items', () => {
    render(<Accordion items={mockItems} defaultExpanded={['conditions']} />)
    
    expect(screen.getByText('Condition details')).toBeInTheDocument()
  })

  it('calls onExpandedChange when item is toggled', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} onExpandedChange={mockOnExpandedChange} />)
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    await user.click(conditionsButton)
    
    expect(mockOnExpandedChange).toHaveBeenCalledWith(['conditions'])
  })

  it('allows multiple items to be expanded when allowMultiple is true', async () => {
    const user = userEvent.setup()
    render(
      <Accordion 
        items={mockItems} 
        allowMultiple 
        onExpandedChange={mockOnExpandedChange} 
      />
    )
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    const medicationsButton = screen.getByRole('button', { name: /current medications/i })
    
    await user.click(conditionsButton)
    await user.click(medicationsButton)
    
    expect(mockOnExpandedChange).toHaveBeenLastCalledWith(['conditions', 'medications'])
  })

  it('collapses other items when allowMultiple is false', async () => {
    const user = userEvent.setup()
    render(
      <Accordion 
        items={mockItems} 
        allowMultiple={false}
        defaultExpanded={['conditions']}
        onExpandedChange={mockOnExpandedChange} 
      />
    )
    
    const medicationsButton = screen.getByRole('button', { name: /current medications/i })
    await user.click(medicationsButton)
    
    expect(mockOnExpandedChange).toHaveBeenLastCalledWith(['medications'])
  })

  it('does not toggle disabled items', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} onExpandedChange={mockOnExpandedChange} />)
    
    const allergiesButton = screen.getByRole('button', { name: /known allergies/i })
    await user.click(allergiesButton)
    
    expect(mockOnExpandedChange).not.toHaveBeenCalled()
    expect(screen.queryByText('Allergy information')).not.toBeInTheDocument()
  })

  it('renders icons when provided', () => {
    render(<Accordion items={mockItems} />)
    
    // Check for heart icon (conditions) and pill icon (medications)
    const icons = document.querySelectorAll('svg')
    expect(icons.length).toBeGreaterThan(0)
  })

  it('renders badges with correct styling', () => {
    render(<Accordion items={mockItems} />)
    
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    
    const errorBadge = screen.getByText('3').closest('span')
    expect(errorBadge).toHaveClass('bg-error-100', 'text-error-700')
  })

  it('shows priority indicators when enabled', () => {
    render(<Accordion items={mockItems} showPriorityIndicators />)
    
    // Should show priority icons for high, medium, and critical priorities
    const priorityIcons = document.querySelectorAll('[aria-label*="Priority:"]')
    expect(priorityIcons).toHaveLength(3)
  })

  it('shows status indicators when enabled', () => {
    render(<Accordion items={mockItems} showStatusIndicators />)
    
    const statusIcons = document.querySelectorAll('[aria-label*="Status:"]')
    expect(statusIcons).toHaveLength(3)
  })

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} />)
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    conditionsButton.focus()
    
    // Enter should expand
    await user.keyboard('{Enter}')
    expect(screen.getByText('Condition details')).toBeInTheDocument()
    
    // Space should collapse
    await user.keyboard(' ')
    expect(screen.queryByText('Condition details')).not.toBeInTheDocument()
  })

  it('handles arrow key navigation', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} />)
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    conditionsButton.focus()
    
    // Arrow down should focus next item
    await user.keyboard('{ArrowDown}')
    
    const medicationsButton = screen.getByRole('button', { name: /current medications/i })
    expect(medicationsButton).toHaveFocus()
  })

  it('handles Home and End keys', async () => {
    const user = userEvent.setup()
    render(<Accordion items={mockItems} />)
    
    const medicationsButton = screen.getByRole('button', { name: /current medications/i })
    medicationsButton.focus()
    
    // Home should focus first item
    await user.keyboard('{Home}')
    
    const conditionsButton = screen.getByRole('button', { name: /active conditions/i })
    expect(conditionsButton).toHaveFocus()
    
    // End should focus last item
    await user.keyboard('{End}')
    
    const allergiesButton = screen.getByRole('button', { name: /known allergies/i })
    expect(allergiesButton).toHaveFocus()
  })

  it('applies correct variant styling', () => {
    const { rerender } = render(<Accordion items={mockItems} variant="bordered" />)
    
    let accordionItems = document.querySelectorAll('[class*="border-gray-300"]')
    expect(accordionItems.length).toBeGreaterThan(0)
    
    rerender(<Accordion items={mockItems} variant="filled" />)
    
    accordionItems = document.querySelectorAll('[class*="bg-gray-50"]')
    expect(accordionItems.length).toBeGreaterThan(0)
  })

  it('applies correct size styling', () => {
    const { rerender } = render(<Accordion items={mockItems} size="sm" />)
    
    let buttons = document.querySelectorAll('[class*="px-3"][class*="py-2"]')
    expect(buttons.length).toBeGreaterThan(0)
    
    rerender(<Accordion items={mockItems} size="lg" />)
    
    buttons = document.querySelectorAll('[class*="px-6"][class*="py-4"]')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('shows loading state', () => {
    render(<Accordion items={mockItems} loading />)
    
    const loadingElements = document.querySelectorAll('.animate-pulse')
    expect(loadingElements.length).toBeGreaterThan(0)
    
    // Should not show actual items when loading
    expect(screen.queryByText('Active Conditions')).not.toBeInTheDocument()
  })

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<Accordion items={mockItems} />)
      
      const region = screen.getByRole('region', { name: /medical information sections/i })
      expect(region).toBeInTheDocument()
      
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-expanded')
        expect(button).toHaveAttribute('aria-controls')
      })
    })

    it('provides metadata in screen reader accessible format', () => {
      render(<Accordion items={mockItems} />)
      
      const metadataElements = document.querySelectorAll('.sr-only')
      expect(metadataElements.length).toBeGreaterThan(0)
      
      // Check for metadata content
      const metadataText = Array.from(metadataElements).map(el => el.textContent).join(' ')
      expect(metadataText).toContain('Priority: high')
      expect(metadataText).toContain('Status: current')
      expect(metadataText).toContain('Category: condition')
    })

    it('handles disabled state with proper ARIA', async () => {
      const user = userEvent.setup()
      render(<Accordion items={mockItems} />)
      
      const allergiesButton = screen.getByRole('button', { name: /known allergies/i })
      expect(allergiesButton).toHaveAttribute('disabled')
      expect(allergiesButton).toHaveClass('opacity-50', 'cursor-not-allowed')
      
      // Should not respond to keyboard events
      await user.keyboard('{Enter}')
      expect(screen.queryByText('Allergy information')).not.toBeInTheDocument()
    })
  })

  describe('controlled mode', () => {
    it('uses controlled expanded state', async () => {
      const user = userEvent.setup()
      const { rerender } = render(
        <Accordion 
          items={mockItems} 
          expanded={['conditions']} 
          onExpandedChange={mockOnExpandedChange} 
        />
      )
      
      expect(screen.getByText('Condition details')).toBeInTheDocument()
      
      rerender(
        <Accordion 
          items={mockItems} 
          expanded={[]} 
          onExpandedChange={mockOnExpandedChange} 
        />
      )
      
      expect(screen.queryByText('Condition details')).not.toBeInTheDocument()
    })
  })

  describe('healthcare-specific features', () => {
    it('displays medical priority levels correctly', () => {
      render(<Accordion items={mockItems} showPriorityIndicators />)
      
      // Check for different priority indicators
      expect(document.querySelector('[aria-label="Priority: high"]')).toBeInTheDocument()
      expect(document.querySelector('[aria-label="Priority: medium"]')).toBeInTheDocument()
      expect(document.querySelector('[aria-label="Priority: critical"]')).toBeInTheDocument()
    })

    it('displays medical status indicators correctly', () => {
      render(<Accordion items={mockItems} showStatusIndicators />)
      
      expect(document.querySelector('[aria-label="Status: current"]')).toBeInTheDocument()
      expect(document.querySelector('[aria-label="Status: requires_review"]')).toBeInTheDocument()
    })

    it('handles medical categories in metadata', () => {
      render(<Accordion items={mockItems} />)
      
      const metadataElements = document.querySelectorAll('.sr-only')
      const metadataText = Array.from(metadataElements).map(el => el.textContent).join(' ')
      
      expect(metadataText).toContain('Category: condition')
      expect(metadataText).toContain('Category: medication')
      expect(metadataText).toContain('Category: allergy')
    })
  })
})
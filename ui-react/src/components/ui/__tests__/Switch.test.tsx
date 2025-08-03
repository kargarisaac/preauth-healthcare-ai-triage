import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Switch from '../Switch'
import { Check, X } from 'lucide-react'

describe('Switch Component', () => {
  let mockOnChange: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnChange = vi.fn()
  })

  it('renders switch without label', () => {
    render(<Switch checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toBeInTheDocument()
    expect(switchElement).toHaveAttribute('aria-checked', 'false')
  })

  it('renders switch with label and description', () => {
    render(
      <Switch 
        label="Enable notifications"
        description="Receive alerts for important updates"
        checked={false} 
        onChange={mockOnChange} 
      />
    )
    
    expect(screen.getByText('Enable notifications')).toBeInTheDocument()
    expect(screen.getByText('Receive alerts for important updates')).toBeInTheDocument()
  })

  it('handles checked state correctly', () => {
    const { rerender } = render(<Switch checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveAttribute('aria-checked', 'false')
    
    rerender(<Switch checked={true} onChange={mockOnChange} />)
    expect(switchElement).toHaveAttribute('aria-checked', 'true')
  })

  it('calls onChange when clicked', async () => {
    const user = userEvent.setup()
    render(<Switch label="Test switch" checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    await user.click(switchElement)
    
    expect(mockOnChange).toHaveBeenCalledWith(true)
  })

  it('handles uncontrolled mode with defaultChecked', async () => {
    const user = userEvent.setup()
    render(<Switch label="Uncontrolled switch" defaultChecked={true} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveAttribute('aria-checked', 'true')
    
    await user.click(switchElement)
    expect(mockOnChange).toHaveBeenCalledWith(false)
  })

  it('handles disabled state correctly', async () => {
    const user = userEvent.setup()
    render(<Switch label="Disabled switch" disabled checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toBeDisabled()
    expect(switchElement).toHaveClass('cursor-not-allowed', 'opacity-50')
    
    // Should not call onChange when disabled
    await user.click(switchElement)
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('handles loading state correctly', async () => {
    const user = userEvent.setup()
    render(<Switch label="Loading switch" loading checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('cursor-wait')
    
    // Should show loading spinner
    const spinner = document.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
    
    // Should not call onChange when loading
    await user.click(switchElement)
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup()
    render(<Switch label="Keyboard switch" checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    
    // Focus the switch
    await user.tab()
    expect(switchElement).toHaveFocus()
    
    // Space should toggle
    await user.keyboard(' ')
    expect(mockOnChange).toHaveBeenCalledWith(true)
    
    // Enter should also toggle
    await user.keyboard('{Enter}')
    expect(mockOnChange).toHaveBeenCalledWith(true)
  })

  it('applies correct size styling', () => {
    const { rerender } = render(<Switch size="sm" checked={false} onChange={mockOnChange} />)
    
    let switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('w-9', 'h-5')
    
    rerender(<Switch size="lg" checked={false} onChange={mockOnChange} />)
    
    switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('w-14', 'h-8')
  })

  it('applies correct variant styling when checked', () => {
    const { rerender } = render(<Switch variant="success" checked={true} onChange={mockOnChange} />)
    
    let switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('bg-success-500')
    
    rerender(<Switch variant="error" checked={true} onChange={mockOnChange} />)
    
    switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('bg-error-500')
  })

  it('shows unchecked styling when not checked', () => {
    render(<Switch variant="success" checked={false} onChange={mockOnChange} />)
    
    const switchElement = screen.getByRole('switch')
    expect(switchElement).toHaveClass('bg-gray-200')
    expect(switchElement).not.toHaveClass('bg-success-500')
  })

  it('renders custom icons', () => {
    render(
      <Switch 
        checked={true}
        checkedIcon={<Check data-testid="check-icon" />}
        uncheckedIcon={<X data-testid="x-icon" />}
        onChange={mockOnChange} 
      />
    )
    
    expect(screen.getByTestId('check-icon')).toBeInTheDocument()
    expect(screen.queryByTestId('x-icon')).not.toBeInTheDocument()
  })

  it('switches icons when toggled', () => {
    const { rerender } = render(
      <Switch 
        checked={false}
        checkedIcon={<Check data-testid="check-icon" />}
        uncheckedIcon={<X data-testid="x-icon" />}
        onChange={mockOnChange} 
      />
    )
    
    expect(screen.getByTestId('x-icon')).toBeInTheDocument()
    expect(screen.queryByTestId('check-icon')).not.toBeInTheDocument()
    
    rerender(
      <Switch 
        checked={true}
        checkedIcon={<Check data-testid="check-icon" />}
        uncheckedIcon={<X data-testid="x-icon" />}
        onChange={mockOnChange} 
      />
    )
    
    expect(screen.getByTestId('check-icon')).toBeInTheDocument()
    expect(screen.queryByTestId('x-icon')).not.toBeInTheDocument()
  })

  it('handles label position correctly', () => {
    const { rerender } = render(
      <Switch 
        label="Left label" 
        labelPosition="left" 
        checked={false} 
        onChange={mockOnChange} 
      />
    )
    
    const container = screen.getByText('Left label').closest('div')
    expect(container?.previousElementSibling?.tagName).toBe('BUTTON')
    
    rerender(
      <Switch 
        label="Right label" 
        labelPosition="right" 
        checked={false} 
        onChange={mockOnChange} 
      />
    )
    
    const rightContainer = screen.getByText('Right label').closest('div')
    expect(rightContainer?.nextElementSibling?.tagName).toBe('BUTTON')
  })

  describe('healthcare-specific features', () => {
    it('displays priority indicators', () => {
      const { rerender } = render(
        <Switch 
          label="Medium Priority"
          medical={{ priority: 'medium' }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      let priorityIndicator = document.querySelector('[title="Priority: medium"]')
      expect(priorityIndicator).toBeInTheDocument()
      expect(priorityIndicator).toHaveClass('bg-warning-400')
      
      rerender(
        <Switch 
          label="Critical Priority"
          medical={{ priority: 'critical' }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      priorityIndicator = document.querySelector('[title="Priority: critical"]')
      expect(priorityIndicator).toBeInTheDocument()
      expect(priorityIndicator).toHaveClass('bg-error-500', 'animate-pulse')
    })

    it('displays compliance indicators', () => {
      const { rerender } = render(
        <Switch 
          label="Required Setting"
          medical={{ compliance: 'required' }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      let complianceIndicator = screen.getByText('required')
      expect(complianceIndicator).toBeInTheDocument()
      expect(complianceIndicator).toHaveClass('bg-error-100', 'text-error-700')
      
      rerender(
        <Switch 
          label="Recommended Setting"
          medical={{ compliance: 'recommended' }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      complianceIndicator = screen.getByText('recommended')
      expect(complianceIndicator).toBeInTheDocument()
      expect(complianceIndicator).toHaveClass('bg-warning-100', 'text-warning-700')
    })

    it('shows safety critical indicator', () => {
      render(
        <Switch 
          label="Safety Setting"
          medical={{ affectsSafety: true }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const safetyIndicator = screen.getByText('Safety Critical')
      expect(safetyIndicator).toBeInTheDocument()
      expect(safetyIndicator).toHaveClass('bg-error-100', 'text-error-700')
      expect(safetyIndicator).toHaveAttribute('title', 'This setting affects patient safety')
    })

    it('includes safety information in screen reader text', () => {
      render(
        <Switch 
          label="Critical Alert"
          medical={{ affectsSafety: true }}
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const screenReaderText = document.querySelector('.sr-only')
      expect(screenReaderText).toHaveTextContent('Critical Alert (affects patient safety)')
    })

    it('handles medical categories correctly', () => {
      const medicalCategories = ['alert', 'notification', 'privacy', 'sharing', 'reminder'] as const
      
      medicalCategories.forEach(category => {
        const { unmount } = render(
          <Switch 
            label={`${category} setting`}
            medical={{ category }}
            checked={false} 
            onChange={mockOnChange} 
          />
        )
        
        // Just verify it renders without errors
        expect(screen.getByText(`${category} setting`)).toBeInTheDocument()
        unmount()
      })
    })
  })

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <Switch 
          label="Accessible switch"
          description="This is a description"
          id="accessible-switch"
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-checked', 'false')
      expect(switchElement).toHaveAttribute('aria-describedby', 'accessible-switch-description')
      expect(switchElement).toHaveAttribute('aria-label', 'Accessible switch')
    })

    it('provides fallback aria-label when no label provided', () => {
      render(<Switch checked={false} onChange={mockOnChange} />)
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-label', 'Toggle switch')
    })

    it('links label correctly with switch', () => {
      render(
        <Switch 
          label="Linked switch"
          id="linked-switch"
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const label = screen.getByText('Linked switch')
      expect(label).toHaveAttribute('for', 'linked-switch')
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement.id).toBe('linked-switch')
    })

    it('generates ID from label when no ID provided', () => {
      render(
        <Switch 
          label="Auto Generated ID"
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement.id).toBe('switch-auto-generated-id')
    })

    it('has touch-friendly sizing', () => {
      render(<Switch label="Touch switch" checked={false} onChange={mockOnChange} />)
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass('touch-manipulation')
    })
  })

  describe('form integration', () => {
    it('works with form controls', async () => {
      const user = userEvent.setup()
      const handleSubmit = vi.fn((e) => e.preventDefault())
      
      render(
        <form onSubmit={handleSubmit}>
          <Switch 
            label="Form switch" 
            name="enable-feature"
            checked={true} 
            onChange={mockOnChange} 
          />
          <button type="submit">Submit</button>
        </form>
      )
      
      const submitButton = screen.getByRole('button', { name: 'Submit' })
      await user.click(submitButton)
      
      expect(handleSubmit).toHaveBeenCalled()
    })

    it('maintains state correctly in uncontrolled mode', async () => {
      const user = userEvent.setup()
      render(
        <Switch 
          label="Uncontrolled switch" 
          defaultChecked={false}
          onChange={mockOnChange} 
        />
      )
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveAttribute('aria-checked', 'false')
      
      await user.click(switchElement)
      expect(switchElement).toHaveAttribute('aria-checked', 'true')
      
      await user.click(switchElement)
      expect(switchElement).toHaveAttribute('aria-checked', 'false')
    })
  })

  describe('styling and visual states', () => {
    it('applies focus styles correctly', async () => {
      const user = userEvent.setup()
      render(<Switch label="Focus switch" checked={false} onChange={mockOnChange} />)
      
      const switchElement = screen.getByRole('switch')
      await user.tab()
      
      expect(switchElement).toHaveClass('focus:ring-2', 'focus:ring-offset-2')
    })

    it('shows different focus ring colors for variants', () => {
      const { rerender } = render(<Switch variant="primary" checked={false} onChange={mockOnChange} />)
      
      let switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass('focus:ring-primary-500')
      
      rerender(<Switch variant="error" checked={false} onChange={mockOnChange} />)
      
      switchElement = screen.getByRole('switch')
      expect(switchElement).toHaveClass('focus:ring-error-500')
    })

    it('applies disabled styling to label and description', () => {
      render(
        <Switch 
          label="Disabled switch"
          description="This is disabled"
          disabled
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const label = screen.getByText('Disabled switch')
      expect(label).toHaveClass('cursor-not-allowed', 'opacity-50')
      
      const description = screen.getByText('This is disabled')
      expect(description).toHaveClass('opacity-50')
    })
  })

  describe('edge cases', () => {
    it('handles rapid toggling correctly', async () => {
      const user = userEvent.setup()
      render(<Switch label="Rapid toggle" checked={false} onChange={mockOnChange} />)
      
      const switchElement = screen.getByRole('switch')
      
      // Rapid clicks
      await user.click(switchElement)
      await user.click(switchElement)
      await user.click(switchElement)
      
      expect(mockOnChange).toHaveBeenCalledTimes(3)
    })

    it('prevents actions when both disabled and loading', async () => {
      const user = userEvent.setup()
      render(
        <Switch 
          label="Disabled and loading" 
          disabled 
          loading 
          checked={false} 
          onChange={mockOnChange} 
        />
      )
      
      const switchElement = screen.getByRole('switch')
      await user.click(switchElement)
      
      expect(mockOnChange).not.toHaveBeenCalled()
    })

    it('handles missing optional props gracefully', () => {
      render(<Switch onChange={mockOnChange} />)
      
      const switchElement = screen.getByRole('switch')
      expect(switchElement).toBeInTheDocument()
      expect(switchElement).toHaveAttribute('aria-checked', 'false') // defaultChecked is false
    })
  })
})
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Checkbox from '../Checkbox'

describe('Checkbox Component', () => {
  let mockOnChange: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnChange = vi.fn()
  })

  it('renders checkbox with label', () => {
    render(<Checkbox label="Accept terms and conditions" />)
    
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
    expect(screen.getByLabelText('Accept terms and conditions')).toBeInTheDocument()
  })

  it('shows required indicator when required', () => {
    render(<Checkbox label="Required field" required />)
    
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('displays helper text when provided', () => {
    render(
      <Checkbox 
        label="Newsletter subscription" 
        helperText="You can unsubscribe at any time"
      />
    )
    
    expect(screen.getByText('You can unsubscribe at any time')).toBeInTheDocument()
  })

  it('displays error message and applies error styling', () => {
    render(
      <Checkbox 
        label="Terms acceptance" 
        error="You must accept the terms to continue"
      />
    )
    
    const errorMessage = screen.getByRole('alert')
    expect(errorMessage).toHaveTextContent('You must accept the terms to continue')
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveClass('border-error-300', 'focus:ring-error-500')
    expect(checkbox).toHaveAttribute('aria-invalid', 'true')
  })

  it('prioritizes error message over helper text', () => {
    render(
      <Checkbox 
        label="Terms acceptance" 
        helperText="Read the terms carefully"
        error="You must accept the terms"
      />
    )
    
    expect(screen.getByRole('alert')).toHaveTextContent('You must accept the terms')
    expect(screen.queryByText('Read the terms carefully')).not.toBeInTheDocument()
  })

  it('calls onChange when clicked', async () => {
    const user = userEvent.setup()
    render(<Checkbox label="Test checkbox" onChange={mockOnChange} />)
    
    const checkbox = screen.getByRole('checkbox')
    await user.click(checkbox)
    
    expect(mockOnChange).toHaveBeenCalledTimes(1)
  })

  it('handles checked state correctly', () => {
    const { rerender } = render(<Checkbox label="Test checkbox" checked={false} />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).not.toBeChecked()
    
    rerender(<Checkbox label="Test checkbox" checked={true} />)
    expect(checkbox).toBeChecked()
  })

  it('handles disabled state correctly', async () => {
    const user = userEvent.setup()
    render(<Checkbox label="Disabled checkbox" disabled onChange={mockOnChange} />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeDisabled()
    expect(checkbox).toHaveClass('opacity-50', 'cursor-not-allowed')
    
    // Should not call onChange when disabled
    await user.click(checkbox)
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('applies disabled styling to label', () => {
    render(<Checkbox label="Disabled checkbox" disabled />)
    
    const label = screen.getByText('Disabled checkbox')
    expect(label).toHaveClass('opacity-50', 'cursor-not-allowed')
  })

  it('handles indeterminate state', () => {
    render(<Checkbox label="Indeterminate checkbox" indeterminate />)
    
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement
    expect(checkbox.indeterminate).toBe(true)
  })

  it('applies custom className', () => {
    render(<Checkbox label="Custom checkbox" className="custom-checkbox" />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveClass('custom-checkbox')
  })

  it('generates unique IDs when not provided', () => {
    render(
      <div>
        <Checkbox label="Checkbox 1" />
        <Checkbox label="Checkbox 2" />
      </div>
    )
    
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes[0].id).not.toBe(checkboxes[1].id)
    expect(checkboxes[0].id).toMatch(/^checkbox-/)
    expect(checkboxes[1].id).toMatch(/^checkbox-/)
  })

  it('uses provided ID', () => {
    render(<Checkbox label="Custom ID checkbox" id="custom-checkbox-id" />)
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox.id).toBe('custom-checkbox-id')
  })

  it('links label to checkbox with correct ID', () => {
    render(<Checkbox label="Linked checkbox" id="linked-checkbox" />)
    
    const label = screen.getByText('Linked checkbox')
    expect(label).toHaveAttribute('for', 'linked-checkbox')
    
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox.id).toBe('linked-checkbox')
  })

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <Checkbox 
          label="Accessible checkbox" 
          helperText="Helper text"
          id="accessible-checkbox"
        />
      )
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-invalid', 'false')
      expect(checkbox).toHaveAttribute('aria-describedby', 'accessible-checkbox-helper')
    })

    it('has proper ARIA attributes with error', () => {
      render(
        <Checkbox 
          label="Error checkbox" 
          error="This field is required"
          id="error-checkbox"
        />
      )
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('aria-invalid', 'true')
      expect(checkbox).toHaveAttribute('aria-describedby', 'error-checkbox-error')
    })

    it('handles keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<Checkbox label="Keyboard checkbox" onChange={mockOnChange} />)
      
      const checkbox = screen.getByRole('checkbox')
      
      // Focus the checkbox
      await user.tab()
      expect(checkbox).toHaveFocus()
      
      // Space should toggle the checkbox
      await user.keyboard(' ')
      expect(mockOnChange).toHaveBeenCalledTimes(1)
    })

    it('provides accessible error messaging', () => {
      render(
        <Checkbox 
          label="Error checkbox" 
          error="Required field"
        />
      )
      
      const errorMessage = screen.getByRole('alert')
      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage).toHaveTextContent('Required field')
    })

    it('handles required state properly', () => {
      render(<Checkbox label="Required checkbox" required />)
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveAttribute('required')
      
      const requiredIndicator = screen.getByText('*')
      expect(requiredIndicator).toHaveClass('text-error-500')
    })
  })

  describe('form integration', () => {
    it('works with form controls', async () => {
      const user = userEvent.setup()
      const handleSubmit = vi.fn((e) => e.preventDefault())
      
      render(
        <form onSubmit={handleSubmit}>
          <Checkbox label="Form checkbox" name="agreement" value="agreed" />
          <button type="submit">Submit</button>
        </form>
      )
      
      const checkbox = screen.getByRole('checkbox')
      const submitButton = screen.getByRole('button', { name: 'Submit' })
      
      await user.click(checkbox)
      await user.click(submitButton)
      
      expect(handleSubmit).toHaveBeenCalled()
    })

    it('forwards ref correctly', () => {
      const ref = { current: null }
      
      render(<Checkbox label="Ref checkbox" ref={ref} />)
      
      expect(ref.current).toBeTruthy()
      expect(ref.current).toBeInstanceOf(HTMLInputElement)
    })

    it('passes through additional props', () => {
      render(
        <Checkbox 
          label="Props checkbox" 
          data-testid="test-checkbox"
          aria-describedby="external-description"
        />
      )
      
      const checkbox = screen.getByTestId('test-checkbox')
      expect(checkbox).toBeInTheDocument()
      expect(checkbox).toHaveAttribute('aria-describedby', 'external-description')
    })
  })

  describe('styling variants', () => {
    it('applies default styling correctly', () => {
      render(<Checkbox label="Default checkbox" />)
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass(
        'h-4', 'w-4', 'rounded', 'border-gray-300', 
        'text-primary-600', 'focus:ring-primary-500'
      )
    })

    it('applies error styling correctly', () => {
      render(<Checkbox label="Error checkbox" error="Error message" />)
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toHaveClass('border-error-300', 'focus:ring-error-500')
      
      const label = screen.getByText('Error checkbox')
      expect(label).toHaveClass('text-error-700')
    })

    it('maintains proper visual hierarchy', () => {
      render(
        <Checkbox 
          label="Visual hierarchy checkbox" 
          helperText="This is helper text"
        />
      )
      
      const label = screen.getByText('Visual hierarchy checkbox')
      expect(label).toHaveClass('text-sm', 'font-medium')
      
      const helperText = screen.getByText('This is helper text')
      expect(helperText).toHaveClass('text-sm', 'text-gray-600')
    })
  })

  describe('edge cases', () => {
    it('handles empty label gracefully', () => {
      render(<Checkbox label="" />)
      
      const checkbox = screen.getByRole('checkbox')
      expect(checkbox).toBeInTheDocument()
    })

    it('handles very long labels correctly', () => {
      const longLabel = 'This is a very long label that might wrap to multiple lines and should still maintain proper alignment with the checkbox component'
      
      render(<Checkbox label={longLabel} />)
      
      expect(screen.getByText(longLabel)).toBeInTheDocument()
    })

    it('updates indeterminate state when prop changes', () => {
      const { rerender } = render(<Checkbox label="Test" indeterminate={false} />)
      
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement
      expect(checkbox.indeterminate).toBe(false)
      
      rerender(<Checkbox label="Test" indeterminate={true} />)
      expect(checkbox.indeterminate).toBe(true)
    })
  })
})
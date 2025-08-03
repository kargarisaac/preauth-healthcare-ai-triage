import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RadioGroup from '../RadioGroup'

describe('RadioGroup Component', () => {
  let mockOnChange: ReturnType<typeof vi.fn>
  let mockOptions: Array<{ value: string; label: string; description?: string; disabled?: boolean }>

  beforeEach(() => {
    mockOnChange = vi.fn()
    mockOptions = [
      { 
        value: 'basic', 
        label: 'Basic Coverage', 
        description: 'Essential medical services only' 
      },
      { 
        value: 'premium', 
        label: 'Premium Coverage', 
        description: 'Comprehensive medical services with extras' 
      },
      { 
        value: 'family', 
        label: 'Family Plan', 
        description: 'Coverage for entire family',
        disabled: true 
      }
    ]
  })

  it('renders radio group with all options', () => {
    render(
      <RadioGroup
        name="insurance-type"
        label="Insurance Type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    expect(screen.getByText('Insurance Type')).toBeInTheDocument()
    expect(screen.getByLabelText('Basic Coverage')).toBeInTheDocument()
    expect(screen.getByLabelText('Premium Coverage')).toBeInTheDocument()
    expect(screen.getByLabelText('Family Plan')).toBeInTheDocument()
  })

  it('shows descriptions when provided', () => {
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    expect(screen.getByText('Essential medical services only')).toBeInTheDocument()
    expect(screen.getByText('Comprehensive medical services with extras')).toBeInTheDocument()
    expect(screen.getByText('Coverage for entire family')).toBeInTheDocument()
  })

  it('displays helper text when provided', () => {
    render(
      <RadioGroup
        name="insurance-type"
        label="Insurance Type"
        helperText="Choose the plan that best fits your needs"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    expect(screen.getByText('Choose the plan that best fits your needs')).toBeInTheDocument()
  })

  it('displays error message and applies error styling', () => {
    render(
      <RadioGroup
        name="insurance-type"
        label="Insurance Type"
        error="Please select an insurance type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    const errorMessage = screen.getByRole('alert')
    expect(errorMessage).toHaveTextContent('Please select an insurance type')
    
    const radioGroup = screen.getByRole('radiogroup')
    expect(radioGroup).toHaveAttribute('aria-invalid', 'true')
  })

  it('prioritizes error message over helper text', () => {
    render(
      <RadioGroup
        name="insurance-type"
        label="Insurance Type"
        helperText="Choose wisely"
        error="Selection required"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    expect(screen.getByRole('alert')).toHaveTextContent('Selection required')
    expect(screen.queryByText('Choose wisely')).not.toBeInTheDocument()
  })

  it('calls onChange when option is selected', async () => {
    const user = userEvent.setup()
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    const basicOption = screen.getByLabelText('Basic Coverage')
    await user.click(basicOption)
    
    expect(mockOnChange).toHaveBeenCalledWith('basic')
  })

  it('handles controlled value correctly', () => {
    const { rerender } = render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value="basic"
        onChange={mockOnChange}
      />
    )
    
    const basicOption = screen.getByLabelText('Basic Coverage')
    expect(basicOption).toBeChecked()
    
    rerender(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value="premium"
        onChange={mockOnChange}
      />
    )
    
    const premiumOption = screen.getByLabelText('Premium Coverage')
    expect(premiumOption).toBeChecked()
    expect(basicOption).not.toBeChecked()
  })

  it('disables individual options when marked as disabled', async () => {
    const user = userEvent.setup()
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    const familyOption = screen.getByLabelText('Family Plan')
    expect(familyOption).toBeDisabled()
    expect(familyOption).toHaveClass('opacity-50', 'cursor-not-allowed')
    
    // Should not call onChange when disabled option is clicked
    await user.click(familyOption)
    expect(mockOnChange).not.toHaveBeenCalled()
  })

  it('disables entire group when disabled prop is true', () => {
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
        disabled
      />
    )
    
    const fieldset = screen.getByRole('group')
    expect(fieldset).toHaveClass('opacity-50')
    
    const radioButtons = screen.getAllByRole('radio')
    radioButtons.forEach(radio => {
      expect(radio).toBeDisabled()
    })
  })

  it('handles horizontal orientation', () => {
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
        orientation="horizontal"
      />
    )
    
    const radioGroup = screen.getByRole('radiogroup')
    expect(radioGroup).toHaveClass('flex', 'space-x-6')
  })

  it('uses vertical orientation by default', () => {
    render(
      <RadioGroup
        name="insurance-type"
        options={mockOptions}
        value=""
        onChange={mockOnChange}
      />
    )
    
    const radioGroup = screen.getByRole('radiogroup')
    expect(radioGroup).toHaveClass('space-y-4')
    expect(radioGroup).not.toHaveClass('flex')
  })

  it('generates unique IDs for radio options', () => {
    render(
      <RadioGroup
        name="test-radio"
        options={[
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2' }
        ]}
        value=""
        onChange={mockOnChange}
      />
    )
    
    const option1 = screen.getByLabelText('Option 1')
    const option2 = screen.getByLabelText('Option 2')
    
    expect(option1.id).toBe('test-radio-option1')
    expect(option2.id).toBe('test-radio-option2')
  })

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <RadioGroup
          name="insurance-type"
          label="Insurance Type"
          helperText="Choose your plan"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const fieldset = screen.getByRole('group')
      const radioGroup = screen.getByRole('radiogroup')
      
      expect(fieldset).toBeInTheDocument()
      expect(radioGroup).toHaveAttribute('aria-invalid', 'false')
      
      // Check for proper fieldset/legend structure
      const legend = screen.getByText('Insurance Type')
      expect(legend.tagName).toBe('LEGEND')
    })

    it('has proper ARIA attributes with error', () => {
      render(
        <RadioGroup
          name="insurance-type"
          label="Insurance Type"
          error="Selection required"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const radioGroup = screen.getByRole('radiogroup')
      expect(radioGroup).toHaveAttribute('aria-invalid', 'true')
      
      const fieldset = screen.getByRole('group')
      const errorId = fieldset.getAttribute('aria-describedby')
      expect(errorId).toContain('error')
    })

    it('links helper text with proper ARIA relationships', () => {
      render(
        <RadioGroup
          name="insurance-type"
          label="Insurance Type"
          helperText="Choose the best option for you"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const fieldset = screen.getByRole('group')
      const describedBy = fieldset.getAttribute('aria-describedby')
      expect(describedBy).toContain('helper')
      
      const helperText = screen.getByText('Choose the best option for you')
      expect(helperText.id).toBe(describedBy)
    })

    it('handles keyboard navigation', async () => {
      const user = userEvent.setup()
      render(
        <RadioGroup
          name="insurance-type"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const basicOption = screen.getByLabelText('Basic Coverage')
      const premiumOption = screen.getByLabelText('Premium Coverage')
      
      // Focus first option
      await user.tab()
      expect(basicOption).toHaveFocus()
      
      // Arrow down should move to next option and select it
      await user.keyboard('{ArrowDown}')
      expect(premiumOption).toHaveFocus()
      expect(mockOnChange).toHaveBeenCalledWith('premium')
    })

    it('skips disabled options in keyboard navigation', async () => {
      const user = userEvent.setup()
      render(
        <RadioGroup
          name="insurance-type"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const basicOption = screen.getByLabelText('Basic Coverage')
      const premiumOption = screen.getByLabelText('Premium Coverage')
      
      // Start from premium (second option)
      premiumOption.focus()
      
      // Arrow down should skip disabled family option and wrap to basic
      await user.keyboard('{ArrowDown}')
      expect(basicOption).toHaveFocus()
    })
  })

  describe('form integration', () => {
    it('works with form elements', async () => {
      const user = userEvent.setup()
      const handleSubmit = vi.fn((e) => e.preventDefault())
      
      render(
        <form onSubmit={handleSubmit}>
          <RadioGroup
            name="plan-type"
            options={[
              { value: 'basic', label: 'Basic' },
              { value: 'premium', label: 'Premium' }
            ]}
            value="basic"
            onChange={mockOnChange}
          />
          <button type="submit">Submit</button>
        </form>
      )
      
      const submitButton = screen.getByRole('button', { name: 'Submit' })
      await user.click(submitButton)
      
      expect(handleSubmit).toHaveBeenCalled()
    })

    it('maintains radio group behavior with same name', async () => {
      const user = userEvent.setup()
      render(
        <RadioGroup
          name="exclusive-choice"
          options={[
            { value: 'option1', label: 'Option 1' },
            { value: 'option2', label: 'Option 2' },
            { value: 'option3', label: 'Option 3' }
          ]}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const option1 = screen.getByLabelText('Option 1')
      const option2 = screen.getByLabelText('Option 2')
      
      // Select first option
      await user.click(option1)
      expect(option1).toBeChecked()
      expect(option2).not.toBeChecked()
      
      // Select second option should uncheck first
      await user.click(option2)
      expect(option1).not.toBeChecked()
      expect(option2).toBeChecked()
    })
  })

  describe('styling and variants', () => {
    it('applies error styling to labels and inputs', () => {
      render(
        <RadioGroup
          name="insurance-type"
          label="Insurance Type"
          error="Required field"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const legend = screen.getByText('Insurance Type')
      expect(legend).toHaveClass('text-error-700')
      
      const radioButtons = screen.getAllByRole('radio')
      radioButtons.forEach(radio => {
        expect(radio).toHaveClass('border-error-300', 'focus:ring-error-500')
      })
    })

    it('maintains proper visual hierarchy', () => {
      render(
        <RadioGroup
          name="insurance-type"
          label="Insurance Type"
          options={mockOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const labels = screen.getAllByText(/Coverage|Plan/)
      labels.forEach(label => {
        expect(label).toHaveClass('text-sm', 'font-medium')
      })
      
      const descriptions = screen.getAllByText(/services|family/)
      descriptions.forEach(desc => {
        expect(desc).toHaveClass('text-sm', 'text-gray-500')
      })
    })
  })

  describe('edge cases', () => {
    it('handles empty options array', () => {
      render(
        <RadioGroup
          name="empty-group"
          label="Empty Group"
          options={[]}
          value=""
          onChange={mockOnChange}
        />
      )
      
      expect(screen.getByText('Empty Group')).toBeInTheDocument()
      expect(screen.queryByRole('radio')).not.toBeInTheDocument()
    })

    it('handles options without descriptions', () => {
      const simpleOptions = [
        { value: 'yes', label: 'Yes' },
        { value: 'no', label: 'No' }
      ]
      
      render(
        <RadioGroup
          name="simple-choice"
          options={simpleOptions}
          value=""
          onChange={mockOnChange}
        />
      )
      
      expect(screen.getByLabelText('Yes')).toBeInTheDocument()
      expect(screen.getByLabelText('No')).toBeInTheDocument()
    })

    it('works without label', () => {
      render(
        <RadioGroup
          name="no-label"
          options={[{ value: 'option', label: 'Option' }]}
          value=""
          onChange={mockOnChange}
        />
      )
      
      const radioGroup = screen.getByRole('radiogroup')
      expect(radioGroup).toBeInTheDocument()
    })
  })
})
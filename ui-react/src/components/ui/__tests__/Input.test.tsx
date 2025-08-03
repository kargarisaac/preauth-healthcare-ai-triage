import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import { axe, toHaveNoViolations } from 'jest-axe'
import Input from '../Input'

// Extend expect with jest-axe matchers
expect.extend(toHaveNoViolations)

describe('Input Component', () => {
  describe('Basic Rendering', () => {
    it('renders basic input correctly', () => {
      render(<Input placeholder="Enter text" />)
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
    })

    it('renders with label', () => {
      render(<Input label="Email" placeholder="Enter email" />)
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
    })

    it('generates unique ID when not provided', () => {
      const { container } = render(<Input label="Test" />)
      const input = screen.getByRole('textbox')
      const label = screen.getByText('Test')
      
      expect(input).toHaveAttribute('id')
      expect(label).toHaveAttribute('for', input.getAttribute('id'))
    })

    it('uses provided ID', () => {
      render(<Input id="custom-id" label="Test" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('id', 'custom-id')
    })

    it('applies fullWidth class by default', () => {
      const { container } = render(<Input />)
      expect(container.firstChild).toHaveClass('w-full')
      expect(screen.getByRole('textbox')).toHaveClass('w-full')
    })

    it('does not apply fullWidth when false', () => {
      const { container } = render(<Input fullWidth={false} />)
      expect(container.firstChild).not.toHaveClass('w-full')
      expect(screen.getByRole('textbox')).not.toHaveClass('w-full')
    })
  })

  describe('Error Handling', () => {
    it('shows error message when error prop is provided', () => {
      render(<Input label="Email" error="Invalid email" />)
      expect(screen.getByText('Invalid email')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('applies error styles when error is present', () => {
      render(<Input error="Error message" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('input-error')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })

    it('links error message to input via aria-describedby', () => {
      render(<Input id="test-input" error="Error message" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'test-input-error')
    })

    it('prioritizes error over helper text', () => {
      render(
        <Input 
          id="test-input"
          error="Error message" 
          helperText="Helper text"
        />
      )
      
      expect(screen.getByText('Error message')).toBeInTheDocument()
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    })
  })

  describe('Helper Text', () => {
    it('shows helper text when provided', () => {
      render(<Input label="Password" helperText="Must be at least 8 characters" />)
      expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument()
    })

    it('links helper text to input via aria-describedby', () => {
      render(<Input id="test-input" helperText="Helper text" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'test-input-helper')
    })
  })

  describe('User Interactions', () => {
    it('handles user input correctly', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      render(<Input onChange={handleChange} placeholder="Type here" />)
      
      const input = screen.getByPlaceholderText('Type here')
      await user.type(input, 'Hello')
      
      expect(handleChange).toHaveBeenCalledTimes(5) // One for each character
      expect(input).toHaveValue('Hello')
    })

    it('handles focus and blur events', async () => {
      const user = userEvent.setup()
      const onFocus = vi.fn()
      const onBlur = vi.fn()
      render(<Input onFocus={onFocus} onBlur={onBlur} />)
      
      const input = screen.getByRole('textbox')
      await user.click(input)
      expect(onFocus).toHaveBeenCalledTimes(1)
      
      await user.tab()
      expect(onBlur).toHaveBeenCalledTimes(1)
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<Input />)
      
      await user.tab()
      expect(screen.getByRole('textbox')).toHaveFocus()
    })
  })

  describe('States', () => {
    it('is disabled when disabled prop is true', () => {
      render(<Input disabled placeholder="Disabled input" />)
      const input = screen.getByPlaceholderText('Disabled input')
      expect(input).toBeDisabled()
      expect(input).toHaveClass('opacity-50', 'cursor-not-allowed')
    })

    it('shows required asterisk when required', () => {
      render(<Input label="Required Field" required />)
      expect(screen.getByText('*')).toBeInTheDocument()
      expect(screen.getByRole('textbox')).toHaveAttribute('required')
    })

    it('does not allow interaction when disabled', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<Input disabled onChange={onChange} />)
      
      const input = screen.getByRole('textbox')
      await user.type(input, 'test')
      
      expect(onChange).not.toHaveBeenCalled()
      expect(input).toHaveValue('')
    })
  })

  describe('Input Types', () => {
    it('supports different input types', () => {
      const { rerender } = render(<Input type="email" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email')
      
      rerender(<Input type="password" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'password')
      
      rerender(<Input type="tel" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'tel')
    })

    it('defaults to text type', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text')
    })
  })

  describe('Icons', () => {
    it('renders with left icon', () => {
      render(
        <Input leftIcon={<span data-testid="left-icon">👤</span>} />
      )
      
      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByRole('textbox')).toHaveClass('pl-10')
    })

    it('renders with right icon', () => {
      render(
        <Input rightIcon={<span data-testid="right-icon">✓</span>} />
      )
      
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
      expect(screen.getByRole('textbox')).toHaveClass('pr-10')
    })

    it('renders with both icons', () => {
      render(
        <Input 
          leftIcon={<span data-testid="left-icon">👤</span>}
          rightIcon={<span data-testid="right-icon">✓</span>}
        />
      )
      
      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('pl-10', 'pr-10')
    })
  })

  describe('Variants', () => {
    it('applies default variant classes', () => {
      render(<Input variant="default" />)
      expect(screen.getByRole('textbox')).toHaveClass('bg-white')
    })

    it('applies filled variant classes', () => {
      render(<Input variant="filled" />)
      expect(screen.getByRole('textbox')).toHaveClass('bg-gray-50')
    })

    it('defaults to default variant', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toHaveClass('bg-white')
    })
  })

  describe('Custom Props', () => {
    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLInputElement>()
      render(<Input ref={ref} />)
      expect(ref.current).toBeInstanceOf(HTMLInputElement)
    })

    it('applies custom className', () => {
      render(<Input className="custom-class" />)
      expect(screen.getByRole('textbox')).toHaveClass('custom-class')
    })

    it('passes through additional props', () => {
      render(<Input data-testid="custom-input" maxLength={10} />)
      const input = screen.getByTestId('custom-input')
      expect(input).toHaveAttribute('maxLength', '10')
    })
  })

  describe('Healthcare Context', () => {
    it('handles medical record numbers', async () => {
      const user = userEvent.setup()
      render(
        <Input 
          label="Medical Record Number"
          placeholder="Enter MRN"
          pattern="[0-9]{8}"
        />
      )
      
      const input = screen.getByLabelText('Medical Record Number')
      await user.type(input, '12345678')
      
      expect(input).toHaveValue('12345678')
      expect(input).toHaveAttribute('pattern', '[0-9]{8}')
    })

    it('handles sensitive healthcare data with autocomplete off', () => {
      render(
        <Input 
          label="Patient ID"
          autoComplete="off"
          type="text"
        />
      )
      
      expect(screen.getByRole('textbox')).toHaveAttribute('autoComplete', 'off')
    })
  })

  describe('Accessibility', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <Input 
          label="Accessible Input"
          helperText="This is a helper text"
          required
        />
      )
      
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('has no accessibility violations with error', async () => {
      const { container } = render(
        <Input 
          label="Input with Error"
          error="This field is required"
          required
        />
      )
      
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('maintains proper ARIA relationships', () => {
      render(
        <Input 
          id="test-input"
          label="Test Input"
          error="Error message"
          helperText="Helper text"
        />
      )
      
      const input = screen.getByRole('textbox')
      const label = screen.getByText('Test Input')
      const error = screen.getByRole('alert')
      
      expect(label).toHaveAttribute('for', 'test-input')
      expect(input).toHaveAttribute('aria-describedby', 'test-input-error')
      expect(error).toHaveAttribute('id', 'test-input-error')
    })

    it('supports screen readers with proper labeling', () => {
      render(
        <Input 
          label="Email Address"
          required
          placeholder="user@example.com"
        />
      )
      
      const input = screen.getByLabelText('Email Address *')
      expect(input).toHaveAttribute('placeholder', 'user@example.com')
      expect(input).toHaveAttribute('required')
    })
  })
})
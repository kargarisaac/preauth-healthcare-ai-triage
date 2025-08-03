import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Select from '../Select';

describe('Select Component', () => {
  const mockOptions = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3', disabled: true }
  ];

  it('renders with label and options', () => {
    render(
      <Select 
        label="Choose Option" 
        options={mockOptions}
        data-testid="test-select"
      />
    );
    
    expect(screen.getByLabelText('Choose Option')).toBeInTheDocument();
    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
    expect(screen.getByText('Option 3')).toBeInTheDocument();
  });

  it('shows placeholder when provided', () => {
    render(
      <Select 
        options={mockOptions}
        placeholder="Select an option"
        data-testid="test-select"
      />
    );
    
    expect(screen.getByText('Select an option')).toBeInTheDocument();
  });

  it('shows required indicator when required', () => {
    render(<Select label="Required Field" options={mockOptions} required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <Select 
        label="Country" 
        options={mockOptions}
        error="Please select a country"
      />
    );
    
    expect(screen.getByRole('alert')).toHaveTextContent('Please select a country');
  });

  it('calls onChange when selection changes', () => {
    const handleChange = vi.fn();
    render(
      <Select 
        options={mockOptions}
        onChange={handleChange}
        data-testid="test-select"
      />
    );
    
    const select = screen.getByTestId('test-select');
    fireEvent.change(select, { target: { value: 'option2' } });
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('disables options when marked as disabled', () => {
    render(<Select options={mockOptions} data-testid="test-select" />);
    
    const select = screen.getByTestId('test-select');
    const disabledOption = select.querySelector('option[value="option3"]');
    expect(disabledOption).toHaveProperty('disabled', true);
  });

  it('applies error styles when error is present', () => {
    render(
      <Select 
        options={mockOptions}
        error="This field is required"
        data-testid="error-select"
      />
    );
    
    const select = screen.getByTestId('error-select');
    expect(select).toHaveClass('input-error');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Select options={mockOptions} disabled data-testid="disabled-select" />);
    
    const select = screen.getByTestId('disabled-select');
    expect(select).toBeDisabled();
  });
});
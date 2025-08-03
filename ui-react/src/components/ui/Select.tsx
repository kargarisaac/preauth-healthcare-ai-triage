import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import type { SelectProps } from '@/types/ui';

/**
 * Select component for dropdown selections with options and accessibility features.
 * 
 * @example
 * ```tsx
 * <Select 
 *   label="Country"
 *   placeholder="Select a country"
 *   options={[
 *     { value: 'ae', label: 'United Arab Emirates' },
 *     { value: 'sa', label: 'Saudi Arabia' }
 *   ]}
 *   required
 * />
 * ```
 */
const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helperText,
  options,
  placeholder,
  fullWidth = true,
  className,
  disabled,
  required,
  id,
  ...props
}, ref) => {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  
  const baseClasses = 'input appearance-none bg-white pr-10 cursor-pointer';
  
  const selectClasses = clsx(
    baseClasses,
    error && 'input-error',
    disabled && 'opacity-50 cursor-not-allowed',
    fullWidth && 'w-full',
    className
  );

  const containerClasses = clsx(
    'relative',
    fullWidth && 'w-full'
  );

  return (
    <div className={containerClasses}>
      {label && (
        <label 
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          disabled={disabled}
          required={required}
          className={selectClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? `${selectId}-error` : 
            helperText ? `${selectId}-helper` : undefined
          }
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        
        {/* Dropdown arrow */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <svg 
            className="w-5 h-5 text-gray-400" 
            viewBox="0 0 20 20" 
            fill="currentColor"
            aria-hidden="true"
          >
            <path 
              fillRule="evenodd" 
              d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" 
              clipRule="evenodd" 
            />
          </svg>
        </div>
      </div>
      
      {error && (
        <p 
          id={`${selectId}-error`}
          className="mt-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p 
          id={`${selectId}-helper`}
          className="mt-2 text-sm text-gray-600"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;
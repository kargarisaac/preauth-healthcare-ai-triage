import React, { forwardRef, useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import type { CheckboxProps } from '@/types/ui';

/**
 * Checkbox component for boolean selections with labels and accessibility features.
 * 
 * @example
 * ```tsx
 * <Checkbox 
 *   label="I agree to the terms and conditions"
 *   required
 *   helperText="You must agree to continue"
 * />
 * ```
 */
const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({
  label,
  error,
  helperText,
  indeterminate = false,
  className,
  disabled,
  required,
  id,
  ...props
}, ref) => {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;
  const internalRef = useRef<HTMLInputElement>(null);
  const checkboxRef = ref || internalRef;
  
  // Handle indeterminate state
  useEffect(() => {
    if (checkboxRef && typeof checkboxRef === 'object' && checkboxRef.current) {
      checkboxRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate, checkboxRef]);
  
  const checkboxClasses = clsx(
    'h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500 focus:ring-2 focus:ring-offset-2 transition-colors',
    error && 'border-error-300 focus:ring-error-500',
    disabled && 'opacity-50 cursor-not-allowed',
    className
  );

  const labelClasses = clsx(
    'text-sm font-medium',
    error ? 'text-error-700' : 'text-gray-700',
    disabled && 'opacity-50 cursor-not-allowed'
  );

  return (
    <div className="relative">
      <div className="flex items-start">
        <div className="flex items-center h-5">
          <input
            ref={checkboxRef}
            id={checkboxId}
            type="checkbox"
            disabled={disabled}
            required={required}
            className={checkboxClasses}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={
              error ? `${checkboxId}-error` : 
              helperText ? `${checkboxId}-helper` : undefined
            }
            {...props}
          />
        </div>
        <div className="ml-3">
          <label 
            htmlFor={checkboxId}
            className={labelClasses}
          >
            {label}
            {required && <span className="text-error-500 ml-1">*</span>}
          </label>
          
          {helperText && !error && (
            <p 
              id={`${checkboxId}-helper`}
              className="mt-1 text-sm text-gray-600"
            >
              {helperText}
            </p>
          )}
        </div>
      </div>
      
      {error && (
        <p 
          id={`${checkboxId}-error`}
          className="mt-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
});

Checkbox.displayName = 'Checkbox';

export default Checkbox;
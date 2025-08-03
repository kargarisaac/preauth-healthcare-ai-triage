import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import type { InputProps } from '@/types/ui';

/**
 * Input component for text inputs with validation, different types, and accessibility features.
 * 
 * @example
 * ```tsx
 * <Input 
 *   type="email"
 *   label="Email Address"
 *   placeholder="Enter your email"
 *   required
 *   error="Please enter a valid email"
 * />
 * ```
 */
const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  variant = 'default',
  fullWidth = true,
  leftIcon,
  rightIcon,
  className,
  disabled,
  required,
  type = 'text',
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  
  const baseClasses = 'input text-base';
  const variantClasses = {
    default: 'bg-white',
    filled: 'bg-gray-50 border-transparent focus:bg-white focus:border-primary-500',
  };

  const inputClasses = clsx(
    baseClasses,
    variantClasses[variant],
    error && 'input-error',
    disabled && 'opacity-50 cursor-not-allowed',
    leftIcon && 'pl-10',
    rightIcon && 'pr-10',
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
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400 text-sm">{leftIcon}</span>
          </div>
        )}
        
        <input
          ref={ref}
          id={inputId}
          type={type}
          disabled={disabled}
          required={required}
          className={inputClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? `${inputId}-error` : 
            helperText ? `${inputId}-helper` : undefined
          }
          {...props}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-gray-400 text-sm">{rightIcon}</span>
          </div>
        )}
      </div>
      
      {error && (
        <p 
          id={`${inputId}-error`}
          className="mt-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p 
          id={`${inputId}-helper`}
          className="mt-2 text-sm text-gray-600"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
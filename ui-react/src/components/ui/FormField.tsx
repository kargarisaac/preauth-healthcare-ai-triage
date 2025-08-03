import React from 'react';
import { clsx } from 'clsx';
import type { FormFieldWrapperProps } from '@/types/ui';

/**
 * FormField wrapper component that provides consistent field layout with labels and error messages.
 * Used to wrap form controls that don't have built-in label/error handling.
 * 
 * @example
 * ```tsx
 * <FormField
 *   label="Upload Document"
 *   error="Please select a valid file"
 *   required
 * >
 *   <FileUpload />
 * </FormField>
 * ```
 */
const FormField: React.FC<FormFieldWrapperProps> = ({
  label,
  error,
  helperText,
  required = false,
  children,
  className,
  labelClassName
}) => {
  const fieldId = `field-${Math.random().toString(36).substr(2, 9)}`;
  
  const containerClasses = clsx(
    'w-full',
    className
  );

  const labelClasses = clsx(
    'block text-sm font-medium mb-2',
    error ? 'text-error-700' : 'text-gray-700',
    labelClassName
  );

  return (
    <div className={containerClasses}>
      {label && (
        <label 
          htmlFor={fieldId}
          className={labelClasses}
        >
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      
      <div 
        id={fieldId}
        aria-describedby={
          error ? `${fieldId}-error` : 
          helperText ? `${fieldId}-helper` : undefined
        }
      >
        {children}
      </div>
      
      {error && (
        <p 
          id={`${fieldId}-error`}
          className="mt-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </p>
      )}
      
      {helperText && !error && (
        <p 
          id={`${fieldId}-helper`}
          className="mt-2 text-sm text-gray-600"
        >
          {helperText}
        </p>
      )}
    </div>
  );
};

export default FormField;
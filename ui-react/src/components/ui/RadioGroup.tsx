import React from 'react';
import { clsx } from 'clsx';
import type { RadioGroupProps } from '@/types/ui';

/**
 * RadioGroup component for single choice selections with accessibility features.
 * 
 * @example
 * ```tsx
 * <RadioGroup 
 *   name="insurance-type"
 *   label="Insurance Type"
 *   value={selectedType}
 *   onChange={setSelectedType}
 *   options={[
 *     { value: 'basic', label: 'Basic Coverage', description: 'Essential medical services' },
 *     { value: 'premium', label: 'Premium Coverage', description: 'Comprehensive medical services' }
 *   ]}
 *   orientation="vertical"
 * />
 * ```
 */
const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  value,
  onChange,
  options,
  label,
  error,
  helperText,
  disabled = false,
  orientation = 'vertical'
}) => {
  const groupId = `radio-group-${Math.random().toString(36).substr(2, 9)}`;
  
  const containerClasses = clsx(
    'space-y-4',
    orientation === 'horizontal' && 'flex space-y-0 space-x-6',
    disabled && 'opacity-50'
  );

  const labelClasses = clsx(
    'text-sm font-medium',
    error ? 'text-error-700' : 'text-gray-700'
  );

  return (
    <fieldset 
      className="w-full"
      aria-describedby={
        error ? `${groupId}-error` : 
        helperText ? `${groupId}-helper` : undefined
      }
    >
      {label && (
        <legend className={labelClasses}>
          {label}
        </legend>
      )}
      
      {(helperText && !error) && (
        <p 
          id={`${groupId}-helper`}
          className="mt-1 text-sm text-gray-600"
        >
          {helperText}
        </p>
      )}
      
      <div 
        className={clsx(
          containerClasses,
          (label || helperText) && 'mt-4'
        )}
        role="radiogroup"
        aria-invalid={error ? 'true' : 'false'}
      >
        {options.map((option) => {
          const radioId = `${name}-${option.value}`;
          const isSelected = value === option.value;
          const isDisabled = disabled || option.disabled;
          
          const radioClasses = clsx(
            'h-4 w-4 border-gray-300 text-primary-600 focus:ring-primary-500 focus:ring-2 focus:ring-offset-2 transition-colors',
            error && 'border-error-300 focus:ring-error-500',
            isDisabled && 'opacity-50 cursor-not-allowed'
          );
          
          const optionLabelClasses = clsx(
            'text-sm font-medium',
            error ? 'text-error-700' : 'text-gray-700',
            isDisabled && 'opacity-50 cursor-not-allowed'
          );
          
          return (
            <div key={option.value} className="relative flex items-start">
              <div className="flex items-center h-5">
                <input
                  id={radioId}
                  name={name}
                  type="radio"
                  value={option.value}
                  checked={isSelected}
                  disabled={isDisabled}
                  onChange={(e) => onChange(e.target.value)}
                  className={radioClasses}
                />
              </div>
              <div className="ml-3">
                <label 
                  htmlFor={radioId}
                  className={optionLabelClasses}
                >
                  {option.label}
                </label>
                {option.description && (
                  <p className="text-sm text-gray-500 mt-1">
                    {option.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {error && (
        <p 
          id={`${groupId}-error`}
          className="mt-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </p>
      )}
    </fieldset>
  );
};

export default RadioGroup;
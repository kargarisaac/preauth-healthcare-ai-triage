import React, { useState, useRef } from 'react';
import { clsx } from 'clsx';

export interface SwitchProps {
  /** Whether the switch is checked */
  checked?: boolean;
  /** Default checked state (for uncontrolled usage) */
  defaultChecked?: boolean;
  /** Callback when checked state changes */
  onChange?: (checked: boolean) => void;
  /** Whether the switch is disabled */
  disabled?: boolean;
  /** Switch label */
  label?: string;
  /** Switch description text */
  description?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Color variant */
  variant?: 'primary' | 'success' | 'warning' | 'error';
  /** Custom class name */
  className?: string;
  /** HTML name attribute */
  name?: string;
  /** HTML id attribute */
  id?: string;
  /** Whether to show loading state */
  loading?: boolean;
  /** Icon to show when checked */
  checkedIcon?: React.ReactNode;
  /** Icon to show when unchecked */
  uncheckedIcon?: React.ReactNode;
  /** Position of label relative to switch */
  labelPosition?: 'left' | 'right';
  /** Healthcare-specific metadata */
  medical?: {
    /** Setting category */
    category?: 'alert' | 'notification' | 'privacy' | 'sharing' | 'reminder';
    /** Priority level for medical settings */
    priority?: 'low' | 'medium' | 'high' | 'critical';
    /** Whether setting affects patient safety */
    affectsSafety?: boolean;
    /** Compliance requirement */
    compliance?: 'required' | 'recommended' | 'optional';
  };
}

/**
 * Switch component for healthcare settings and preferences.
 * 
 * Optimized for medical workflows with features like:
 * - Patient privacy controls (data sharing, research participation)
 * - Alert and notification preferences
 * - Safety-critical settings with visual indicators
 * - Compliance requirement indicators
 * - Accessibility features for healthcare providers
 * 
 * @example
 * ```tsx
 * // Patient privacy setting
 * <Switch
 *   label="Share data for research"
 *   description="Allow your anonymized medical data to be used for research"
 *   checked={shareForResearch}
 *   onChange={setShareForResearch}
 *   medical={{ 
 *     category: 'privacy',
 *     compliance: 'optional'
 *   }}
 * />
 * 
 * // Critical alert setting
 * <Switch
 *   label="Critical Lab Alerts"
 *   description="Receive immediate notifications for critical lab values"
 *   checked={criticalAlerts}
 *   onChange={setCriticalAlerts}
 *   variant="error"
 *   medical={{
 *     category: 'alert',
 *     priority: 'critical',
 *     affectsSafety: true,
 *     compliance: 'required'
 *   }}
 * />
 * ```
 */
const Switch: React.FC<SwitchProps> = ({
  checked,
  defaultChecked = false,
  onChange,
  disabled = false,
  label,
  description,
  size = 'md',
  variant = 'primary',
  className,
  name,
  id,
  loading = false,
  checkedIcon,
  uncheckedIcon,
  labelPosition = 'right',
  medical,
}) => {
  const [internalChecked, setInternalChecked] = useState(defaultChecked);
  const switchRef = useRef<HTMLButtonElement>(null);

  const isChecked = checked !== undefined ? checked : internalChecked;

  const handleToggle = () => {
    if (disabled || loading) return;

    const newChecked = !isChecked;
    setInternalChecked(newChecked);
    onChange?.(newChecked);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleToggle();
    }
  };

  const getSwitchSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          track: 'w-9 h-5',
          thumb: 'w-4 h-4',
          thumbTranslate: isChecked ? 'translate-x-4' : 'translate-x-0.5',
          thumbSize: '16px',
        };
      case 'lg':
        return {
          track: 'w-14 h-8',
          thumb: 'w-7 h-7',
          thumbTranslate: isChecked ? 'translate-x-6' : 'translate-x-0.5',
          thumbSize: '28px',
        };
      default: // md
        return {
          track: 'w-11 h-6',
          thumb: 'w-5 h-5',
          thumbTranslate: isChecked ? 'translate-x-5' : 'translate-x-0.5',
          thumbSize: '20px',
        };
    }
  };

  const getVariantClasses = () => {
    const baseClasses = 'transition-colors duration-200 ease-in-out';
    
    if (disabled) {
      return clsx(baseClasses, 'bg-gray-200');
    }

    if (loading) {
      return clsx(baseClasses, 'bg-gray-300');
    }

    if (!isChecked) {
      return clsx(baseClasses, 'bg-gray-200');
    }

    switch (variant) {
      case 'success':
        return clsx(baseClasses, 'bg-success-500');
      case 'warning':
        return clsx(baseClasses, 'bg-warning-500');
      case 'error':
        return clsx(baseClasses, 'bg-error-500');
      default: // primary
        return clsx(baseClasses, 'bg-primary-500');
    }
  };

  const getPriorityIndicator = () => {
    if (!medical?.priority || medical.priority === 'low') return null;

    const colors = {
      medium: 'bg-warning-400',
      high: 'bg-warning-500',
      critical: 'bg-error-500',
    };

    return (
      <div
        className={clsx(
          'w-2 h-2 rounded-full',
          colors[medical.priority],
          medical.priority === 'critical' && 'animate-pulse'
        )}
        title={`Priority: ${medical.priority}`}
      />
    );
  };

  const getComplianceIndicator = () => {
    if (!medical?.compliance || medical.compliance === 'optional') return null;

    return (
      <span
        className={clsx(
          'ml-2 px-1.5 py-0.5 text-xs font-medium rounded',
          medical.compliance === 'required' 
            ? 'bg-error-100 text-error-700' 
            : 'bg-warning-100 text-warning-700'
        )}
      >
        {medical.compliance}
      </span>
    );
  };

  const sizeClasses = getSwitchSizeClasses();
  const switchId = id || `switch-${label?.replace(/\s+/g, '-').toLowerCase()}`;

  const switchElement = (
    <button
      ref={switchRef}
      type="button"
      role="switch"
      aria-checked={isChecked}
      aria-describedby={description ? `${switchId}-description` : undefined}
      aria-label={label || 'Toggle switch'}
      disabled={disabled || loading}
      name={name}
      id={switchId}
      className={clsx(
        'relative inline-flex flex-shrink-0 border-2 border-transparent rounded-full cursor-pointer',
        'transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2',
        sizeClasses.track,
        getVariantClasses(),
        disabled && 'cursor-not-allowed opacity-50',
        loading && 'cursor-wait',
        variant === 'primary' && 'focus:ring-primary-500',
        variant === 'success' && 'focus:ring-success-500',
        variant === 'warning' && 'focus:ring-warning-500',
        variant === 'error' && 'focus:ring-error-500',
        // Touch-friendly sizing
        'touch-manipulation'
      )}
      onClick={handleToggle}
      onKeyDown={handleKeyDown}
    >
      <span className="sr-only">
        {label || 'Toggle switch'}
        {medical?.affectsSafety && ' (affects patient safety)'}
      </span>
      
      {/* Thumb */}
      <span
        className={clsx(
          'pointer-events-none relative inline-block rounded-full bg-white shadow transform ring-0',
          'transition duration-200 ease-in-out',
          sizeClasses.thumb,
          sizeClasses.thumbTranslate
        )}
      >
        {/* Loading Spinner */}
        {loading && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ fontSize: `${parseInt(sizeClasses.thumbSize) * 0.5}px` }}
          >
            <div className={clsx(
              'border-2 border-gray-200 border-t-gray-500 rounded-full animate-spin',
              size === 'sm' && 'w-2 h-2 border-1',
              size === 'md' && 'w-3 h-3',
              size === 'lg' && 'w-4 h-4'
            )} />
          </div>
        )}

        {/* Icons */}
        {!loading && (isChecked ? checkedIcon : uncheckedIcon) && (
          <div
            className="absolute inset-0 flex items-center justify-center text-gray-500"
            style={{ fontSize: `${parseInt(sizeClasses.thumbSize) * 0.6}px` }}
          >
            {isChecked ? checkedIcon : uncheckedIcon}
          </div>
        )}
      </span>
    </button>
  );

  const labelElement = label && (
    <div className="flex-1 min-w-0">
      <div className="flex items-center">
        <label
          htmlFor={switchId}
          className={clsx(
            'text-sm font-medium text-gray-900 cursor-pointer',
            disabled && 'cursor-not-allowed opacity-50'
          )}
        >
          {label}
        </label>
        
        {getPriorityIndicator()}
        {getComplianceIndicator()}
        
        {medical?.affectsSafety && (
          <span
            className="ml-2 text-xs bg-error-100 text-error-700 px-1.5 py-0.5 rounded"
            title="This setting affects patient safety"
          >
            Safety Critical
          </span>
        )}
      </div>
      
      {description && (
        <p
          id={`${switchId}-description`}
          className={clsx(
            'text-sm text-gray-600 mt-0.5',
            disabled && 'opacity-50'
          )}
        >
          {description}
        </p>
      )}
    </div>
  );

  if (!label) {
    return switchElement;
  }

  return (
    <div className={clsx('flex items-start space-x-3', className)}>
      {labelPosition === 'left' && labelElement}
      {switchElement}
      {labelPosition === 'right' && labelElement}
    </div>
  );
};

export default Switch;
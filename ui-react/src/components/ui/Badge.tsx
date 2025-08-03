import React from 'react';
import { clsx } from 'clsx';
import type { BadgeProps } from '@/types/ui';

const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  dot = false,
  count,
  showZero = false,
  overflowCount = 99,
  status,
  children,
  className,
}) => {
  // Healthcare status mapping
  const statusVariantMap = {
    approved: 'success',
    pending: 'warning',
    denied: 'error',
    processing: 'info',
    cancelled: 'default',
    expired: 'error',
  } as const;

  const finalVariant = status ? statusVariantMap[status] : variant;

  const baseClasses = 'inline-flex items-center font-medium rounded-full transition-colors';

  const variantClasses = {
    default: 'bg-gray-100 text-gray-800 border border-gray-200',
    primary: 'bg-primary-100 text-primary-800 border border-primary-200',
    secondary: 'bg-gray-100 text-gray-700 border border-gray-300',
    success: 'bg-success-100 text-success-800 border border-success-200',
    warning: 'bg-warning-100 text-warning-800 border border-warning-200',
    error: 'bg-error-100 text-error-800 border border-error-200',
    info: 'bg-blue-100 text-blue-800 border border-blue-200',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  const dotClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  };

  // Handle count display
  const shouldShowCount = count !== undefined && (count > 0 || showZero);
  const displayCount = count !== undefined && count > overflowCount ? `${overflowCount}+` : count;

  if (dot) {
    return (
      <span className={clsx('relative inline-flex', className)}>
        {children}
        <span
          className={clsx(
            'absolute -top-1 -right-1 rounded-full',
            dotClasses[size],
            variantClasses[finalVariant].replace('text-', 'bg-').replace('-100', '-500')
          )}
        />
      </span>
    );
  }

  if (shouldShowCount && children) {
    return (
      <span className={clsx('relative inline-flex', className)}>
        {children}
        <span
          className={clsx(
            'absolute -top-2 -right-2 min-w-5 h-5 flex items-center justify-center rounded-full text-xs font-medium text-white',
            count === 0 ? 'bg-gray-400' : 'bg-error-500'
          )}
        >
          {displayCount}
        </span>
      </span>
    );
  }

  return (
    <span
      className={clsx(
        baseClasses,
        variantClasses[finalVariant],
        sizeClasses[size],
        className
      )}
    >
      {shouldShowCount ? displayCount : children}
    </span>
  );
};

// Healthcare status badges with predefined styling
export const StatusBadge: React.FC<{ status: string; label?: string }> = ({ status, label }) => {
  const statusConfig = {
    approved: { variant: 'success' as const, label: label || 'Approved' },
    pending: { variant: 'warning' as const, label: label || 'Pending' },
    denied: { variant: 'error' as const, label: label || 'Denied' },
    processing: { variant: 'info' as const, label: label || 'Processing' },
    cancelled: { variant: 'default' as const, label: label || 'Cancelled' },
    expired: { variant: 'error' as const, label: label || 'Expired' },
    active: { variant: 'success' as const, label: label || 'Active' },
    inactive: { variant: 'default' as const, label: label || 'Inactive' },
  };

  const config = statusConfig[status as keyof typeof statusConfig] || { variant: 'default' as const, label: status };

  return <Badge variant={config.variant}>{config.label}</Badge>;
};

// Priority badge for medical cases
export const PriorityBadge: React.FC<{ priority: 'low' | 'medium' | 'high' | 'urgent' }> = ({ priority }) => {
  const priorityConfig = {
    low: { variant: 'default' as const, label: 'Low' },
    medium: { variant: 'info' as const, label: 'Medium' },
    high: { variant: 'warning' as const, label: 'High' },
    urgent: { variant: 'error' as const, label: 'Urgent' },
  };

  const config = priorityConfig[priority];

  return <Badge variant={config.variant}>{config.label}</Badge>;
};

export default Badge;
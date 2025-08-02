import React from 'react';
import { clsx } from 'clsx';
import type { ButtonProps } from '@/types/ui';
import LoadingSpinner from './LoadingSpinner';

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  children,
  onClick,
  className,
  ...props
}) => {
  const baseClasses = 'btn focus-ring';
  
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    tertiary: 'btn-tertiary',
    danger: 'btn-danger',
  };
  
  const sizeClasses = {
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg',
  };

  return (
    <button
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        (disabled || loading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <LoadingSpinner size="sm" className="mr-2 !border-current" />
      )}
      {children}
    </button>
  );
};

export default Button;
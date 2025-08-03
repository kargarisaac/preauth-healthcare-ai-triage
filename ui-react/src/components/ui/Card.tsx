import React from 'react';
import { clsx } from 'clsx';
import type { CardProps } from '@/types/ui';

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  className,
  padding = 'md'
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div className={clsx('card', className)}>
      {(title || subtitle) && (
        <div className="card-header">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary">{title}</h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 dark:text-dark-text-secondary mt-1">{subtitle}</p>
          )}
        </div>
      )}
      <div className={clsx('card-body', paddingClasses[padding])}>
        {children}
      </div>
    </div>
  );
};

export default Card;
export { Card };

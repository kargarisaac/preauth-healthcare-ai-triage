import React from 'react';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  Calendar,
  DollarSign,
  FileText,
  Activity,
} from 'lucide-react';
import type {
  RequestStatus,
  RequestPriority,
  RequestType,
  StatusBadgeConfig,
} from '@/types/requests';

// Status configurations with icons and colors
const STATUS_CONFIGS: Record<RequestStatus, StatusBadgeConfig> = {
  approved: {
    icon: 'check-circle',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    label: 'Approved',
  },
  pending: {
    icon: 'clock',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    label: 'Pending',
  },
  denied: {
    icon: 'x-circle',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
    label: 'Denied',
  },
  under_review: {
    icon: 'alert-triangle',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
    label: 'Under Review',
  },
  cancelled: {
    icon: 'x-circle',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    label: 'Cancelled',
  },
  expired: {
    icon: 'clock',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    label: 'Expired',
  },
};

// Priority configurations
const PRIORITY_CONFIGS: Record<RequestPriority, StatusBadgeConfig> = {
  low: {
    icon: 'activity',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    label: 'Low',
  },
  medium: {
    icon: 'activity',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    label: 'Medium',
  },
  high: {
    icon: 'activity',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
    label: 'High',
  },
  urgent: {
    icon: 'alert-triangle',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    label: 'Urgent',
  },
};

// Type configurations
const TYPE_CONFIGS: Record<RequestType, StatusBadgeConfig> = {
  authorization: {
    icon: 'file-text',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    label: 'Authorization',
  },
  claim: {
    icon: 'dollar-sign',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    label: 'Claim',
  },
  reimbursement: {
    icon: 'activity',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    label: 'Reimbursement',
  },
  eligibility: {
    icon: 'user',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
    label: 'Eligibility',
  },
};

// Helper function to get icon component
const getIconComponent = (iconName: string) => {
  switch (iconName) {
    case 'check-circle':
      return CheckCircle;
    case 'x-circle':
      return XCircle;
    case 'clock':
      return Clock;
    case 'alert-triangle':
      return AlertTriangle;
    case 'user':
      return User;
    case 'calendar':
      return Calendar;
    case 'dollar-sign':
      return DollarSign;
    case 'file-text':
      return FileText;
    case 'activity':
      return Activity;
    default:
      return Activity;
  }
};

// Base badge component
interface BadgeProps {
  config: StatusBadgeConfig;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  config,
  size = 'md',
  showIcon = true,
  className = '',
}) => {
  const Icon = getIconComponent(config.icon);
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${config.bgColor} ${config.color} ${sizeClasses[size]} ${className}`}
    >
      {showIcon && <Icon className={`${iconSizes[size]} mr-1`} />}
      {config.label}
    </span>
  );
};

// Status badge component
interface StatusBadgeProps {
  status: RequestStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const config = STATUS_CONFIGS[status];
  return (
    <Badge
      config={config}
      size={size}
      showIcon={showIcon}
      className={className}
    />
  );
};

// Priority badge component
interface PriorityBadgeProps {
  priority: RequestPriority;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({
  priority,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const config = PRIORITY_CONFIGS[priority];
  return (
    <Badge
      config={config}
      size={size}
      showIcon={showIcon}
      className={className}
    />
  );
};

// Type badge component
interface TypeBadgeProps {
  type: RequestType;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export const TypeBadge: React.FC<TypeBadgeProps> = ({
  type,
  size = 'md',
  showIcon = true,
  className,
}) => {
  const config = TYPE_CONFIGS[type];
  return (
    <Badge
      config={config}
      size={size}
      showIcon={showIcon}
      className={className}
    />
  );
};

// Combined status and priority badge
interface StatusWithPriorityProps {
  status: RequestStatus;
  priority: RequestPriority;
  showIcons?: boolean;
  className?: string;
}

export const StatusWithPriority: React.FC<StatusWithPriorityProps> = ({
  status,
  priority,
  showIcons = true,
  className = '',
}) => {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <StatusBadge status={status} size="sm" showIcon={showIcons} />
      <PriorityBadge priority={priority} size="sm" showIcon={showIcons} />
    </div>
  );
};

// Amount badge with currency formatting
interface AmountBadgeProps {
  amount: number;
  currency: string;
  type?: 'requested' | 'approved' | 'denied';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const AmountBadge: React.FC<AmountBadgeProps> = ({
  amount,
  currency,
  type = 'requested',
  size = 'md',
  className = '',
}) => {
  const typeColors = {
    requested: 'bg-blue-100 text-blue-700',
    approved: 'bg-green-100 text-green-700',
    denied: 'bg-red-100 text-red-700',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  const formattedAmount = new Intl.NumberFormat('en-AE', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${typeColors[type]} ${sizeClasses[size]} ${className}`}
    >
      <DollarSign className="w-3 h-3 mr-1" />
      {formattedAmount}
    </span>
  );
};

// Processing time badge
interface ProcessingTimeBadgeProps {
  seconds: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const ProcessingTimeBadge: React.FC<ProcessingTimeBadgeProps> = ({
  seconds,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  };

  const getTimeColor = (seconds: number): string => {
    if (seconds < 300) return 'bg-green-100 text-green-700'; // < 5 min - fast
    if (seconds < 1800) return 'bg-yellow-100 text-yellow-700'; // < 30 min - normal
    return 'bg-red-100 text-red-700'; // > 30 min - slow
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${getTimeColor(seconds)} ${sizeClasses[size]} ${className}`}
    >
      <Clock className="w-3 h-3 mr-1" />
      {formatTime(seconds)}
    </span>
  );
};

// Custom badge for any text with configurable colors
interface CustomBadgeProps {
  text: string;
  color?: 'gray' | 'red' | 'yellow' | 'green' | 'blue' | 'indigo' | 'purple' | 'pink';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
}

export const CustomBadge: React.FC<CustomBadgeProps> = ({
  text,
  color = 'gray',
  size = 'md',
  icon: Icon,
  className = '',
}) => {
  const colorClasses = {
    gray: 'bg-gray-100 text-gray-700',
    red: 'bg-red-100 text-red-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    indigo: 'bg-indigo-100 text-indigo-700',
    purple: 'bg-purple-100 text-purple-700',
    pink: 'bg-pink-100 text-pink-700',
  };
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${colorClasses[color]} ${sizeClasses[size]} ${className}`}
    >
      {Icon && <Icon className={`${iconSizes[size]} mr-1`} />}
      {text}
    </span>
  );
};

// Export all status configurations for external use
export { STATUS_CONFIGS, PRIORITY_CONFIGS, TYPE_CONFIGS };
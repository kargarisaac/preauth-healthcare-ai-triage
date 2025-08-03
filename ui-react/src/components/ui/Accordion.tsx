import React, { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, AlertTriangle, Clock, CheckCircle } from 'lucide-react';

export interface AccordionItem {
  /** Unique identifier for the accordion item */
  id: string;
  /** Title displayed in the accordion header */
  title: string;
  /** Content to display when expanded */
  content: React.ReactNode;
  /** Icon component to display next to the title */
  icon?: React.ComponentType<{ className?: string }>;
  /** Whether the item is disabled */
  disabled?: boolean;
  /** Default expanded state */
  defaultExpanded?: boolean;
  /** Badge content (e.g., count, status) */
  badge?: string | number;
  /** Badge variant for different styling */
  badgeVariant?: 'default' | 'warning' | 'error' | 'success';
  /** Healthcare-specific metadata */
  metadata?: {
    /** Medical priority level */
    priority?: 'low' | 'medium' | 'high' | 'critical';
    /** Last updated timestamp */
    lastUpdated?: Date;
    /** Status of medical information */
    status?: 'current' | 'historical' | 'pending' | 'requires_review';
    /** Medical category */
    category?: 'condition' | 'medication' | 'allergy' | 'procedure' | 'vital' | 'note';
  };
}

export interface AccordionProps {
  /** Array of accordion items */
  items: AccordionItem[];
  /** Whether multiple items can be expanded at once */
  allowMultiple?: boolean;
  /** Default expanded items (for uncontrolled usage) */
  defaultExpanded?: string[];
  /** Controlled expanded items */
  expanded?: string[];
  /** Callback when expansion state changes */
  onExpandedChange?: (expandedIds: string[]) => void;
  /** Accordion styling variant */
  variant?: 'default' | 'bordered' | 'filled' | 'minimal';
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Custom class name */
  className?: string;
  /** Whether to show priority indicators */
  showPriorityIndicators?: boolean;
  /** Whether to show status indicators */
  showStatusIndicators?: boolean;
  /** Loading state */
  loading?: boolean;
}

/**
 * Accordion component for organizing collapsible healthcare information.
 * 
 * Perfect for medical records with features like:
 * - Priority indicators for critical conditions
 * - Status badges for medical information states
 * - Metadata support for medical categories
 * - Smooth animations with proper accessibility
 * - Keyboard navigation (Tab, Enter, Space, Arrow keys)
 * 
 * @example
 * ```tsx
 * const medicalSections = [
 *   {
 *     id: 'conditions',
 *     title: 'Active Conditions',
 *     icon: Heart,
 *     badge: 3,
 *     badgeVariant: 'error',
 *     content: <ConditionsList />,
 *     metadata: { 
 *       priority: 'high', 
 *       status: 'current',
 *       category: 'condition'
 *     }
 *   },
 *   {
 *     id: 'medications',
 *     title: 'Current Medications',
 *     icon: Pill,
 *     badge: 5,
 *     content: <MedicationsList />,
 *     metadata: { priority: 'medium', status: 'current' }
 *   }
 * ];
 * 
 * <Accordion 
 *   items={medicalSections}
 *   allowMultiple
 *   showPriorityIndicators
 *   showStatusIndicators
 * />
 * ```
 */
const Accordion: React.FC<AccordionProps> = ({
  items,
  allowMultiple = false,
  defaultExpanded = [],
  expanded,
  onExpandedChange,
  variant = 'default',
  size = 'md',
  className,
  showPriorityIndicators = false,
  showStatusIndicators = false,
  loading = false,
}) => {
  const [internalExpanded, setInternalExpanded] = useState<string[]>(defaultExpanded);
  const contentRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const currentExpanded = expanded || internalExpanded;

  useEffect(() => {
    if (expanded) {
      setInternalExpanded(expanded);
    }
  }, [expanded]);

  const handleToggle = (itemId: string) => {
    const item = items.find(item => item.id === itemId);
    if (item?.disabled) return;

    let newExpanded: string[];

    if (allowMultiple) {
      newExpanded = currentExpanded.includes(itemId)
        ? currentExpanded.filter(id => id !== itemId)
        : [...currentExpanded, itemId];
    } else {
      newExpanded = currentExpanded.includes(itemId) ? [] : [itemId];
    }

    setInternalExpanded(newExpanded);
    onExpandedChange?.(newExpanded);
  };

  const handleKeyDown = (event: React.KeyboardEvent, itemId: string) => {
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        handleToggle(itemId);
        break;
      case 'ArrowDown':
        event.preventDefault();
        focusNextItem(itemId);
        break;
      case 'ArrowUp':
        event.preventDefault();
        focusPreviousItem(itemId);
        break;
      case 'Home':
        event.preventDefault();
        focusFirstItem();
        break;
      case 'End':
        event.preventDefault();
        focusLastItem();
        break;
    }
  };

  const focusNextItem = (currentId: string) => {
    const currentIndex = items.findIndex(item => item.id === currentId);
    const nextIndex = (currentIndex + 1) % items.length;
    const nextButton = document.querySelector(`[data-accordion-trigger="${items[nextIndex].id}"]`) as HTMLButtonElement;
    nextButton?.focus();
  };

  const focusPreviousItem = (currentId: string) => {
    const currentIndex = items.findIndex(item => item.id === currentId);
    const prevIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
    const prevButton = document.querySelector(`[data-accordion-trigger="${items[prevIndex].id}"]`) as HTMLButtonElement;
    prevButton?.focus();
  };

  const focusFirstItem = () => {
    const firstButton = document.querySelector(`[data-accordion-trigger="${items[0].id}"]`) as HTMLButtonElement;
    firstButton?.focus();
  };

  const focusLastItem = () => {
    const lastButton = document.querySelector(`[data-accordion-trigger="${items[items.length - 1].id}"]`) as HTMLButtonElement;
    lastButton?.focus();
  };

  const getPriorityIcon = (priority?: string) => {
    switch (priority) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-error-500" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />;
      case 'medium':
        return <Clock className="w-4 h-4 text-primary-500" />;
      default:
        return null;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'current':
        return <CheckCircle className="w-4 h-4 text-success-500" />;
      case 'requires_review':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-primary-500" />;
      default:
        return null;
    }
  };

  const getItemClasses = (variant: string) => {
    const baseClasses = 'mb-2 last:mb-0';
    
    const variantClasses = {
      default: 'border border-gray-200 rounded-lg',
      bordered: 'border border-gray-300 rounded-lg shadow-soft',
      filled: 'bg-gray-50 border border-gray-200 rounded-lg',
      minimal: 'border-b border-gray-200 last:border-b-0 rounded-none',
    };

    return clsx(baseClasses, variantClasses[variant]);
  };

  const getHeaderClasses = (variant: string, size: string, isExpanded: boolean, disabled: boolean) => {
    const baseClasses = 'w-full flex items-center justify-between text-left transition-all duration-200 focus-ring group';
    
    const sizeClasses = {
      sm: 'px-3 py-2 text-sm',
      md: 'px-4 py-3 text-base',
      lg: 'px-6 py-4 text-lg',
    };

    const variantClasses = {
      default: clsx(
        'hover:bg-gray-50',
        variant === 'default' && 'rounded-lg',
        variant === 'bordered' && 'rounded-lg',
        variant === 'filled' && 'rounded-lg bg-gray-50 hover:bg-gray-100',
        variant === 'minimal' && 'hover:bg-gray-50'
      ),
      bordered: 'hover:bg-gray-50 rounded-lg',
      filled: 'bg-gray-50 hover:bg-gray-100 rounded-lg',
      minimal: 'hover:bg-gray-50',
    };

    const stateClasses = clsx(
      isExpanded && variant !== 'minimal' && 'bg-gray-50',
      disabled && 'opacity-50 cursor-not-allowed'
    );

    return clsx(
      baseClasses,
      sizeClasses[size],
      variantClasses[variant],
      stateClasses,
      // Touch-friendly minimum height
      'min-h-[44px]'
    );
  };

  const getBadgeClasses = (badgeVariant?: string) => {
    const baseClasses = 'ml-2 inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium';
    
    const variantClasses = {
      default: 'bg-gray-100 text-gray-700',
      warning: 'bg-warning-100 text-warning-700',
      error: 'bg-error-100 text-error-700',
      success: 'bg-success-100 text-success-700',
    };

    return clsx(baseClasses, variantClasses[badgeVariant as keyof typeof variantClasses] || variantClasses.default);
  };

  if (loading) {
    return (
      <div className={clsx('space-y-3', className)}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-gray-200 rounded-lg">
            <div className="h-12 bg-gray-200 rounded-t-lg animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={clsx('w-full', className)} role="region" aria-label="Medical information sections">
      {items.map((item) => {
        const isExpanded = currentExpanded.includes(item.id);
        const IconComponent = item.icon;
        const priorityIcon = showPriorityIndicators ? getPriorityIcon(item.metadata?.priority) : null;
        const statusIcon = showStatusIndicators ? getStatusIcon(item.metadata?.status) : null;

        return (
          <div key={item.id} className={getItemClasses(variant)}>
            {/* Header */}
            <button
              data-accordion-trigger={item.id}
              type="button"
              className={getHeaderClasses(variant, size, isExpanded, !!item.disabled)}
              aria-expanded={isExpanded}
              aria-controls={`accordion-content-${item.id}`}
              aria-describedby={item.metadata ? `accordion-meta-${item.id}` : undefined}
              disabled={item.disabled}
              onClick={() => handleToggle(item.id)}
              onKeyDown={(e) => handleKeyDown(e, item.id)}
            >
              <div className="flex items-center min-w-0 flex-1">
                {/* Priority Indicator */}
                {priorityIcon && (
                  <div className="mr-2 flex-shrink-0" aria-label={`Priority: ${item.metadata?.priority}`}>
                    {priorityIcon}
                  </div>
                )}

                {/* Icon */}
                {IconComponent && (
                  <IconComponent className="w-5 h-5 mr-3 text-gray-500 flex-shrink-0" />
                )}

                {/* Title */}
                <span className="font-medium text-gray-900 truncate">
                  {item.title}
                </span>

                {/* Badge */}
                {item.badge && (
                  <span className={getBadgeClasses(item.badgeVariant)}>
                    {item.badge}
                  </span>
                )}

                {/* Status Indicator */}
                {statusIcon && (
                  <div className="ml-2 flex-shrink-0" aria-label={`Status: ${item.metadata?.status}`}>
                    {statusIcon}
                  </div>
                )}
              </div>

              {/* Chevron */}
              <ChevronDown
                className={clsx(
                  'w-5 h-5 text-gray-500 transition-transform duration-200 flex-shrink-0 ml-2',
                  isExpanded && 'transform rotate-180'
                )}
                aria-hidden="true"
              />
            </button>

            {/* Content */}
            <div
              id={`accordion-content-${item.id}`}
              ref={(el) => {
                if (el) {
                  contentRefs.current.set(item.id, el);
                } else {
                  contentRefs.current.delete(item.id);
                }
              }}
              className={clsx(
                'overflow-hidden transition-all duration-300 ease-in-out',
                isExpanded ? 'max-h-none opacity-100' : 'max-h-0 opacity-0'
              )}
              aria-hidden={!isExpanded}
            >
              <div className={clsx(
                'px-4 pb-4',
                size === 'sm' && 'px-3 pb-3',
                size === 'lg' && 'px-6 pb-6',
                variant === 'filled' && 'bg-white mx-3 mb-3 rounded-lg border',
                variant === 'minimal' && 'border-t border-gray-200 pt-3'
              )}>
                {item.content}

                {/* Metadata */}
                {item.metadata && (
                  <div id={`accordion-meta-${item.id}`} className="sr-only">
                    {item.metadata.priority && `Priority: ${item.metadata.priority}. `}
                    {item.metadata.status && `Status: ${item.metadata.status}. `}
                    {item.metadata.category && `Category: ${item.metadata.category}. `}
                    {item.metadata.lastUpdated && `Last updated: ${item.metadata.lastUpdated.toLocaleDateString()}.`}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Accordion;
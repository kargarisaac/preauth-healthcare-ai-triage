import React, { useState, useEffect, useRef } from 'react';
import { clsx } from 'clsx';

export interface TabItem {
  /** Unique identifier for the tab */
  id: string;
  /** Display label for the tab */
  label: string;
  /** Content to display when tab is active */
  content?: React.ReactNode;
  /** Icon component to display next to the label */
  icon?: React.ComponentType<{ className?: string }>;
  /** Whether the tab is disabled */
  disabled?: boolean;
  /** Badge content (e.g., count, status) */
  badge?: string | number;
  /** Badge variant for different styling */
  badgeVariant?: 'default' | 'warning' | 'error' | 'success';
  /** Healthcare-specific metadata */
  metadata?: {
    /** Medical record section type */
    recordType?: 'overview' | 'history' | 'vitals' | 'medications' | 'allergies' | 'procedures' | 'notes';
    /** Priority level for medical information */
    priority?: 'low' | 'medium' | 'high' | 'critical';
    /** Last updated timestamp */
    lastUpdated?: Date;
    /** Whether section requires attention */
    requiresAttention?: boolean;
  };
}

export interface TabsProps {
  /** Array of tab items */
  items: TabItem[];
  /** Currently active tab ID */
  activeTab?: string;
  /** Default active tab (for uncontrolled usage) */
  defaultActiveTab?: string;
  /** Callback when tab changes */
  onTabChange?: (tabId: string) => void;
  /** Tab styling variant */
  variant?: 'default' | 'pills' | 'underline' | 'cards';
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Whether tabs are full width */
  fullWidth?: boolean;
  /** Custom class name */
  className?: string;
  /** Whether to show content area */
  showContent?: boolean;
  /** Custom content area class name */
  contentClassName?: string;
  /** Whether tabs are scrollable horizontally */
  scrollable?: boolean;
  /** Loading state */
  loading?: boolean;
}

/**
 * Tabs component for organizing healthcare information into sections.
 * 
 * Optimized for medical workflows with features like:
 * - Priority indicators for critical information
 * - Attention badges for sections requiring review
 * - Metadata support for medical record types
 * - Responsive scrolling for many tabs
 * - Keyboard navigation (Arrow keys, Tab, Enter, Space)
 * 
 * @example
 * ```tsx
 * const patientTabs = [
 *   {
 *     id: 'overview',
 *     label: 'Overview',
 *     icon: User,
 *     content: <PatientOverview />,
 *     metadata: { recordType: 'overview' }
 *   },
 *   {
 *     id: 'medications',
 *     label: 'Medications',
 *     icon: Pill,
 *     badge: 5,
 *     badgeVariant: 'warning',
 *     content: <MedicationList />,
 *     metadata: { recordType: 'medications', requiresAttention: true }
 *   }
 * ];
 * 
 * <Tabs 
 *   items={patientTabs}
 *   variant="underline"
 *   onTabChange={(tabId) => setActiveSection(tabId)}
 * />
 * ```
 */
const Tabs: React.FC<TabsProps> = ({
  items,
  activeTab,
  defaultActiveTab,
  onTabChange,
  variant = 'default',
  size = 'md',
  fullWidth = false,
  className,
  showContent = true,
  contentClassName,
  scrollable = false,
  loading = false,
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState(
    activeTab || defaultActiveTab || items[0]?.id || ''
  );
  const [focusedTab, setFocusedTab] = useState<string | null>(null);
  const tabListRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  const currentActiveTab = activeTab || internalActiveTab;
  const activeItem = items.find(item => item.id === currentActiveTab);

  useEffect(() => {
    if (activeTab) {
      setInternalActiveTab(activeTab);
    }
  }, [activeTab]);

  const handleTabClick = (tabId: string) => {
    const tab = items.find(item => item.id === tabId);
    if (tab?.disabled) return;

    setInternalActiveTab(tabId);
    onTabChange?.(tabId);
  };

  const handleKeyDown = (event: React.KeyboardEvent, tabId: string) => {
    const currentIndex = items.findIndex(item => item.id === tabId);
    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault();
        newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        break;
      case 'ArrowRight':
        event.preventDefault();
        newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        break;
      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        newIndex = items.length - 1;
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        handleTabClick(tabId);
        return;
      default:
        return;
    }

    // Find next non-disabled tab
    while (items[newIndex]?.disabled && newIndex !== currentIndex) {
      if (event.key === 'ArrowLeft' || event.key === 'End') {
        newIndex = newIndex > 0 ? newIndex - 1 : items.length - 1;
      } else {
        newIndex = newIndex < items.length - 1 ? newIndex + 1 : 0;
      }
    }

    const nextTab = items[newIndex];
    if (nextTab && !nextTab.disabled) {
      setFocusedTab(nextTab.id);
      tabRefs.current.get(nextTab.id)?.focus();
    }
  };

  const getTabClasses = (item: TabItem, isActive: boolean) => {
    const baseClasses = 'relative inline-flex items-center justify-center transition-all duration-200 focus-ring';
    
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    const variantClasses = {
      default: clsx(
        'border-b-2 font-medium',
        isActive 
          ? 'border-primary-500 text-primary-600' 
          : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
      ),
      pills: clsx(
        'rounded-lg font-medium',
        isActive 
          ? 'bg-primary-100 text-primary-700' 
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      ),
      underline: clsx(
        'border-b-2 font-medium',
        isActive 
          ? 'border-primary-500 text-primary-600' 
          : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
      ),
      cards: clsx(
        'rounded-t-lg border border-b-0 font-medium',
        isActive 
          ? 'bg-white border-gray-300 text-gray-900' 
          : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
      ),
    };

    const disabledClasses = item.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';
    const attentionClasses = item.metadata?.requiresAttention ? 'animate-pulse-slow' : '';

    return clsx(
      baseClasses,
      sizeClasses[size],
      variantClasses[variant],
      disabledClasses,
      attentionClasses,
      fullWidth && 'flex-1',
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
      <div className={clsx('space-y-4', className)}>
        <div className="flex space-x-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded animate-pulse w-24" />
          ))}
        </div>
        {showContent && (
          <div className="h-64 bg-gray-100 rounded animate-pulse" />
        )}
      </div>
    );
  }

  return (
    <div className={clsx('w-full', className)}>
      {/* Tab List */}
      <div
        ref={tabListRef}
        className={clsx(
          'flex',
          scrollable ? 'overflow-x-auto scrollbar-hide' : 'flex-wrap',
          variant === 'cards' && 'border-b border-gray-300'
        )}
        role="tablist"
        aria-label="Medical record sections"
      >
        {items.map((item) => {
          const isActive = item.id === currentActiveTab;
          const IconComponent = item.icon;

          return (
            <button
              key={item.id}
              ref={(el) => {
                if (el) {
                  tabRefs.current.set(item.id, el);
                } else {
                  tabRefs.current.delete(item.id);
                }
              }}
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${item.id}`}
              aria-label={`${item.label}${item.metadata?.requiresAttention ? ' (requires attention)' : ''}${item.badge ? ` (${item.badge} items)` : ''}`}
              tabIndex={isActive ? 0 : -1}
              disabled={item.disabled}
              className={getTabClasses(item, isActive)}
              onClick={() => handleTabClick(item.id)}
              onKeyDown={(e) => handleKeyDown(e, item.id)}
              onFocus={() => setFocusedTab(item.id)}
              onBlur={() => setFocusedTab(null)}
            >
              {IconComponent && (
                <IconComponent 
                  className={clsx(
                    'w-4 h-4',
                    item.label && 'mr-2'
                  )} 
                />
              )}
              
              <span>{item.label}</span>

              {item.badge && (
                <span className={getBadgeClasses(item.badgeVariant)}>
                  {item.badge}
                </span>
              )}

              {item.metadata?.requiresAttention && (
                <span 
                  className="ml-2 w-2 h-2 bg-error-500 rounded-full animate-pulse"
                  aria-hidden="true"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {showContent && activeItem && (
        <div
          id={`tabpanel-${activeItem.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${activeItem.id}`}
          className={clsx(
            'mt-4 focus:outline-none',
            variant === 'cards' && 'bg-white border border-gray-300 border-t-0 rounded-b-lg p-6',
            contentClassName
          )}
          tabIndex={0}
        >
          {activeItem.content}
        </div>
      )}
    </div>
  );
};

export default Tabs;
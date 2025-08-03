import React from 'react';
import { clsx } from 'clsx';
import { ChevronRight, Home } from 'lucide-react';

export interface BreadcrumbItem {
  /** Unique identifier for the breadcrumb item */
  id: string;
  /** Display text for the breadcrumb */
  label: string;
  /** URL or path for navigation */
  href?: string;
  /** Icon component to display next to the label */
  icon?: React.ComponentType<{ className?: string }>;
  /** Whether this item is currently active (last item) */
  isActive?: boolean;
  /** Additional metadata for healthcare contexts */
  metadata?: {
    /** Patient ID or medical record number */
    patientId?: string;
    /** Medical record section type */
    recordType?: 'demographics' | 'history' | 'vitals' | 'medications' | 'allergies' | 'procedures';
    /** Visit or appointment ID */
    visitId?: string;
  };
}

export interface BreadcrumbsProps {
  /** Array of breadcrumb items to display */
  items: BreadcrumbItem[];
  /** Custom separator icon between items */
  separator?: React.ComponentType<{ className?: string }>;
  /** Show home icon for first item */
  showHomeIcon?: boolean;
  /** Maximum number of items to show before collapsing */
  maxItems?: number;
  /** Custom class name for styling */
  className?: string;
  /** Callback when a breadcrumb item is clicked */
  onItemClick?: (item: BreadcrumbItem) => void;
  /** Whether to show tooltips with metadata on hover */
  showTooltips?: boolean;
}

/**
 * Breadcrumbs component for navigation trails in healthcare applications.
 * 
 * Provides clear navigation hierarchy for deep page structures like:
 * - Patient Records → Demographics → Contact Information
 * - Medical History → Conditions → Diabetes Management
 * - Appointments → Today → Patient Details
 * 
 * Features:
 * - Healthcare-specific metadata support
 * - Keyboard navigation (Tab, Enter, Space)
 * - Responsive design with item collapsing
 * - Screen reader friendly with proper ARIA labels
 * - Touch-friendly for mobile devices
 * 
 * @example
 * ```tsx
 * const breadcrumbs = [
 *   { id: 'home', label: 'Dashboard', href: '/' },
 *   { id: 'patients', label: 'Patients', href: '/patients' },
 *   { id: 'patient', label: 'John Smith', href: '/patients/123', 
 *     metadata: { patientId: '123', recordType: 'demographics' } },
 *   { id: 'demographics', label: 'Demographics', isActive: true }
 * ];
 * 
 * <Breadcrumbs 
 *   items={breadcrumbs}
 *   onItemClick={(item) => navigate(item.href)}
 *   showTooltips
 * />
 * ```
 */
const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  separator: Separator = ChevronRight,
  showHomeIcon = true,
  maxItems = 5,
  className,
  onItemClick,
  showTooltips = false,
}) => {
  // Handle item collapsing when there are too many items
  const displayItems = React.useMemo(() => {
    if (items.length <= maxItems) {
      return items;
    }

    const firstItem = items[0];
    const lastItems = items.slice(-2); // Keep last 2 items
    const collapsedCount = items.length - 3; // First + last 2 items

    return [
      firstItem,
      {
        id: 'collapsed',
        label: `... (${collapsedCount} more)`,
        isCollapsed: true,
      },
      ...lastItems,
    ];
  }, [items, maxItems]);

  const handleItemClick = (item: BreadcrumbItem, event: React.KeyboardEvent | React.MouseEvent) => {
    if ('key' in event && event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    event.preventDefault();
    if (onItemClick && !item.isActive && !(item as any).isCollapsed) {
      onItemClick(item);
    }
  };

  const getTooltipContent = (item: BreadcrumbItem) => {
    if (!showTooltips || !item.metadata) return undefined;

    const { patientId, recordType, visitId } = item.metadata;
    const parts = [];
    
    if (patientId) parts.push(`Patient: ${patientId}`);
    if (recordType) parts.push(`Section: ${recordType}`);
    if (visitId) parts.push(`Visit: ${visitId}`);
    
    return parts.join(' • ');
  };

  return (
    <nav
      aria-label="Breadcrumb navigation"
      className={clsx('flex items-center space-x-1 text-sm', className)}
      role="navigation"
    >
      <ol className="flex items-center space-x-1" role="list">
        {displayItems.map((item, index) => {
          const isLast = index === displayItems.length - 1;
          const isCollapsed = (item as any).isCollapsed;
          const IconComponent = item.icon;
          const tooltipContent = getTooltipContent(item);

          return (
            <li key={item.id} className="flex items-center space-x-1" role="listitem">
              {/* Breadcrumb Item */}
              <div className="flex items-center">
                {index === 0 && showHomeIcon && !IconComponent && (
                  <Home className="w-4 h-4 mr-1 text-gray-500" aria-hidden="true" />
                )}
                
                {IconComponent && (
                  <IconComponent className="w-4 h-4 mr-1 text-gray-500" aria-hidden="true" />
                )}

                {isCollapsed ? (
                  <span
                    className="text-gray-500 cursor-default"
                    aria-label={`${(item as any).label} - navigation items collapsed`}
                  >
                    {item.label}
                  </span>
                ) : item.isActive || isLast ? (
                  <span
                    className="font-medium text-gray-900 cursor-default"
                    aria-current="page"
                    title={tooltipContent}
                  >
                    {item.label}
                  </span>
                ) : (
                  <button
                    type="button"
                    className={clsx(
                      'text-gray-600 hover:text-gray-900 focus:text-gray-900',
                      'transition-colors duration-200 rounded-sm focus-ring',
                      'touch-manipulation min-h-[44px] flex items-center px-1 -mx-1'
                    )}
                    onClick={(e) => handleItemClick(item, e)}
                    onKeyDown={(e) => handleItemClick(item, e)}
                    title={tooltipContent}
                    aria-label={`Navigate to ${item.label}${tooltipContent ? ` (${tooltipContent})` : ''}`}
                  >
                    {item.label}
                  </button>
                )}
              </div>

              {/* Separator */}
              {!isLast && (
                <Separator 
                  className="w-4 h-4 text-gray-400 flex-shrink-0" 
                  aria-hidden="true" 
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumbs;
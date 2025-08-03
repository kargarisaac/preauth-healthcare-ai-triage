import React, { useState, useRef, useEffect, cloneElement, isValidElement } from 'react';
import { clsx } from 'clsx';
import type { TooltipProps } from '@/types/ui';

const Tooltip: React.FC<TooltipProps> = ({
  title,
  placement = 'top',
  trigger = 'hover',
  visible,
  defaultVisible = false,
  onVisibleChange,
  children,
  className,
  overlayClassName,
  delay = 0,
  mouseEnterDelay = 100,
  mouseLeaveDelay = 100,
  arrow = true,
  maxWidth = 320,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const isVisible = visible !== undefined ? visible : internalVisible;

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight,
    };

    let x = 0;
    let y = 0;

    // Calculate position based on placement
    switch (placement) {
      case 'top':
      case 'top-start':
      case 'top-end':
        y = triggerRect.top - tooltipRect.height - 8;
        if (placement === 'top-start') {
          x = triggerRect.left;
        } else if (placement === 'top-end') {
          x = triggerRect.right - tooltipRect.width;
        } else {
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        }
        break;

      case 'bottom':
      case 'bottom-start':
      case 'bottom-end':
        y = triggerRect.bottom + 8;
        if (placement === 'bottom-start') {
          x = triggerRect.left;
        } else if (placement === 'bottom-end') {
          x = triggerRect.right - tooltipRect.width;
        } else {
          x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        }
        break;

      case 'left':
      case 'left-start':
      case 'left-end':
        x = triggerRect.left - tooltipRect.width - 8;
        if (placement === 'left-start') {
          y = triggerRect.top;
        } else if (placement === 'left-end') {
          y = triggerRect.bottom - tooltipRect.height;
        } else {
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        }
        break;

      case 'right':
      case 'right-start':
      case 'right-end':
        x = triggerRect.right + 8;
        if (placement === 'right-start') {
          y = triggerRect.top;
        } else if (placement === 'right-end') {
          y = triggerRect.bottom - tooltipRect.height;
        } else {
          y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        }
        break;
    }

    // Adjust for viewport boundaries
    if (x < 8) x = 8;
    if (x + tooltipRect.width > viewport.width - 8) {
      x = viewport.width - tooltipRect.width - 8;
    }
    if (y < 8) y = 8;
    if (y + tooltipRect.height > viewport.height - 8) {
      y = viewport.height - tooltipRect.height - 8;
    }

    setPosition({ x, y });
  };

  const showTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    
    const showDelay = trigger === 'hover' ? mouseEnterDelay : delay;
    timeoutRef.current = setTimeout(() => {
      setInternalVisible(true);
      onVisibleChange?.(true);
    }, showDelay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    
    const hideDelay = trigger === 'hover' ? mouseLeaveDelay : delay;
    timeoutRef.current = setTimeout(() => {
      setInternalVisible(false);
      onVisibleChange?.(false);
    }, hideDelay);
  };

  const toggleTooltip = () => {
    const newVisible = !isVisible;
    setInternalVisible(newVisible);
    onVisibleChange?.(newVisible);
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition);
      return () => {
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition);
      };
    }
  }, [isVisible, placement]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const getArrowClasses = () => {
    const baseArrow = 'absolute w-2 h-2 bg-gray-900 transform rotate-45';
    
    if (placement.startsWith('top')) {
      return clsx(baseArrow, 'top-full -mt-1 left-1/2 -translate-x-1/2');
    }
    if (placement.startsWith('bottom')) {
      return clsx(baseArrow, 'bottom-full -mb-1 left-1/2 -translate-x-1/2');
    }
    if (placement.startsWith('left')) {
      return clsx(baseArrow, 'left-full -ml-1 top-1/2 -translate-y-1/2');
    }
    if (placement.startsWith('right')) {
      return clsx(baseArrow, 'right-full -mr-1 top-1/2 -translate-y-1/2');
    }
    
    return baseArrow;
  };

  // Clone children and add event handlers
  const triggerProps: any = {};

  if (trigger === 'hover') {
    triggerProps.onMouseEnter = showTooltip;
    triggerProps.onMouseLeave = hideTooltip;
  } else if (trigger === 'click') {
    triggerProps.onClick = toggleTooltip;
  } else if (trigger === 'focus') {
    triggerProps.onFocus = showTooltip;
    triggerProps.onBlur = hideTooltip;
  }

  if (!isValidElement(children)) {
    console.warn('Tooltip children must be a valid React element');
    return children;
  }

  const clonedChildren = cloneElement(children, {
    ...triggerProps,
    ref: (node: HTMLElement) => {
      triggerRef.current = node;
      // Handle existing ref
      const { ref } = children;
      if (typeof ref === 'function') {
        ref(node);
      } else if (ref) {
        (ref as any).current = node;
      }
    },
  });

  return (
    <>
      <span className={clsx('inline-block', className)}>
        {clonedChildren}
      </span>
      
      {isVisible && (
        <>
          {/* Overlay for click-outside behavior */}
          {trigger === 'click' && (
            <div
              className="fixed inset-0 z-40"
              onClick={hideTooltip}
              aria-hidden="true"
            />
          )}
          
          {/* Tooltip content */}
          <div
            ref={tooltipRef}
            className={clsx(
              'fixed z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg',
              'animate-fade-in',
              overlayClassName
            )}
            style={{
              left: position.x,
              top: position.y,
              maxWidth: maxWidth,
            }}
            role="tooltip"
            aria-hidden={!isVisible}
          >
            {typeof title === 'string' ? (
              <span className="break-words">{title}</span>
            ) : (
              title
            )}
            
            {arrow && (
              <div className={getArrowClasses()} aria-hidden="true" />
            )}
          </div>
        </>
      )}
    </>
  );
};

// Healthcare-specific tooltip variants
export const MedicalTooltip: React.FC<{
  diagnosis?: string;
  icdCode?: string;
  description?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  children: React.ReactElement;
}> = ({ diagnosis, icdCode, description, severity, children }) => {
  const severityColors = {
    low: 'text-green-400',
    medium: 'text-yellow-400',
    high: 'text-orange-400',
    critical: 'text-red-400',
  };

  const tooltipContent = (
    <div className="space-y-2">
      {diagnosis && (
        <div>
          <span className="font-semibold">Diagnosis:</span> {diagnosis}
        </div>
      )}
      {icdCode && (
        <div>
          <span className="font-semibold">ICD Code:</span> {icdCode}
        </div>
      )}
      {severity && (
        <div>
          <span className="font-semibold">Severity:</span>{' '}
          <span className={severityColors[severity]}>
            {severity.charAt(0).toUpperCase() + severity.slice(1)}
          </span>
        </div>
      )}
      {description && (
        <div className="text-xs text-gray-300 mt-2 border-t border-gray-600 pt-2">
          {description}
        </div>
      )}
    </div>
  );

  return (
    <Tooltip title={tooltipContent} maxWidth={400}>
      {children}
    </Tooltip>
  );
};

export const AuthorizationTooltip: React.FC<{
  authId: string;
  status: string;
  approvalDate?: string;
  expiryDate?: string;
  amount?: number;
  currency?: string;
  children: React.ReactElement;
}> = ({ authId, status, approvalDate, expiryDate, amount, currency, children }) => {
  const tooltipContent = (
    <div className="space-y-2">
      <div>
        <span className="font-semibold">Auth ID:</span> {authId}
      </div>
      <div>
        <span className="font-semibold">Status:</span> {status}
      </div>
      {approvalDate && (
        <div>
          <span className="font-semibold">Approved:</span> {approvalDate}
        </div>
      )}
      {expiryDate && (
        <div>
          <span className="font-semibold">Expires:</span> {expiryDate}
        </div>
      )}
      {amount && currency && (
        <div>
          <span className="font-semibold">Amount:</span> {currency} {amount.toLocaleString()}
        </div>
      )}
    </div>
  );

  return (
    <Tooltip title={tooltipContent} maxWidth={300}>
      {children}
    </Tooltip>
  );
};

export default Tooltip;
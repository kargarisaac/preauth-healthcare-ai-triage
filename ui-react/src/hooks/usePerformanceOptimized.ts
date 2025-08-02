import React, { useCallback, useMemo, useRef, useEffect, useState } from 'react';
import { useDebounce } from 'use-debounce';
import { usePerformance } from '@contexts/PerformanceContext';

// Optimized useState with deep comparison
export const useOptimizedState = <T>(initialState: T | (() => T)) => {
  const [state, setState] = useState(initialState);
  const setOptimizedState = useCallback((newState: T | ((prev: T) => T)) => {
    setState(prev => {
      const nextState = typeof newState === 'function' ? (newState as (prev: T) => T)(prev) : newState;
      
      // Deep comparison to prevent unnecessary re-renders
      if (JSON.stringify(nextState) === JSON.stringify(prev)) {
        return prev;
      }
      
      return nextState;
    });
  }, []);
  
  return [state, setOptimizedState] as const;
};

// Debounced callback with performance tracking
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  options?: {
    leading?: boolean;
    trailing?: boolean;
    maxWait?: number;
  }
) => {
  const [debouncedCallback] = useDebounce(callback, delay, options);
  return debouncedCallback;
};

// Throttled callback
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
) => {
  const lastCallRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  return useCallback((...args: Parameters<T>) => {
    const now = Date.now();
    
    if (now - lastCallRef.current >= delay) {
      lastCallRef.current = now;
      return callback(...args);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        lastCallRef.current = Date.now();
        callback(...args);
      }, delay - (now - lastCallRef.current));
    }
  }, [callback, delay]);
};

// Async data fetching with performance tracking
export const useAsyncData = <T>(
  asyncFn: () => Promise<T>,
  deps: React.DependencyList = [],
  options?: {
    immediate?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  }
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const requestId = useRef(0);
  
  const execute = useCallback(async () => {
    const currentRequestId = ++requestId.current;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await asyncFn();
      
      // Only update if this is still the latest request
      if (currentRequestId === requestId.current) {
        setData(result);
        options?.onSuccess?.(result);
      }
    } catch (err) {
      if (currentRequestId === requestId.current) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        options?.onError?.(error);
      }
    } finally {
      if (currentRequestId === requestId.current) {
        setLoading(false);
      }
    }
  }, [asyncFn, ...deps]);
  
  useEffect(() => {
    if (options?.immediate !== false) {
      execute();
    }
  }, [execute]);
  
  return {
    data,
    loading,
    error,
    execute,
    refetch: execute
  };
};

// Intersection observer hook for lazy rendering
export const useIntersectionObserver = (
  options?: IntersectionObserverInit
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const targetRef = useRef<HTMLElement | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  
  const setTarget = useCallback((element: HTMLElement | null) => {
    if (targetRef.current && observerRef.current) {
      observerRef.current.unobserve(targetRef.current);
    }
    
    targetRef.current = element;
    
    if (element) {
      if (!observerRef.current) {
        observerRef.current = new IntersectionObserver(
          ([entry]) => {
            setIsIntersecting(entry.isIntersecting);
            if (entry.isIntersecting && !hasIntersected) {
              setHasIntersected(true);
            }
          },
          {
            threshold: 0.1,
            rootMargin: '50px',
            ...options
          }
        );
      }
      
      observerRef.current.observe(element);
    }
  }, [hasIntersected, options]);
  
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);
  
  return {
    ref: setTarget,
    isIntersecting,
    hasIntersected
  };
};

// Memory-efficient list rendering
export const useVirtualList = <T>(
  items: T[],
  containerHeight: number,
  itemHeight: number,
  overscan = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, overscan, items.length]);
  
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.startIndex, visibleRange.endIndex + 1)
      .map((item, index) => ({
        item,
        index: visibleRange.startIndex + index
      }));
  }, [items, visibleRange]);
  
  const totalHeight = items.length * itemHeight;
  const offsetY = visibleRange.startIndex * itemHeight;
  
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(event.currentTarget.scrollTop);
  }, []);
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll
  };
};
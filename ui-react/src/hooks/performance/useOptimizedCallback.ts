import { useCallback, useRef } from 'react';

/**
 * Enhanced useCallback that tracks performance and prevents unnecessary re-renders
 */
export const useOptimizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList,
  options?: {
    debounceMs?: number;
    throttleMs?: number;
    maxExecutionsPerSecond?: number;
  }
): T => {
  const { debounceMs, throttleMs, maxExecutionsPerSecond = 60 } = options || {};
  const lastExecution = useRef<number>(0);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const executionCount = useRef<number>(0);
  const secondStart = useRef<number>(Date.now());

  return useCallback(
    ((...args: any[]) => {
      const now = Date.now();
      
      // Rate limiting
      if (maxExecutionsPerSecond) {
        if (now - secondStart.current >= 1000) {
          executionCount.current = 0;
          secondStart.current = now;
        }
        
        if (executionCount.current >= maxExecutionsPerSecond) {
          return;
        }
        
        executionCount.current++;
      }

      // Debouncing
      if (debounceMs) {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        timeoutRef.current = setTimeout(() => {
          callback(...args);
        }, debounceMs);
        return;
      }

      // Throttling
      if (throttleMs && now - lastExecution.current < throttleMs) {
        return;
      }

      lastExecution.current = now;
      return callback(...args);
    }) as T,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps
  );
};

/**
 * Memoized callback specifically for healthcare data processing
 */
export const useHealthcareCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T => {
  return useOptimizedCallback(callback, deps, {
    maxExecutionsPerSecond: 30, // Lower rate for healthcare data processing
    throttleMs: 100, // Prevent rapid-fire healthcare operations
  });
};
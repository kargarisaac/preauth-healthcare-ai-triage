import { useEffect, useCallback, useRef, useState } from 'react';
import { usePerformance } from '@contexts/PerformanceContext';
import { trackAnalytics, markPerformance, measurePerformance } from '@utils/performance';

interface PerformanceMonitorOptions {
  trackRenders?: boolean;
  trackMemory?: boolean;
  trackInteractions?: boolean;
  memoryThreshold?: number; // MB
  renderThreshold?: number; // ms
  componentName?: string;
}

interface ComponentMetrics {
  renderCount: number;
  averageRenderTime: number;
  slowRenders: number;
  memoryUsage?: number;
  lastRenderTime: number;
}

export const usePerformanceMonitor = (options: PerformanceMonitorOptions = {}) => {
  const {
    trackRenders = true,
    trackMemory = false,
    trackInteractions = false,
    memoryThreshold = 50, // 50MB
    renderThreshold = 16, // 16ms (60fps)
    componentName = 'UnknownComponent',
  } = options;

  const { markPerformance: contextMark, measurePerformance: contextMeasure } = usePerformance();
  const renderCountRef = useRef(0);
  const renderTimesRef = useRef<number[]>([]);
  const lastMemoryCheckRef = useRef(0);
  const componentMountTime = useRef(Date.now());
  
  const [metrics, setMetrics] = useState<ComponentMetrics>({
    renderCount: 0,
    averageRenderTime: 0,
    slowRenders: 0,
    lastRenderTime: 0,
  });

  // Track component renders
  const trackRender = useCallback(() => {
    if (!trackRenders) return;

    const renderStart = `${componentName}-render-${renderCountRef.current}`;
    const renderEnd = `${componentName}-render-end-${renderCountRef.current}`;
    
    markPerformance(renderStart);
    
    // Use requestAnimationFrame to measure after render
    requestAnimationFrame(() => {
      markPerformance(renderEnd);
      const renderTime = measurePerformance(`${componentName}-render`, renderStart, renderEnd);
      
      renderCountRef.current++;
      renderTimesRef.current.push(renderTime);
      
      // Keep only last 100 render times for memory efficiency
      if (renderTimesRef.current.length > 100) {
        renderTimesRef.current = renderTimesRef.current.slice(-100);
      }
      
      const averageRenderTime = renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length;
      const slowRenders = renderTimesRef.current.filter(time => time > renderThreshold).length;
      
      setMetrics(prev => ({
        ...prev,
        renderCount: renderCountRef.current,
        averageRenderTime,
        slowRenders,
        lastRenderTime: renderTime,
      }));
      
      // Track slow renders
      if (renderTime > renderThreshold) {
        trackAnalytics({
          name: 'slow_render',
          category: 'performance',
          data: {
            componentName,
            renderTime,
            renderCount: renderCountRef.current,
            threshold: renderThreshold,
          },
          value: renderTime,
        });
      }
    });
  }, [trackRenders, componentName, renderThreshold]);

  // Track memory usage
  const trackMemoryUsage = useCallback(() => {
    if (!trackMemory || typeof window === 'undefined') return;

    const memory = (performance as any).memory;
    if (memory) {
      const usedMB = memory.usedJSHeapSize / 1024 / 1024;
      
      setMetrics(prev => ({ ...prev, memoryUsage: usedMB }));
      
      // Track memory spikes
      if (usedMB > memoryThreshold) {
        const now = Date.now();
        // Only track once per minute to avoid spam
        if (now - lastMemoryCheckRef.current > 60000) {
          lastMemoryCheckRef.current = now;
          
          trackAnalytics({
            name: 'high_memory_usage',
            category: 'performance',
            data: {
              componentName,
              memoryUsage: usedMB,
              threshold: memoryThreshold,
              totalHeapSize: memory.totalJSHeapSize / 1024 / 1024,
              heapSizeLimit: memory.jsHeapSizeLimit / 1024 / 1024,
            },
            value: usedMB,
          });
        }
      }
    }
  }, [trackMemory, componentName, memoryThreshold]);

  // Track user interactions
  const trackInteraction = useCallback((interactionType: string, target?: string, metadata?: Record<string, any>) => {
    if (!trackInteractions) return;
    
    trackAnalytics({
      name: 'component_interaction',
      category: 'interaction',
      data: {
        componentName,
        interactionType,
        target,
        renderCount: renderCountRef.current,
        averageRenderTime: renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length || 0,
        ...metadata,
      },
    });
  }, [trackInteractions, componentName]);

  // Component lifecycle tracking
  useEffect(() => {
    const mountTime = Date.now() - componentMountTime.current;
    
    trackAnalytics({
      name: 'component_mount',
      category: 'lifecycle',
      data: {
        componentName,
        mountTime,
      },
      value: mountTime,
    });

    return () => {
      const totalLifetime = Date.now() - componentMountTime.current;
      
      trackAnalytics({
        name: 'component_unmount',
        category: 'lifecycle',
        data: {
          componentName,
          totalRenders: renderCountRef.current,
          averageRenderTime: renderTimesRef.current.reduce((a, b) => a + b, 0) / renderTimesRef.current.length || 0,
          totalLifetime,
          slowRenderPercentage: (metrics.slowRenders / Math.max(metrics.renderCount, 1)) * 100,
        },
        value: totalLifetime,
      });
    };
  }, [componentName, metrics.slowRenders, metrics.renderCount]);

  // Automatic render tracking
  useEffect(() => {
    trackRender();
  });

  // Memory monitoring interval
  useEffect(() => {
    if (!trackMemory) return;
    
    const interval = setInterval(trackMemoryUsage, 5000); // Check every 5 seconds
    
    return () => clearInterval(interval);
  }, [trackMemory, trackMemoryUsage]);

  // Performance report
  const getPerformanceReport = useCallback(() => {
    return {
      ...metrics,
      componentName,
      lifetime: Date.now() - componentMountTime.current,
      renderEfficiency: metrics.renderCount > 0 ? (metrics.renderCount - metrics.slowRenders) / metrics.renderCount : 1,
      memoryEfficient: metrics.memoryUsage ? metrics.memoryUsage < memoryThreshold : true,
    };
  }, [metrics, componentName, memoryThreshold]);

  return {
    metrics,
    trackRender,
    trackInteraction,
    trackMemoryUsage,
    getPerformanceReport,
  };
};

// Hook for tracking specific operations (file uploads, API calls, etc.)
export const useOperationPerformance = (operationName: string) => {
  const operationStartTime = useRef<number | null>(null);
  const operationCount = useRef(0);
  const totalTime = useRef(0);

  const startOperation = useCallback((metadata?: Record<string, any>) => {
    operationStartTime.current = Date.now();
    markPerformance(`${operationName}-start-${operationCount.current}`);
    
    trackAnalytics({
      name: 'operation_start',
      category: 'operation',
      data: {
        operationName,
        operationId: operationCount.current,
        ...metadata,
      },
    });
  }, [operationName]);

  const endOperation = useCallback((success: boolean = true, metadata?: Record<string, any>) => {
    if (operationStartTime.current === null) return 0;
    
    const endTime = Date.now();
    const duration = endTime - operationStartTime.current;
    
    markPerformance(`${operationName}-end-${operationCount.current}`);
    const measuredDuration = measurePerformance(
      `${operationName}-${operationCount.current}`,
      `${operationName}-start-${operationCount.current}`,
      `${operationName}-end-${operationCount.current}`
    );
    
    operationCount.current++;
    totalTime.current += duration;
    operationStartTime.current = null;
    
    trackAnalytics({
      name: 'operation_complete',
      category: 'operation',
      data: {
        operationName,
        duration,
        measuredDuration,
        success,
        operationCount: operationCount.current,
        averageDuration: totalTime.current / operationCount.current,
        ...metadata,
      },
      value: duration,
    });
    
    return duration;
  }, [operationName]);

  const getOperationStats = useCallback(() => {
    return {
      operationName,
      totalOperations: operationCount.current,
      totalTime: totalTime.current,
      averageTime: operationCount.current > 0 ? totalTime.current / operationCount.current : 0,
      isRunning: operationStartTime.current !== null,
    };
  }, [operationName]);

  return {
    startOperation,
    endOperation,
    getOperationStats,
  };
};
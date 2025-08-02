import React, { createContext, useContext, useCallback, useMemo, useEffect, useState } from 'react';

interface PerformanceMetrics {
  CLS: number | null;
  FID: number | null;
  FCP: number | null;
  LCP: number | null;
  TTFB: number | null;
}

interface PerformanceContextType {
  metrics: PerformanceMetrics;
  networkStatus: {
    online: boolean;
    effectiveType?: string;
    downlink?: number;
    rtt?: number;
  };
  isLowEndDevice: boolean;
  prefersReducedMotion: boolean;
  updateMetrics: () => void;
  markPerformance: (name: string) => void;
  measurePerformance: (name: string, startMark: string, endMark?: string) => number;
}

const PerformanceContext = createContext<PerformanceContextType | undefined>(undefined);

interface PerformanceProviderProps {
  children: React.ReactNode;
}

// Detect low-end devices based on hardware capabilities
const detectLowEndDevice = (): boolean => {
  // Check memory (if available)
  const memory = (navigator as any).memory;
  if (memory && memory.jsHeapSizeLimit < 1073741824) { // Less than 1GB
    return true;
  }
  
  // Check CPU cores
  const cores = navigator.hardwareConcurrency;
  if (cores && cores <= 2) {
    return true;
  }
  
  // Check connection type
  const connection = (navigator as any).connection;
  if (connection && (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g')) {
    return true;
  }
  
  return false;
};

const getNetworkStatus = () => {
  const connection = (navigator as any).connection;
  return {
    online: navigator.onLine,
    effectiveType: connection?.effectiveType,
    downlink: connection?.downlink,
    rtt: connection?.rtt,
  };
};

// Memoized performance provider
export const PerformanceProvider: React.FC<PerformanceProviderProps> = React.memo(({ children }) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    CLS: null,
    FID: null,
    FCP: null,
    LCP: null,
    TTFB: null,
  });
  
  const [networkStatus, setNetworkStatus] = useState(() => getNetworkStatus());
  const [isLowEndDevice] = useState(() => detectLowEndDevice());
  const [prefersReducedMotion] = useState(() => 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );

  // Update metrics periodically
  useEffect(() => {
    const metricsInterval = setInterval(() => {
      // Mock metrics update - replace with actual web vitals
      setMetrics(prev => ({ ...prev }));
    }, 5000);
    
    return () => {
      clearInterval(metricsInterval);
    };
  }, []);

  // Memoized update function
  const updateMetrics = useCallback(() => {
    setMetrics(prev => ({ ...prev }));
  }, []);

  // Performance marking with memoization
  const markPerformance = useCallback((name: string) => {
    if ('performance' in window && 'mark' in performance) {
      performance.mark(name);
    }
  }, []);

  // Performance measurement with memoization
  const measurePerformance = useCallback((name: string, startMark: string, endMark?: string) => {
    if ('performance' in window && 'measure' in performance) {
      try {
        if (endMark) {
          performance.measure(name, startMark, endMark);
        } else {
          performance.measure(name, startMark);
        }
        
        const measure = performance.getEntriesByName(name, 'measure')[0];
        return measure?.duration || 0;
      } catch (error) {
        console.warn('Performance measurement failed:', error);
        return 0;
      }
    }
    return 0;
  }, []);

  // Memoized context value
  const contextValue = useMemo(() => ({
    metrics,
    networkStatus,
    isLowEndDevice,
    prefersReducedMotion,
    updateMetrics,
    markPerformance,
    measurePerformance,
  }), [
    metrics,
    networkStatus,
    isLowEndDevice,
    prefersReducedMotion,
    updateMetrics,
    markPerformance,
    measurePerformance,
  ]);

  return (
    <PerformanceContext.Provider value={contextValue}>
      {children}
    </PerformanceContext.Provider>
  );
});

PerformanceProvider.displayName = 'PerformanceProvider';

// Custom hook to use performance context
export const usePerformance = (): PerformanceContextType => {
  const context = useContext(PerformanceContext);
  if (context === undefined) {
    throw new Error('usePerformance must be used within a PerformanceProvider');
  }
  return context;
};
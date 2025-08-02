// Performance monitoring and Web Vitals tracking
export interface PerformanceMetrics {
  CLS: number | null;
  FID: number | null;
  FCP: number | null;
  LCP: number | null;
  TTFB: number | null;
}

let metrics: PerformanceMetrics = {
  CLS: null,
  FID: null,
  FCP: null,
  LCP: null,
  TTFB: null,
};

// Initialize Web Vitals tracking
export const initPerformanceMonitoring = () => {
  // Mock implementation - replace with actual web-vitals library
  console.log('Performance monitoring initialized');
};

// Get current metrics
export const getMetrics = (): PerformanceMetrics => ({ ...metrics });

// Custom performance marks
export const markPerformance = (name: string) => {
  if ('performance' in window && 'mark' in performance) {
    performance.mark(name);
  }
};

// Measure performance between marks
export const measurePerformance = (name: string, startMark: string, endMark?: string) => {
  if ('performance' in window && 'measure' in performance) {
    try {
      if (endMark) {
        performance.measure(name, startMark, endMark);
      } else {
        performance.measure(name, startMark);
      }

      const measure = performance.getEntriesByName(name, 'measure')[0];
      if (measure && process.env.NODE_ENV === 'development') {
        console.log(`Performance measure ${name}:`, measure.duration, 'ms');
      }
      return measure?.duration || 0;
    } catch (error) {
      console.warn('Performance measurement failed:', error);
      return 0;
    }
  }
  return 0;
};

// Enhanced Performance monitoring and Web Vitals tracking
export interface PerformanceMetrics {
  CLS: number | null;
  FID: number | null;
  FCP: number | null;
  LCP: number | null;
  TTFB: number | null;
  INP: number | null; // Interaction to Next Paint
  renderTime?: number;
  bundleSize?: number;
}

export interface HealthcareMetrics {
  fileProcessingTime: number;
  validationTime: number;
  fhirMappingTime: number;
  apiResponseTime: number;
  errorRate: number;
  userFlowCompletionRate: number;
}

let metrics: PerformanceMetrics = {
  CLS: null,
  FID: null,
  FCP: null,
  LCP: null,
  TTFB: null,
  INP: null,
};

let healthcareMetrics: HealthcareMetrics = {
  fileProcessingTime: 0,
  validationTime: 0,
  fhirMappingTime: 0,
  apiResponseTime: 0,
  errorRate: 0,
  userFlowCompletionRate: 0,
};

// Analytics integration interface
interface AnalyticsEvent {
  name: string;
  category: string;
  data?: Record<string, any>;
  value?: number;
  timestamp?: number;
}

const analyticsQueue: AnalyticsEvent[] = [];

// Enhanced performance monitoring initialization
export const initPerformanceMonitoring = () => {
  if (typeof window === 'undefined') return;

  // Real Web Vitals tracking (fallback implementation)
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      switch (entry.entryType) {
        case 'largest-contentful-paint':
          metrics.LCP = entry.startTime;
          break;
        case 'first-input':
          metrics.FID = (entry as any).processingStart - entry.startTime;
          break;
        case 'layout-shift':
          if (!(entry as any).hadRecentInput) {
            metrics.CLS = (metrics.CLS || 0) + (entry as any).value;
          }
          break;
        case 'paint':
          if (entry.name === 'first-contentful-paint') {
            metrics.FCP = entry.startTime;
          }
          break;
        case 'navigation':
          const navEntry = entry as PerformanceNavigationTiming;
          metrics.TTFB = navEntry.responseStart - navEntry.requestStart;
          break;
      }
    }
  });

  try {
    observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift', 'paint', 'navigation'] });
  } catch (e) {
    console.warn('Performance Observer not supported:', e);
  }

  // Track Long Tasks for INP approximation
  if ('PerformanceObserver' in window) {
    const longTaskObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        metrics.INP = (metrics.INP || 0) + entry.duration;
      }
    });

    try {
      longTaskObserver.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      console.warn('Long task observer not supported');
    }
  }

  // Memory monitoring
  const checkMemory = () => {
    const memory = (performance as any).memory;
    if (memory) {
      trackAnalytics({
        name: 'memory_usage',
        category: 'performance',
        data: {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          limit: memory.jsHeapSizeLimit,
        },
      });
    }
  };

  // Check memory every 30 seconds
  setInterval(checkMemory, 30000);

  console.log('Enhanced performance monitoring initialized');
};

// Track analytics events
export const trackAnalytics = (event: AnalyticsEvent) => {
  const enhancedEvent = {
    ...event,
    timestamp: Date.now(),
  };

  analyticsQueue.push(enhancedEvent);

  // In development, log events
  if (process.env.NODE_ENV === 'development') {
    console.log('Analytics Event:', enhancedEvent);
  }

  // Batch send analytics (every 10 events or 30 seconds)
  if (analyticsQueue.length >= 10) {
    sendAnalyticsBatch();
  }
};

// Send analytics batch
const sendAnalyticsBatch = async () => {
  if (analyticsQueue.length === 0) return;

  const batch = analyticsQueue.splice(0);

  try {
    // Replace with your analytics endpoint
    if (process.env.NODE_ENV === 'production') {
      await fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: batch }),
      });
    }
  } catch (error) {
    console.error('Failed to send analytics:', error);
    // Re-queue failed events (with limit)
    if (analyticsQueue.length < 100) {
      analyticsQueue.unshift(...batch.slice(-50)); // Keep last 50 events
    }
  }
};

// Auto-send analytics every 30 seconds
if (typeof window !== 'undefined') {
  setInterval(sendAnalyticsBatch, 30000);
}

// Healthcare-specific performance tracking
export const trackHealthcareMetric = (metric: keyof HealthcareMetrics, value: number) => {
  healthcareMetrics[metric] = value;

  trackAnalytics({
    name: `healthcare_${metric}`,
    category: 'healthcare_performance',
    value,
  });
};

// Enhanced file processing tracking
export const trackFileProcessing = (fileType: string, fileSize: number, processingTime: number) => {
  trackAnalytics({
    name: 'file_processing',
    category: 'healthcare',
    data: {
      fileType,
      fileSize,
      processingTime,
      timestamp: Date.now(),
    },
    value: processingTime,
  });
};

// User interaction tracking
export const trackUserInteraction = (action: string, element: string, metadata?: Record<string, any>) => {
  trackAnalytics({
    name: 'user_interaction',
    category: 'ui',
    data: {
      action,
      element,
      ...metadata,
    },
  });
};

// Error tracking
export const trackError = (error: Error, context?: string) => {
  trackAnalytics({
    name: 'error',
    category: 'error',
    data: {
      message: error.message,
      stack: error.stack,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
    },
  });
};

// Get current metrics
export const getMetrics = (): PerformanceMetrics => ({ ...metrics });
export const getHealthcareMetrics = (): HealthcareMetrics => ({ ...healthcareMetrics });

// Custom performance marks with analytics integration
export const markPerformance = (name: string, metadata?: Record<string, any>) => {
  if ('performance' in window && 'mark' in performance) {
    performance.mark(name);

    trackAnalytics({
      name: 'performance_mark',
      category: 'performance',
      data: {
        markName: name,
        timestamp: Date.now(),
        ...metadata,
      },
    });
  }
};

// Enhanced performance measurement
export const measurePerformance = (name: string, startMark: string, endMark?: string) => {
  if ('performance' in window && 'measure' in performance) {
    try {
      if (endMark) {
        performance.measure(name, startMark, endMark);
      } else {
        performance.measure(name, startMark);
      }

      const measure = performance.getEntriesByName(name, 'measure')[0];
      const duration = measure?.duration || 0;

      if (measure) {
        trackAnalytics({
          name: 'performance_measure',
          category: 'performance',
          data: {
            measureName: name,
            startMark,
            endMark,
            duration,
          },
          value: duration,
        });

        if (process.env.NODE_ENV === 'development') {
          console.log(`Performance measure ${name}:`, duration, 'ms');
        }
      }

      return duration;
    } catch (error) {
      console.warn('Performance measurement failed:', error);
      trackError(error as Error, `measurePerformance: ${name}`);
      return 0;
    }
  }
  return 0;
};

// Resource loading optimization
export const preloadResource = (href: string, as: string, crossorigin?: string) => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = href;
  link.as = as;
  if (crossorigin) link.crossOrigin = crossorigin;
  document.head.appendChild(link);
};

// Critical resource hints
export const addResourceHints = () => {
  // DNS prefetch for external resources
  const dnsPrefetch = (hostname: string) => {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = `//${hostname}`;
    document.head.appendChild(link);
  };

  // Preconnect to critical origins
  const preconnect = (href: string) => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = href;
    document.head.appendChild(link);
  };

  // Add resource hints for healthcare APIs and assets
  dnsPrefetch('fonts.googleapis.com');
  dnsPrefetch('fonts.gstatic.com');
  preconnect('https://api.healthcare-preauth.org');
};

// Performance budget monitoring
export const checkPerformanceBudget = () => {
  const budget = {
    LCP: 2500, // 2.5s
    FID: 100, // 100ms
    CLS: 0.1, // 0.1
    FCP: 1800, // 1.8s
    TTFB: 600, // 600ms
  };

  const issues: string[] = [];

  Object.entries(budget).forEach(([metric, threshold]) => {
    const value = metrics[metric as keyof PerformanceMetrics];
    if (value !== null && value > threshold) {
      issues.push(`${metric}: ${value}ms > ${threshold}ms`);
    }
  });

  if (issues.length > 0) {
    trackAnalytics({
      name: 'performance_budget_violation',
      category: 'performance',
      data: { issues },
    });
  }

  return issues;
};
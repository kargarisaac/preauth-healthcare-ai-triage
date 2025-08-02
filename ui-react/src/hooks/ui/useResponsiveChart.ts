import { useState, useEffect, useRef, useCallback } from 'react';

interface ChartDimensions {
  width: number;
  height: number;
}

interface ResponsiveChartConfig {
  // Base dimensions
  baseWidth?: number;
  baseHeight?: number;
  aspectRatio?: number;
  
  // Responsive breakpoints
  breakpoints?: {
    sm: number;  // 640px
    md: number;  // 768px
    lg: number;  // 1024px
    xl: number;  // 1280px
  };
  
  // Size adjustments per breakpoint
  sizeAdjustments?: {
    sm?: { width?: number; height?: number };
    md?: { width?: number; height?: number };
    lg?: { width?: number; height?: number };
    xl?: { width?: number; height?: number };
  };
  
  // Minimum and maximum constraints
  minWidth?: number;
  maxWidth?: number;
  minHeight?: number;
  maxHeight?: number;
  
  // Chart-specific options
  maintainAspectRatio?: boolean;
  autoResize?: boolean;
  debounceMs?: number;
}

interface UseResponsiveChartReturn {
  dimensions: ChartDimensions;
  containerRef: React.RefObject<HTMLDivElement>;
  isLoading: boolean;
  currentBreakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  
  // Chart configuration helpers
  getResponsiveMargin: () => { top: number; right: number; bottom: number; left: number };
  getResponsiveFontSize: () => { title: number; axis: number; legend: number; tooltip: number };
  getResponsiveSpacing: () => { padding: number; gap: number };
  shouldShowLegend: () => boolean;
  shouldShowLabels: () => boolean;
  getOptimalTickCount: () => { x: number; y: number };
  
  // Manual control
  updateDimensions: (width?: number, height?: number) => void;
  recalculate: () => void;
}

const DEFAULT_CONFIG: Required<ResponsiveChartConfig> = {
  baseWidth: 800,
  baseHeight: 400,
  aspectRatio: 2, // width/height
  breakpoints: {
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280
  },
  sizeAdjustments: {
    sm: { width: 0.8, height: 0.9 },
    md: { width: 0.9, height: 0.95 },
    lg: { width: 1.0, height: 1.0 },
    xl: { width: 1.1, height: 1.05 }
  },
  minWidth: 280,
  maxWidth: 1200,
  minHeight: 200,
  maxHeight: 600,
  maintainAspectRatio: true,
  autoResize: true,
  debounceMs: 150
};

// Debounce utility
const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  
  return useCallback(((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }) as T, [callback, delay]);
};

export const useResponsiveChart = (
  config: ResponsiveChartConfig = {}
): UseResponsiveChartReturn => {
  const fullConfig = { ...DEFAULT_CONFIG, ...config };
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [dimensions, setDimensions] = useState<ChartDimensions>({
    width: fullConfig.baseWidth,
    height: fullConfig.baseHeight
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [currentBreakpoint, setCurrentBreakpoint] = useState<'xs' | 'sm' | 'md' | 'lg' | 'xl'>('lg');

  // Determine current breakpoint
  const determineBreakpoint = (width: number): 'xs' | 'sm' | 'md' | 'lg' | 'xl' => {
    if (width >= fullConfig.breakpoints.xl) return 'xl';
    if (width >= fullConfig.breakpoints.lg) return 'lg';
    if (width >= fullConfig.breakpoints.md) return 'md';
    if (width >= fullConfig.breakpoints.sm) return 'sm';
    return 'xs';
  };

  // Calculate responsive dimensions
  const calculateDimensions = useCallback((containerWidth?: number): ChartDimensions => {
    let targetWidth = containerWidth || fullConfig.baseWidth;
    let targetHeight = fullConfig.baseHeight;
    
    // Determine breakpoint
    const breakpoint = determineBreakpoint(targetWidth);
    setCurrentBreakpoint(breakpoint);
    
    // Apply size adjustments for current breakpoint
    const adjustments = breakpoint === 'xs' ? undefined : fullConfig.sizeAdjustments[breakpoint];
    if (adjustments) {
      if (adjustments.width) {
        targetWidth = targetWidth * adjustments.width;
      }
      if (adjustments.height) {
        targetHeight = targetHeight * adjustments.height;
      }
    }
    
    // Maintain aspect ratio if enabled
    if (fullConfig.maintainAspectRatio && fullConfig.aspectRatio) {
      targetHeight = targetWidth / fullConfig.aspectRatio;
    }
    
    // Apply constraints
    targetWidth = Math.max(
      fullConfig.minWidth, 
      Math.min(targetWidth, fullConfig.maxWidth)
    );
    
    targetHeight = Math.max(
      fullConfig.minHeight,
      Math.min(targetHeight, fullConfig.maxHeight)
    );
    
    return {
      width: Math.round(targetWidth),
      height: Math.round(targetHeight)
    };
  }, [fullConfig]);

  // Debounced resize handler
  const debouncedResize = useDebounce(() => {
    if (!containerRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const newDimensions = calculateDimensions(containerRect.width);
    
    setDimensions(newDimensions);
    setIsLoading(false);
  }, fullConfig.debounceMs);

  // Resize observer
  useEffect(() => {
    if (!fullConfig.autoResize || !containerRef.current) return;

    const resizeObserver = new ResizeObserver(() => {
      debouncedResize();
    });
    
    resizeObserver.observe(containerRef.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, [debouncedResize, fullConfig.autoResize]);

  // Window resize listener as fallback
  useEffect(() => {
    if (!fullConfig.autoResize) return;

    const handleWindowResize = () => {
      debouncedResize();
    };

    window.addEventListener('resize', handleWindowResize);
    
    return () => {
      window.removeEventListener('resize', handleWindowResize);
    };
  }, [debouncedResize, fullConfig.autoResize]);

  // Initial calculation
  useEffect(() => {
    const initialResize = () => {
      if (containerRef.current) {
        const containerRect = containerRef.current.getBoundingClientRect();
        const initialDimensions = calculateDimensions(containerRect.width);
        setDimensions(initialDimensions);
      } else {
        const initialDimensions = calculateDimensions();
        setDimensions(initialDimensions);
      }
      setIsLoading(false);
    };

    // Use setTimeout to ensure container is rendered
    const timeout = setTimeout(initialResize, 0);
    return () => clearTimeout(timeout);
  }, [calculateDimensions]);

  // Device type helpers
  const isMobile = currentBreakpoint === 'xs' || currentBreakpoint === 'sm';
  const isTablet = currentBreakpoint === 'md';
  const isDesktop = currentBreakpoint === 'lg' || currentBreakpoint === 'xl';

  // Chart configuration helpers
  const getResponsiveMargin = useCallback(() => {
    const baseMargin = { top: 20, right: 30, bottom: 60, left: 60 };
    
    switch (currentBreakpoint) {
      case 'xs':
        return { top: 10, right: 15, bottom: 40, left: 40 };
      case 'sm':
        return { top: 15, right: 20, bottom: 50, left: 50 };
      case 'md':
        return { top: 18, right: 25, bottom: 55, left: 55 };
      case 'lg':
        return baseMargin;
      case 'xl':
        return { top: 25, right: 35, bottom: 65, left: 65 };
      default:
        return baseMargin;
    }
  }, [currentBreakpoint]);

  const getResponsiveFontSize = useCallback(() => {
    const baseSizes = { title: 16, axis: 12, legend: 12, tooltip: 11 };
    
    switch (currentBreakpoint) {
      case 'xs':
        return { title: 14, axis: 10, legend: 10, tooltip: 9 };
      case 'sm':
        return { title: 15, axis: 11, legend: 11, tooltip: 10 };
      case 'md':
        return baseSizes;
      case 'lg':
        return baseSizes;
      case 'xl':
        return { title: 18, axis: 13, legend: 13, tooltip: 12 };
      default:
        return baseSizes;
    }
  }, [currentBreakpoint]);

  const getResponsiveSpacing = useCallback(() => {
    switch (currentBreakpoint) {
      case 'xs':
        return { padding: 8, gap: 4 };
      case 'sm':
        return { padding: 12, gap: 6 };
      case 'md':
        return { padding: 16, gap: 8 };
      case 'lg':
        return { padding: 20, gap: 10 };
      case 'xl':
        return { padding: 24, gap: 12 };
      default:
        return { padding: 16, gap: 8 };
    }
  }, [currentBreakpoint]);

  const shouldShowLegend = useCallback(() => {
    // Hide legend on very small screens
    return currentBreakpoint !== 'xs';
  }, [currentBreakpoint]);

  const shouldShowLabels = useCallback(() => {
    // Hide detailed labels on small screens
    return currentBreakpoint !== 'xs' && currentBreakpoint !== 'sm';
  }, [currentBreakpoint]);

  const getOptimalTickCount = useCallback(() => {
    const baseX = Math.floor(dimensions.width / 80); // ~80px per tick
    const baseY = Math.floor(dimensions.height / 40); // ~40px per tick
    
    switch (currentBreakpoint) {
      case 'xs':
        return { x: Math.max(3, Math.floor(baseX * 0.6)), y: Math.max(3, Math.floor(baseY * 0.7)) };
      case 'sm':
        return { x: Math.max(4, Math.floor(baseX * 0.8)), y: Math.max(4, Math.floor(baseY * 0.8)) };
      case 'md':
        return { x: Math.max(5, baseX), y: Math.max(5, baseY) };
      case 'lg':
        return { x: Math.max(6, baseX), y: Math.max(6, baseY) };
      case 'xl':
        return { x: Math.max(8, Math.floor(baseX * 1.2)), y: Math.max(7, Math.floor(baseY * 1.1)) };
      default:
        return { x: baseX, y: baseY };
    }
  }, [dimensions, currentBreakpoint]);

  // Manual control functions
  const updateDimensions = useCallback((width?: number, height?: number) => {
    setDimensions(prev => ({
      width: width || prev.width,
      height: height || prev.height
    }));
  }, []);

  const recalculate = useCallback(() => {
    if (containerRef.current) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const newDimensions = calculateDimensions(containerRect.width);
      setDimensions(newDimensions);
    }
  }, [calculateDimensions]);

  return {
    dimensions,
    containerRef,
    isLoading,
    currentBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
    getResponsiveMargin,
    getResponsiveFontSize,
    getResponsiveSpacing,
    shouldShowLegend,
    shouldShowLabels,
    getOptimalTickCount,
    updateDimensions,
    recalculate
  };
};
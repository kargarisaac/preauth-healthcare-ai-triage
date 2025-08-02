import { useState, useEffect, useCallback, useRef } from 'react';

interface MobileCapabilities {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  supportsTouch: boolean;
  supportsCameraAccess: boolean;
  supportsGeolocation: boolean;
  isOnline: boolean;
  devicePixelRatio: number;
  screenSize: {
    width: number;
    height: number;
  };
}

interface TouchGesture {
  type: 'swipe' | 'tap' | 'longpress' | 'pinch';
  direction?: 'left' | 'right' | 'up' | 'down';
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  duration: number;
  distance: number;
}

interface SwipeConfig {
  minDistance: number;
  maxDuration: number;
  threshold: number;
}

const DEFAULT_SWIPE_CONFIG: SwipeConfig = {
  minDistance: 50,
  maxDuration: 300,
  threshold: 30
};

export const useMobileOptimization = () => {
  const [capabilities, setCapabilities] = useState<MobileCapabilities>({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    supportsTouch: false,
    supportsCameraAccess: false,
    supportsGeolocation: false,
    isOnline: true,
    devicePixelRatio: 1,
    screenSize: { width: 0, height: 0 }
  });

  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);

  // Detect device capabilities
  useEffect(() => {
    const updateCapabilities = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      const isTablet = /ipad|android(?=.*tablet)|tablet/i.test(userAgent);
      const isDesktop = !isMobile && !isTablet;

      setCapabilities({
        isMobile: isMobile && !isTablet,
        isTablet,
        isDesktop,
        supportsTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        supportsCameraAccess: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        supportsGeolocation: !!navigator.geolocation,
        isOnline: navigator.onLine,
        devicePixelRatio: window.devicePixelRatio || 1,
        screenSize: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      });

      // Set orientation
      setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait');
    };

    updateCapabilities();

    // Listen for resize and orientation changes
    window.addEventListener('resize', updateCapabilities);
    window.addEventListener('orientationchange', updateCapabilities);
    window.addEventListener('online', updateCapabilities);
    window.addEventListener('offline', updateCapabilities);

    return () => {
      window.removeEventListener('resize', updateCapabilities);
      window.removeEventListener('orientationchange', updateCapabilities);
      window.removeEventListener('online', updateCapabilities);
      window.removeEventListener('offline', updateCapabilities);
    };
  }, []);

  // Touch gesture detection
  const setupTouchGestures = useCallback((
    element: HTMLElement,
    onGesture: (gesture: TouchGesture) => void,
    config: Partial<SwipeConfig> = {}
  ) => {
    const swipeConfig = { ...DEFAULT_SWIPE_CONFIG, ...config };

    const handleTouchStart = (e: TouchEvent) => {
      const touch = e.touches[0];
      touchStartRef.current = {
        x: touch.clientX,
        y: touch.clientY,
        time: Date.now()
      };
    };

    const handleTouchEnd = (e: TouchEvent) => {
      if (!touchStartRef.current) return;

      const touch = e.changedTouches[0];
      const endTime = Date.now();
      const duration = endTime - touchStartRef.current.time;

      const deltaX = touch.clientX - touchStartRef.current.x;
      const deltaY = touch.clientY - touchStartRef.current.y;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

      // Determine gesture type
      if (distance < 10 && duration < 200) {
        // Tap
        onGesture({
          type: 'tap',
          startX: touchStartRef.current.x,
          startY: touchStartRef.current.y,
          endX: touch.clientX,
          endY: touch.clientY,
          duration,
          distance
        });
      } else if (distance < 10 && duration >= 500) {
        // Long press
        onGesture({
          type: 'longpress',
          startX: touchStartRef.current.x,
          startY: touchStartRef.current.y,
          endX: touch.clientX,
          endY: touch.clientY,
          duration,
          distance
        });
      } else if (distance >= swipeConfig.minDistance && duration <= swipeConfig.maxDuration) {
        // Swipe
        let direction: 'left' | 'right' | 'up' | 'down';

        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          direction = deltaX > 0 ? 'right' : 'left';
        } else {
          direction = deltaY > 0 ? 'down' : 'up';
        }

        onGesture({
          type: 'swipe',
          direction,
          startX: touchStartRef.current.x,
          startY: touchStartRef.current.y,
          endX: touch.clientX,
          endY: touch.clientY,
          duration,
          distance
        });
      }

      touchStartRef.current = null;
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, []);

  // Haptic feedback
  const triggerHapticFeedback = useCallback((
    intensity: 'light' | 'medium' | 'heavy' = 'medium'
  ) => {
    if ('vibrate' in navigator) {
      const patterns = {
        light: [10],
        medium: [20],
        heavy: [30]
      };
      navigator.vibrate(patterns[intensity]);
    }
  }, []);

  // Prevent zoom on double tap
  const preventDoubleClickZoom = useCallback((element: HTMLElement) => {
    let lastTouchEnd = 0;

    const handleTouchEnd = (e: TouchEvent) => {
      const now = Date.now();
      if (now - lastTouchEnd <= 300) {
        e.preventDefault();
      }
      lastTouchEnd = now;
    };

    element.addEventListener('touchend', handleTouchEnd, { passive: false });

    return () => {
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, []);

  // Optimize for mobile performance
  const optimizeForMobile = useCallback(() => {
    if (!capabilities.isMobile) return;

    // Reduce animations on mobile
    document.documentElement.style.setProperty('--animation-duration', '0.2s');

    // Add touch-friendly cursor
    document.body.style.cursor = 'default';

    // Prevent text selection on touch
    document.body.style.webkitTouchCallout = 'none';
    document.body.style.webkitUserSelect = 'none';
    document.body.style.userSelect = 'none';

    // Improve scrolling performance
    document.body.style.webkitOverflowScrolling = 'touch';
    document.body.style.overflowScrolling = 'touch';
  }, [capabilities.isMobile]);

  // Apply mobile optimizations
  useEffect(() => {
    optimizeForMobile();
  }, [optimizeForMobile]);

  // Get appropriate viewport classes
  const getViewportClasses = useCallback(() => {
    const classes = [];

    if (capabilities.isMobile) classes.push('mobile');
    if (capabilities.isTablet) classes.push('tablet');
    if (capabilities.isDesktop) classes.push('desktop');
    if (capabilities.supportsTouch) classes.push('touch');
    if (orientation === 'landscape') classes.push('landscape');
    if (orientation === 'portrait') classes.push('portrait');

    return classes.join(' ');
  }, [capabilities, orientation]);

  // Get responsive breakpoint
  const getBreakpoint = useCallback(() => {
    const width = capabilities.screenSize.width;

    if (width < 640) return 'sm';
    if (width < 768) return 'md';
    if (width < 1024) return 'lg';
    if (width < 1280) return 'xl';
    return '2xl';
  }, [capabilities.screenSize.width]);

  // Check if element is in viewport
  const isInViewport = useCallback((element: HTMLElement) => {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= capabilities.screenSize.height &&
      rect.right <= capabilities.screenSize.width
    );
  }, [capabilities.screenSize]);

  // Smooth scroll to element
  const scrollToElement = useCallback((
    element: HTMLElement,
    behavior: ScrollBehavior = 'smooth'
  ) => {
    element.scrollIntoView({
      behavior,
      block: 'center',
      inline: 'nearest'
    });
  }, []);

  // Get safe area insets for mobile devices
  const getSafeAreaInsets = useCallback(() => {
    const style = getComputedStyle(document.documentElement);

    return {
      top: parseInt(style.getPropertyValue('--sat') || '0'),
      right: parseInt(style.getPropertyValue('--sar') || '0'),
      bottom: parseInt(style.getPropertyValue('--sab') || '0'),
      left: parseInt(style.getPropertyValue('--sal') || '0')
    };
  }, []);

  return {
    // Capabilities
    capabilities,
    orientation,

    // Utility functions
    setupTouchGestures,
    triggerHapticFeedback,
    preventDoubleClickZoom,
    optimizeForMobile,

    // Helper functions
    getViewportClasses,
    getBreakpoint,
    isInViewport,
    scrollToElement,
    getSafeAreaInsets,

    // Convenience flags
    isMobile: capabilities.isMobile,
    isTablet: capabilities.isTablet,
    isDesktop: capabilities.isDesktop,
    supportsTouch: capabilities.supportsTouch,
    isOnline: capabilities.isOnline
  };
};

export default useMobileOptimization;

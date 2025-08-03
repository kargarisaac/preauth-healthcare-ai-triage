import React, { useState, useRef, useEffect } from 'react';
import { useIntersectionObserver } from '@hooks/usePerformanceOptimized';
import { trackAnalytics } from '@utils/performance';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  placeholder?: string;
  blurDataURL?: string;
  priority?: boolean;
  onLoad?: () => void;
  onError?: () => void;
}

export const LazyImage: React.FC<LazyImageProps> = React.memo(({
  src,
  alt,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMSIgaGVpZ2h0PSIxIiB2aWV3Qm94PSIwIDAgMSAxIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxIiBoZWlnaHQ9IjEiIGZpbGw9IiNGMEYwRjAiLz48L3N2Zz4=',
  blurDataURL,
  priority = false,
  onLoad,
  onError,
  className = '',
  ...props
}) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [imageRef, setImageRef] = useState<HTMLImageElement | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [loadStartTime] = useState(Date.now());
  
  const { ref: intersectionRef, isIntersecting, hasIntersected } = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '50px',
  });

  // Combined ref for intersection observer and image element
  const combinedRef = useRef<HTMLImageElement | null>(null);
  const setCombinedRef = (element: HTMLImageElement | null) => {
    combinedRef.current = element;
    setImageRef(element);
    intersectionRef(element);
  };

  // Preload image when in viewport or priority
  useEffect(() => {
    if (!hasIntersected && !priority) return;

    const img = new Image();
    
    const handleLoad = () => {
      const loadTime = Date.now() - loadStartTime;
      
      setImageSrc(src);
      setIsLoaded(true);
      
      // Track image loading performance
      trackAnalytics({
        name: 'image_loaded',
        category: 'performance',
        data: {
          src,
          loadTime,
          priority,
          wasIntersecting: isIntersecting,
        },
        value: loadTime,
      });
      
      onLoad?.();
    };

    const handleError = () => {
      setHasError(true);
      
      trackAnalytics({
        name: 'image_error',
        category: 'error',
        data: {
          src,
          alt,
          priority,
        },
      });
      
      onError?.();
    };

    img.addEventListener('load', handleLoad);
    img.addEventListener('error', handleError);
    img.src = src;

    return () => {
      img.removeEventListener('load', handleLoad);
      img.removeEventListener('error', handleError);
    };
  }, [hasIntersected, priority, src, alt, loadStartTime, isIntersecting, onLoad, onError]);

  // Progressive blur effect
  const imageClasses = `
    transition-all duration-300 ease-in-out
    ${isLoaded ? 'opacity-100' : 'opacity-90'}
    ${blurDataURL && !isLoaded ? 'blur-sm' : ''}
    ${hasError ? 'opacity-50 grayscale' : ''}
    ${className}
  `.trim();

  if (hasError) {
    return (
      <div 
        className={`bg-gray-200 flex items-center justify-center ${className}`}
        {...props}
      >
        <span className="text-gray-500 text-sm">Failed to load image</span>
      </div>
    );
  }

  return (
    <img
      ref={setCombinedRef}
      src={imageSrc}
      alt={alt}
      className={imageClasses}
      loading={priority ? 'eager' : 'lazy'}
      decoding="async"
      {...props}
    />
  );
});

LazyImage.displayName = 'LazyImage';
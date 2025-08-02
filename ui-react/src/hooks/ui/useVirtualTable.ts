import { useMemo, useCallback, useState, useEffect, useRef } from 'react';
import type { RequestHistoryItem, VirtualScrollConfig } from '@/types/requests';

interface VirtualTableItem {
  id: string;
  data: RequestHistoryItem;
  index: number;
  height: number;
}

interface UseVirtualTableOptions {
  items: RequestHistoryItem[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  getItemId?: (item: RequestHistoryItem) => string;
}

interface UseVirtualTableReturn {
  virtualItems: VirtualTableItem[];
  totalHeight: number;
  scrollToIndex: (index: number) => void;
  scrollToItem: (itemId: string) => void;
  containerRef: React.RefObject<HTMLDivElement>;
  scrollElementRef: React.RefObject<HTMLDivElement>;
  isScrolling: boolean;
  startIndex: number;
  endIndex: number;
}

const DEFAULT_CONFIG: VirtualScrollConfig = {
  itemHeight: 60,
  overscan: 5,
  threshold: 1,
};

export function useVirtualTable({
  items,
  itemHeight,
  containerHeight,
  overscan = DEFAULT_CONFIG.overscan,
  getItemId = (item) => item.id,
}: UseVirtualTableOptions): UseVirtualTableReturn {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // Calculate total height
  const totalHeight = useMemo(() => {
    return items.length * itemHeight;
  }, [items.length, itemHeight]);

  // Calculate visible range
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  // Generate virtual items
  const virtualItems = useMemo(() => {
    const result: VirtualTableItem[] = [];
    for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
      const item = items[i];
      if (item) {
        result.push({
          id: getItemId(item),
          data: item,
          index: i,
          height: itemHeight,
        });
      }
    }
    return result;
  }, [items, visibleRange, itemHeight, getItemId]);

  // Handle scroll events
  const handleScroll = useCallback((event: Event) => {
    const target = event.target as HTMLDivElement;
    setScrollTop(target.scrollTop);
    setIsScrolling(true);

    // Clear existing timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Set scrolling to false after scroll ends
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);
  }, []);

  // Scroll to specific index
  const scrollToIndex = useCallback((index: number) => {
    if (!scrollElementRef.current) return;

    const clampedIndex = Math.max(0, Math.min(index, items.length - 1));
    const scrollTop = clampedIndex * itemHeight;

    scrollElementRef.current.scrollTop = scrollTop;
  }, [items.length, itemHeight]);

  // Scroll to specific item
  const scrollToItem = useCallback((itemId: string) => {
    const index = items.findIndex(item => getItemId(item) === itemId);
    if (index !== -1) {
      scrollToIndex(index);
    }
  }, [items, getItemId, scrollToIndex]);

  // Setup scroll listener
  useEffect(() => {
    const scrollElement = scrollElementRef.current;
    if (!scrollElement) return;

    scrollElement.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      scrollElement.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return {
    virtualItems,
    totalHeight,
    scrollToIndex,
    scrollToItem,
    containerRef,
    scrollElementRef,
    isScrolling,
    startIndex: visibleRange.startIndex,
    endIndex: visibleRange.endIndex,
  };
}

// Hook for dynamic item heights (advanced virtualization)
interface UseDynamicVirtualTableOptions {
  items: RequestHistoryItem[];
  estimatedItemHeight: number;
  containerHeight: number;
  overscan?: number;
  getItemId?: (item: RequestHistoryItem) => string;
  getItemHeight?: (item: RequestHistoryItem, index: number) => number;
}

export function useDynamicVirtualTable({
  items,
  estimatedItemHeight,
  containerHeight,
  overscan = DEFAULT_CONFIG.overscan,
  getItemId = (item) => item.id,
  getItemHeight,
}: UseDynamicVirtualTableOptions) {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const [itemHeights, setItemHeights] = useState<Map<string, number>>(new Map());
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // Calculate item positions and heights
  const itemMetrics = useMemo(() => {
    let totalHeight = 0;
    const positions: number[] = [];
    const heights: number[] = [];

    items.forEach((item, index) => {
      positions[index] = totalHeight;

      const itemId = getItemId(item);
      let height = itemHeights.get(itemId);

      if (!height) {
        height = getItemHeight ? getItemHeight(item, index) : estimatedItemHeight;
      }

      heights[index] = height;
      totalHeight += height;
    });

    return { positions, heights, totalHeight };
  }, [items, itemHeights, estimatedItemHeight, getItemId, getItemHeight]);

  // Find visible range using binary search for efficiency
  const visibleRange = useMemo(() => {
    const { positions, heights } = itemMetrics;

    // Binary search for start index
    let startIndex = 0;
    let endIndex = positions.length - 1;

    while (startIndex <= endIndex) {
      const midIndex = Math.floor((startIndex + endIndex) / 2);
      const midPosition = positions[midIndex];

      if (midPosition < scrollTop) {
        startIndex = midIndex + 1;
      } else {
        endIndex = midIndex - 1;
      }
    }

    startIndex = Math.max(0, startIndex - overscan);

    // Find end index
    let visibleEndIndex = startIndex;
    let currentPosition = positions[startIndex] || 0;

    while (
      visibleEndIndex < positions.length &&
      currentPosition < scrollTop + containerHeight
    ) {
      currentPosition = positions[visibleEndIndex] + heights[visibleEndIndex];
      visibleEndIndex++;
    }

    visibleEndIndex = Math.min(positions.length - 1, visibleEndIndex + overscan);

    return { startIndex, endIndex: visibleEndIndex };
  }, [scrollTop, containerHeight, overscan, itemMetrics]);

  // Generate virtual items with dynamic positioning
  const virtualItems = useMemo(() => {
    const result: (VirtualTableItem & { offsetTop: number })[] = [];
    const { positions, heights } = itemMetrics;

    for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
      const item = items[i];
      if (item) {
        result.push({
          id: getItemId(item),
          data: item,
          index: i,
          height: heights[i] || estimatedItemHeight,
          offsetTop: positions[i] || 0,
        });
      }
    }
    return result;
  }, [items, visibleRange, itemMetrics, estimatedItemHeight, getItemId]);

  // Update item height measurement
  const measureItem = useCallback((itemId: string, height: number) => {
    setItemHeights(prev => {
      const updated = new Map(prev);
      updated.set(itemId, height);
      return updated;
    });
  }, []);

  // Handle scroll events
  const handleScroll = useCallback((event: Event) => {
    const target = event.target as HTMLDivElement;
    setScrollTop(target.scrollTop);
    setIsScrolling(true);

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);
  }, []);

  // Scroll to specific index
  const scrollToIndex = useCallback((index: number) => {
    if (!scrollElementRef.current) return;

    const clampedIndex = Math.max(0, Math.min(index, items.length - 1));
    const scrollTop = itemMetrics.positions[clampedIndex] || 0;

    scrollElementRef.current.scrollTop = scrollTop;
  }, [items.length, itemMetrics.positions]);

  // Scroll to specific item
  const scrollToItem = useCallback((itemId: string) => {
    const index = items.findIndex(item => getItemId(item) === itemId);
    if (index !== -1) {
      scrollToIndex(index);
    }
  }, [items, getItemId, scrollToIndex]);

  // Setup scroll listener
  useEffect(() => {
    const scrollElement = scrollElementRef.current;
    if (!scrollElement) return;

    scrollElement.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      scrollElement.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  return {
    virtualItems,
    totalHeight: itemMetrics.totalHeight,
    scrollToIndex,
    scrollToItem,
    containerRef,
    scrollElementRef,
    isScrolling,
    startIndex: visibleRange.startIndex,
    endIndex: visibleRange.endIndex,
    measureItem,
  };
}

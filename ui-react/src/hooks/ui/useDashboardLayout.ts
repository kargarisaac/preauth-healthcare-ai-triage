import { useState, useCallback, useEffect } from 'react';
import { DashboardWidget, DashboardConfig, DateRangePreset } from '../../types/analytics';
import { subDays, startOfDay, endOfDay, startOfWeek, endOfWeek, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, startOfYear, endOfYear } from 'date-fns';

interface UseDashboardLayoutOptions {
  storageKey?: string;
  defaultLayout?: 'grid' | 'columns' | 'rows';
}

interface UseDashboardLayoutReturn {
  // Configuration
  config: DashboardConfig;
  updateConfig: (updates: Partial<DashboardConfig>) => void;

  // Widgets
  widgets: DashboardWidget[];
  visibleWidgets: DashboardWidget[];
  addWidget: (widget: Omit<DashboardWidget, 'id' | 'lastUpdated'>) => void;
  updateWidget: (id: string, updates: Partial<DashboardWidget>) => void;
  removeWidget: (id: string) => void;
  toggleWidgetVisibility: (id: string) => void;
  reorderWidgets: (fromIndex: number, toIndex: number) => void;

  // Date Range
  dateRange: DateRangePreset;
  setDateRange: (range: DateRangePreset) => void;
  dateRangePresets: DateRangePreset[];

  // Layout Management
  resetLayout: () => void;
  exportLayout: () => string;
  importLayout: (layoutJson: string) => boolean;

  // Responsive
  isMobile: boolean;
  isTablet: boolean;
  screenSize: 'mobile' | 'tablet' | 'desktop';
}

const DEFAULT_CONFIG: DashboardConfig = {
  layout: 'grid',
  refreshInterval: 30,
  timezone: 'Asia/Dubai',
  currency: 'AED',
  dateFormat: 'dd/MM/yyyy',
  theme: 'light'
};

const DEFAULT_WIDGETS: DashboardWidget[] = [
  {
    id: 'metrics-overview',
    type: 'metric',
    title: 'Key Performance Metrics',
    size: 'large',
    position: { row: 0, col: 0, width: 2, height: 1 },
    config: { showTrends: true, showComparisons: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'processing-trends',
    type: 'chart',
    title: 'Processing Trends',
    size: 'large',
    position: { row: 0, col: 2, width: 2, height: 1 },
    config: { chartType: 'line', showLegend: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'format-distribution',
    type: 'chart',
    title: 'Format Distribution',
    size: 'medium',
    position: { row: 1, col: 0, width: 1, height: 1 },
    config: { chartType: 'pie', showPercentages: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'system-health',
    type: 'metric',
    title: 'System Health',
    size: 'medium',
    position: { row: 1, col: 1, width: 1, height: 1 },
    config: { showGauges: true, alertThresholds: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'cost-savings',
    type: 'chart',
    title: 'Cost Savings Tracker',
    size: 'large',
    position: { row: 1, col: 2, width: 2, height: 1 },
    config: { chartType: 'bar', showTargets: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'provider-performance',
    type: 'table',
    title: 'Provider Performance',
    size: 'large',
    position: { row: 2, col: 0, width: 2, height: 1 },
    config: { sortable: true, filterable: true, pageSize: 10 },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  },
  {
    id: 'geographic-heatmap',
    type: 'chart',
    title: 'Geographic Distribution',
    size: 'large',
    position: { row: 2, col: 2, width: 2, height: 1 },
    config: { chartType: 'heatmap', showTooltips: true },
    isVisible: true,
    lastUpdated: new Date().toISOString()
  }
];

export const useDashboardLayout = (
  options: UseDashboardLayoutOptions = {}
): UseDashboardLayoutReturn => {
  const { storageKey = 'healthcare-preauth-dashboard-layout', defaultLayout = 'grid' } = options;

  // State
  const [config, setConfig] = useState<DashboardConfig>(() => {
    const saved = localStorage.getItem(`${storageKey}-config`);
    if (saved) {
      try {
        return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      } catch {
        return { ...DEFAULT_CONFIG, layout: defaultLayout };
      }
    }
    return { ...DEFAULT_CONFIG, layout: defaultLayout };
  });

  const [widgets, setWidgets] = useState<DashboardWidget[]>(() => {
    const saved = localStorage.getItem(`${storageKey}-widgets`);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return DEFAULT_WIDGETS;
      }
    }
    return DEFAULT_WIDGETS;
  });

  const [dateRange, setDateRangeState] = useState<DateRangePreset>(() => {
    const now = new Date();
    return {
      id: 'last-7-days',
      label: 'Last 7 Days',
      startDate: startOfDay(subDays(now, 7)),
      endDate: endOfDay(now),
      isCustom: false
    };
  });

  const [screenSize, setScreenSize] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');

  // Date range presets
  const dateRangePresets: DateRangePreset[] = [
    {
      id: 'today',
      label: 'Today',
      startDate: startOfDay(new Date()),
      endDate: endOfDay(new Date()),
      isCustom: false
    },
    {
      id: 'yesterday',
      label: 'Yesterday',
      startDate: startOfDay(subDays(new Date(), 1)),
      endDate: endOfDay(subDays(new Date(), 1)),
      isCustom: false
    },
    {
      id: 'last-7-days',
      label: 'Last 7 Days',
      startDate: startOfDay(subDays(new Date(), 7)),
      endDate: endOfDay(new Date()),
      isCustom: false
    },
    {
      id: 'last-30-days',
      label: 'Last 30 Days',
      startDate: startOfDay(subDays(new Date(), 30)),
      endDate: endOfDay(new Date()),
      isCustom: false
    },
    {
      id: 'this-week',
      label: 'This Week',
      startDate: startOfWeek(new Date(), { weekStartsOn: 1 }),
      endDate: endOfWeek(new Date(), { weekStartsOn: 1 }),
      isCustom: false
    },
    {
      id: 'this-month',
      label: 'This Month',
      startDate: startOfMonth(new Date()),
      endDate: endOfMonth(new Date()),
      isCustom: false
    },
    {
      id: 'this-quarter',
      label: 'This Quarter',
      startDate: startOfQuarter(new Date()),
      endDate: endOfQuarter(new Date()),
      isCustom: false
    },
    {
      id: 'this-year',
      label: 'This Year',
      startDate: startOfYear(new Date()),
      endDate: endOfYear(new Date()),
      isCustom: false
    }
  ];

  // Computed values
  const visibleWidgets = widgets.filter(widget => widget.isVisible);
  const isMobile = screenSize === 'mobile';
  const isTablet = screenSize === 'tablet';

  // Configuration management
  const updateConfig = useCallback((updates: Partial<DashboardConfig>) => {
    setConfig(prev => {
      const newConfig = { ...prev, ...updates };
      localStorage.setItem(`${storageKey}-config`, JSON.stringify(newConfig));
      return newConfig;
    });
  }, [storageKey]);

  // Widget management
  const addWidget = useCallback((widget: Omit<DashboardWidget, 'id' | 'lastUpdated'>) => {
    const newWidget: DashboardWidget = {
      ...widget,
      id: `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      lastUpdated: new Date().toISOString()
    };

    setWidgets(prev => {
      const newWidgets = [...prev, newWidget];
      localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(newWidgets));
      return newWidgets;
    });
  }, [storageKey]);

  const updateWidget = useCallback((id: string, updates: Partial<DashboardWidget>) => {
    setWidgets(prev => {
      const newWidgets = prev.map(widget =>
        widget.id === id
          ? { ...widget, ...updates, lastUpdated: new Date().toISOString() }
          : widget
      );
      localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(newWidgets));
      return newWidgets;
    });
  }, [storageKey]);

  const removeWidget = useCallback((id: string) => {
    setWidgets(prev => {
      const newWidgets = prev.filter(widget => widget.id !== id);
      localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(newWidgets));
      return newWidgets;
    });
  }, [storageKey]);

  const toggleWidgetVisibility = useCallback((id: string) => {
    updateWidget(id, { isVisible: !widgets.find(w => w.id === id)?.isVisible });
  }, [widgets, updateWidget]);

  const reorderWidgets = useCallback((fromIndex: number, toIndex: number) => {
    setWidgets(prev => {
      const newWidgets = [...prev];
      const [removed] = newWidgets.splice(fromIndex, 1);
      newWidgets.splice(toIndex, 0, removed);
      localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(newWidgets));
      return newWidgets;
    });
  }, [storageKey]);

  // Date range management
  const setDateRange = useCallback((range: DateRangePreset) => {
    setDateRangeState(range);
  }, []);

  // Layout management
  const resetLayout = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
    setWidgets(DEFAULT_WIDGETS);
    localStorage.removeItem(`${storageKey}-config`);
    localStorage.removeItem(`${storageKey}-widgets`);
  }, [storageKey]);

  const exportLayout = useCallback(() => {
    return JSON.stringify({
      config,
      widgets,
      version: '1.0.0',
      exportedAt: new Date().toISOString()
    }, null, 2);
  }, [config, widgets]);

  const importLayout = useCallback((layoutJson: string) => {
    try {
      const imported = JSON.parse(layoutJson);

      if (imported.config && imported.widgets) {
        setConfig({ ...DEFAULT_CONFIG, ...imported.config });
        setWidgets(imported.widgets);

        localStorage.setItem(`${storageKey}-config`, JSON.stringify(imported.config));
        localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(imported.widgets));

        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, [storageKey]);

  // Screen size detection
  useEffect(() => {
    const updateScreenSize = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setScreenSize('mobile');
      } else if (width < 1024) {
        setScreenSize('tablet');
      } else {
        setScreenSize('desktop');
      }
    };

    updateScreenSize();
    window.addEventListener('resize', updateScreenSize);

    return () => window.removeEventListener('resize', updateScreenSize);
  }, []);

  // Auto-save widgets on change
  useEffect(() => {
    localStorage.setItem(`${storageKey}-widgets`, JSON.stringify(widgets));
  }, [widgets, storageKey]);

  return {
    config,
    updateConfig,
    widgets,
    visibleWidgets,
    addWidget,
    updateWidget,
    removeWidget,
    toggleWidgetVisibility,
    reorderWidgets,
    dateRange,
    setDateRange,
    dateRangePresets,
    resetLayout,
    exportLayout,
    importLayout,
    isMobile,
    isTablet,
    screenSize
  };
};
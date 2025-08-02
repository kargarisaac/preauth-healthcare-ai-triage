# Analytics Dashboard Components

A comprehensive analytics dashboard system for healthcare data visualization with real-time metrics, interactive charts, and performance tracking specifically designed for UAE pre-authorization workflows.

## Overview

The analytics dashboard provides:
- **Real-time Metrics**: Live KPI tracking with WebSocket integration
- **Interactive Charts**: Multiple chart types with customizable views
- **Performance Analysis**: Historical trends and provider performance
- **Cost Tracking**: ROI calculations and savings projections
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Export Capabilities**: PNG, PDF, and Excel export options

## Components

### 1. AnalyticsDashboard
Main dashboard component that orchestrates all analytics views.

```tsx
import { AnalyticsDashboard } from './components/dashboard/AnalyticsDashboard';

<AnalyticsDashboard className="p-6" />
```

**Features:**
- Tabbed interface (Overview, Performance, Financial)
- Real-time connection status
- Date range selection
- Export functionality
- Fullscreen mode
- Alert notifications

### 2. MetricsGrid
KPI metrics display with trend indicators and summary cards.

```tsx
import { MetricsGrid } from './components/dashboard/MetricsGrid';

<MetricsGrid
  metrics={analyticsMetrics}
  isLoading={false}
  showTrends={true}
/>
```

**Metrics Displayed:**
- Total Processed Requests
- Automation Rate
- Average Processing Time
- Success Rate
- Cost Savings YTD
- Data Quality Score
- Provider/Member Satisfaction

### 3. ProcessingCharts
Interactive charts for processing trends and format distribution.

```tsx
import { ProcessingCharts } from './components/dashboard/ProcessingCharts';

<ProcessingCharts
  trends={processingTrends}
  formatDistribution={formatDistribution}
  isLoading={false}
/>
```

**Chart Types:**
- Line charts for volume trends
- Area charts for performance metrics
- Pie charts for format distribution
- Bar charts for error analysis

### 4. PerformanceTrends
Historical performance analysis with provider rankings.

```tsx
import { PerformanceTrends } from './components/dashboard/PerformanceTrends';

<PerformanceTrends
  trends={trends}
  providerPerformance={providerPerformance}
  qualityMetrics={qualityMetrics}
  isLoading={false}
/>
```

**Features:**
- Performance trend cards with targets
- Historical trend visualization
- Provider performance ranking
- Quality metrics breakdown
- Error rate analysis

### 5. CostSavingsTracker
Financial impact tracking with ROI calculations.

```tsx
import { CostSavingsTracker } from './components/dashboard/CostSavingsTracker';

<CostSavingsTracker
  costSavings={costSavingsBreakdown}
  metrics={analyticsMetrics}
  isLoading={false}
/>
```

**Features:**
- ROI calculator
- Yearly projections
- Savings breakdown by category
- Historical trends
- Target tracking

## Custom Hooks

### useAnalytics
Main hook for analytics data management.

```tsx
import { useAnalytics } from './hooks/data/useAnalytics';

const {
  data,
  metrics,
  loading,
  error,
  refresh,
  exportData
} = useAnalytics({
  autoRefresh: true,
  refreshInterval: 30,
  dateRange: dateRangePreset
});
```

### useRealTimeMetrics
WebSocket integration for real-time updates.

```tsx
import { useRealTimeMetrics } from './hooks/data/useRealTimeMetrics';

const {
  metrics,
  systemHealth,
  isConnected,
  connectionStatus,
  lastUpdate
} = useRealTimeMetrics({
  enabled: true,
  reconnectInterval: 5000
});
```

### useChartData
Chart data formatting and transformation.

```tsx
import { useChartData } from './hooks/charts/useChartData';

const {
  processingTrendData,
  formatDistributionData,
  providerPerformanceData,
  automationRateGauge,
  formatCurrency,
  formatPercentage
} = useChartData(trends, formatDistribution, providers, costSavings);
```

### useDashboardLayout
Dashboard configuration and layout management.

```tsx
import { useDashboardLayout } from './hooks/ui/useDashboardLayout';

const {
  config,
  widgets,
  dateRange,
  setDateRange,
  resetLayout,
  exportLayout,
  isMobile
} = useDashboardLayout();
```

## Data Types

### Core Analytics Types
```typescript
// Key metrics interface
interface AnalyticsMetrics {
  totalProcessed: number;
  automationRate: number;
  avgProcessingTime: number;
  successRate: number;
  costSavings: number;
  // ... more metrics
}

// Processing trend data
interface ProcessingTrend {
  date: string;
  volume: number;
  processingTime: number;
  successRate: number;
  automationRate: number;
}

// Provider performance
interface ProviderPerformance {
  providerId: string;
  providerName: string;
  qualityScore: number;
  approvalRate: number;
  // ... more fields
}
```

### Chart Data Types
```typescript
interface LineChartData {
  id: string;
  name: string;
  data: ChartDataPoint[];
  color: string;
}

interface PieChartData {
  name: string;
  value: number;
  percentage: number;
  color: string;
}
```

## Configuration

### Date Range Presets
```typescript
const dateRangePresets = [
  { id: 'today', label: 'Today' },
  { id: 'last-7-days', label: 'Last 7 Days' },
  { id: 'last-30-days', label: 'Last 30 Days' },
  { id: 'this-month', label: 'This Month' },
  { id: 'this-quarter', label: 'This Quarter' }
];
```

### Chart Colors
```typescript
const CHART_COLORS = {
  primary: '#0066cc',      // Nazmito Blue
  secondary: '#00a86b',    // Success Green
  accent: '#ff6b35',       // Warning Orange
  error: '#dc3545',        // Error Red
  info: '#17a2b8'          // Info Cyan
};
```

## API Integration

### Analytics Endpoint
```typescript
// Fetch analytics data
GET /api/analytics?start_date=2024-01-01&end_date=2024-12-31

// Response
interface AnalyticsApiResponse {
  success: boolean;
  data: AnalyticsDashboardData;
  metadata: {
    generatedAt: string;
    dataRange: { start: string; end: string };
    totalRecords: number;
  };
}
```

### WebSocket Connection
```typescript
// Real-time updates via WebSocket
const ws = new WebSocket('ws://localhost:8000/api/ws/analytics');

// Message format
interface RealTimeUpdate {
  timestamp: string;
  type: 'metric_update' | 'alert' | 'system_status';
  data: any;
  priority: 'low' | 'medium' | 'high';
}
```

## Responsive Design

The dashboard is built with mobile-first principles:

- **Mobile (< 768px)**: Single column layout, collapsed navigation
- **Tablet (768px - 1024px)**: Two column grid, slide-out navigation
- **Desktop (> 1024px)**: Multi-column grid, persistent sidebar

## Healthcare-Specific Features

### UAE Standards Support
- **eClaimLink** (Dubai Health Authority)
- **Shafafiya** (Abu Dhabi Department of Health)
- **ICD-10-AM** diagnostic codes
- **CPT** procedure codes

### Key Metrics for Healthcare
- Pre-authorization processing times
- Claims approval rates
- Provider performance scores
- Member satisfaction tracking
- Cost per transaction
- SLA compliance rates

### Performance Targets
- Processing Time: < 15 minutes average
- Success Rate: > 95%
- Automation Rate: > 85%
- Data Quality: > 90%
- SLA Compliance: > 95%

## Usage Example

```tsx
import React from 'react';
import { DashboardPage } from './components/dashboard/DashboardPage';

function App() {
  return (
    <div className="App">
      <DashboardPage />
    </div>
  );
}

export default App;
```

## Performance Considerations

- **Lazy Loading**: Charts load only when visible
- **Virtualization**: Large datasets use virtual scrolling
- **Caching**: API responses cached for 30 seconds
- **Debouncing**: User interactions debounced (300ms)
- **Bundle Splitting**: Charts loaded separately from main bundle

## Accessibility

- **WCAG 2.1 AA** compliant
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: ARIA labels and descriptions
- **Color Contrast**: 4.5:1 minimum ratio
- **Focus Management**: Proper focus indicators

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- **React 18**: Core framework
- **Recharts**: Chart library
- **date-fns**: Date manipulation
- **Tailwind CSS**: Styling
- **Lucide React**: Icons

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

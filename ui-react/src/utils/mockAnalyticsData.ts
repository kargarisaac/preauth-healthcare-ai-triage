import { 
  AnalyticsDashboardData,
  AnalyticsMetrics,
  ProcessingTrend,
  FormatDistribution,
  ProviderPerformance,
  CostSavingsBreakdown,
  QualityMetrics,
  TimeBasedHeatmap,
  GeographicData,
  AlertThreshold,
  SystemHealth
} from '../types/analytics';

// Utility functions for generating realistic data
const randomBetween = (min: number, max: number): number => 
  Math.random() * (max - min) + min;

const randomInt = (min: number, max: number): number => 
  Math.floor(randomBetween(min, max));

const getRandomDate = (daysAgo: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date.toISOString().split('T')[0];
};

// UAE healthcare providers
const UAE_PROVIDERS = [
  'Emirates Health Services',
  'Cleveland Clinic Abu Dhabi',
  'Mediclinic Middle East',
  'NMC Healthcare',
  'Aster DM Healthcare',
  'VPS Healthcare',
  'Burjeel Holdings',
  'Prime Healthcare Group',
  'Thumbay Group',
  'Al Zahra Hospital Group'
];

// UAE Emirates
const UAE_EMIRATES = [
  'Dubai',
  'Abu Dhabi', 
  'Sharjah',
  'Ajman',
  'Fujairah',
  'Ras Al Khaimah',
  'Umm Al Quwain'
] as const;

// Healthcare service categories for cost savings
const COST_CATEGORIES = [
  'Automated Authorization',
  'Data Processing Efficiency',
  'Manual Review Reduction',
  'Error Prevention',
  'Compliance Automation',
  'Provider Portal Integration',
  'Member Communication',
  'Audit Trail Automation'
];

export const generateMockAnalyticsMetrics = (): AnalyticsMetrics => ({
  // Processing Volume Metrics
  totalProcessed: randomInt(75000, 125000),
  dailyVolume: randomInt(800, 1500),
  monthlyVolume: randomInt(18000, 35000),
  volumeGrowthRate: randomBetween(0.05, 0.25), // 5-25% growth
  
  // Automation & Efficiency Metrics
  automationRate: randomBetween(0.82, 0.96), // 82-96%
  manualTouchPoints: randomInt(15, 45),
  avgProcessingTime: randomInt(180, 900), // 3-15 minutes in seconds
  slaCompliance: randomBetween(0.89, 0.98), // 89-98%
  
  // Quality & Performance Metrics
  dataQualityScore: randomBetween(0.88, 0.97), // 88-97%
  errorRate: randomBetween(0.01, 0.06), // 1-6%
  successRate: randomBetween(0.91, 0.98), // 91-98%
  reprocessingRate: randomBetween(0.005, 0.025), // 0.5-2.5%
  
  // Financial Metrics
  costSavings: randomInt(35000, 75000), // Monthly savings in AED
  roiPercentage: randomBetween(180, 320), // 180-320% ROI
  avgCostPerTransaction: randomBetween(8, 18), // 8-18 AED per transaction
  totalSavingsYTD: randomInt(400000, 850000), // YTD savings in AED
  
  // Provider & Member Metrics
  providerSatisfactionScore: randomBetween(4.1, 4.8), // Out of 5
  memberSatisfactionScore: randomBetween(4.3, 4.9), // Out of 5
  avgResponseTime: randomBetween(12, 35), // 12-35 minutes
  firstCallResolution: randomBetween(0.78, 0.92) // 78-92%
});

export const generateMockProcessingTrends = (days: number = 30): ProcessingTrend[] => {
  return Array.from({ length: days }, (_, i) => {
    const baseVolume = randomInt(600, 1200);
    const seasonalFactor = 1 + 0.3 * Math.sin((i / 7) * Math.PI); // Weekly pattern
    
    return {
      date: getRandomDate(days - i - 1),
      volume: Math.round(baseVolume * seasonalFactor),
      processingTime: randomInt(180, 780), // 3-13 minutes
      successRate: randomBetween(0.89, 0.97),
      errorCount: randomInt(3, 25),
      automationRate: randomBetween(0.80, 0.95)
    };
  });
};

export const generateMockFormatDistribution = (): FormatDistribution[] => {
  const formats: FormatDistribution['format'][] = [
    'eClaimLink', 'Shafafiya', 'CSV', 'Claims CSV', 'Clinical CSV'
  ];
  
  const totalRequests = randomInt(8000, 15000);
  let remaining = totalRequests;
  
  return formats.map((format, index) => {
    const isLast = index === formats.length - 1;
    const count = isLast ? remaining : randomInt(Math.floor(remaining * 0.1), Math.floor(remaining * 0.4));
    remaining -= count;
    
    return {
      format,
      count,
      percentage: (count / totalRequests) * 100,
      avgProcessingTime: randomInt(120, 600), // 2-10 minutes
      successRate: randomBetween(0.88, 0.96)
    };
  });
};

export const generateMockProviderPerformance = (): ProviderPerformance[] => {
  return UAE_PROVIDERS.map(provider => ({
    providerId: `PRV-${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
    providerName: provider,
    totalRequests: randomInt(500, 3000),
    approvalRate: randomBetween(0.75, 0.92),
    avgResponseTime: randomBetween(15, 45), // minutes
    qualityScore: randomBetween(0.72, 0.95),
    costSavings: randomInt(15000, 65000), // AED per month
    satisfactionScore: randomBetween(3.8, 4.7) // Out of 5
  }));
};

export const generateMockCostSavingsBreakdown = (): CostSavingsBreakdown[] => {
  const totalSavings = randomInt(45000, 85000);
  let remaining = totalSavings;
  
  return COST_CATEGORIES.map((category, index) => {
    const isLast = index === COST_CATEGORIES.length - 1;
    const amount = isLast ? remaining : randomInt(
      Math.floor(totalSavings * 0.05), 
      Math.floor(totalSavings * 0.25)
    );
    remaining -= amount;
    
    const trends: ('up' | 'down' | 'stable')[] = ['up', 'down', 'stable'];
    const trend = trends[Math.floor(Math.random() * trends.length)];
    
    return {
      category,
      amount: Math.max(0, amount),
      percentage: (amount / totalSavings) * 100,
      trend,
      comparison: randomBetween(-15, 25) // vs previous period
    };
  });
};

export const generateMockQualityMetrics = (): QualityMetrics[] => {
  const qualityMeasures = [
    { 
      measure: 'Data Completeness',
      unit: '%',
      description: 'Percentage of complete data records'
    },
    {
      measure: 'Processing Accuracy',
      unit: '%', 
      description: 'Accuracy of automated processing'
    },
    {
      measure: 'Response Time SLA',
      unit: '%',
      description: 'Requests processed within SLA'
    },
    {
      measure: 'Error Resolution',
      unit: '%',
      description: 'Errors resolved within target time'
    },
    {
      measure: 'Provider Adoption',
      unit: '%',
      description: 'Providers using digital channels'
    }
  ];

  return qualityMeasures.map(({ measure, unit, description }) => {
    const target = randomBetween(85, 95);
    const current = randomBetween(target * 0.7, target * 1.1);
    
    const trends: ('improving' | 'stable' | 'declining')[] = ['improving', 'stable', 'declining'];
    const trend = trends[Math.floor(Math.random() * trends.length)];
    
    return {
      metric: measure,
      current,
      target,
      trend,
      benchmark: randomBetween(target * 0.8, target * 0.95),
      unit
    };
  });
};

export const generateMockHeatmapData = (): TimeBasedHeatmap[] => {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] as const;
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const data: TimeBasedHeatmap[] = [];
  
  days.forEach(day => {
    hours.forEach(hour => {
      // Business hours (8-18) have higher volume
      const isBusinessHours = hour >= 8 && hour <= 18;
      const isWeekend = day === 'Saturday' || day === 'Sunday';
      
      let baseVolume = isBusinessHours ? randomInt(80, 150) : randomInt(10, 40);
      if (isWeekend) baseVolume *= 0.3;
      
      const volume = Math.round(baseVolume);
      const maxVolume = 150;
      const intensity = Math.min(volume / maxVolume, 1);
      
      data.push({
        hour,
        day,
        volume,
        intensity
      });
    });
  });
  
  return data;
};

export const generateMockGeographicData = (): GeographicData[] => {
  return UAE_EMIRATES.map(emirate => {
    const requests = randomInt(500, 5000);
    const topProviders = UAE_PROVIDERS
      .sort(() => Math.random() - 0.5)
      .slice(0, randomInt(2, 4));
    
    return {
      emirate,
      requests,
      approvalRate: randomBetween(0.78, 0.94),
      avgProcessingTime: randomBetween(12, 35), // minutes
      topProviders
    };
  });
};

export const generateMockAlertThresholds = (): AlertThreshold[] => {
  const alertConfigs = [
    {
      metric: 'avgProcessingTime' as keyof AnalyticsMetrics,
      name: 'Average Processing Time',
      unit: 'minutes',
      warningThreshold: 20,
      criticalThreshold: 30
    },
    {
      metric: 'errorRate' as keyof AnalyticsMetrics,
      name: 'Error Rate',
      unit: '%',
      warningThreshold: 5,
      criticalThreshold: 10
    },
    {
      metric: 'automationRate' as keyof AnalyticsMetrics,
      name: 'Automation Rate',
      unit: '%',
      warningThreshold: 80,
      criticalThreshold: 70
    },
    {
      metric: 'slaCompliance' as keyof AnalyticsMetrics,
      name: 'SLA Compliance',
      unit: '%',
      warningThreshold: 90,
      criticalThreshold: 85
    }
  ];

  return alertConfigs.map(config => {
    const currentValue = config.metric === 'avgProcessingTime' ? 
      randomBetween(10, 35) :
      config.metric === 'errorRate' ?
      randomBetween(1, 12) :
      config.metric === 'automationRate' ?
      randomBetween(65, 95) :
      randomBetween(80, 98);

    let status: 'normal' | 'warning' | 'critical' = 'normal';
    
    if (config.metric === 'avgProcessingTime' || config.metric === 'errorRate') {
      // Higher values are bad
      if (currentValue >= config.criticalThreshold) status = 'critical';
      else if (currentValue >= config.warningThreshold) status = 'warning';
    } else {
      // Lower values are bad
      if (currentValue <= config.criticalThreshold) status = 'critical';
      else if (currentValue <= config.warningThreshold) status = 'warning';
    }

    return {
      id: `alert-${Math.random().toString(36).substr(2, 8)}`,
      metric: config.metric,
      name: config.name,
      warningThreshold: config.warningThreshold,
      criticalThreshold: config.criticalThreshold,
      currentValue,
      unit: config.unit,
      status,
      lastTriggered: status !== 'normal' ? new Date(Date.now() - randomInt(0, 3600000)).toISOString() : undefined
    };
  });
};

export const generateMockSystemHealth = (): SystemHealth => {
  const cpuUsage = randomBetween(15, 85);
  const memoryUsage = randomBetween(35, 80);
  const diskUsage = randomBetween(45, 75);
  const errorRate = randomBetween(0.1, 3.5);
  
  let status: SystemHealth['status'] = 'healthy';
  if (cpuUsage > 90 || memoryUsage > 90 || diskUsage > 90 || errorRate > 5) {
    status = 'critical';
  } else if (cpuUsage > 75 || memoryUsage > 80 || diskUsage > 80 || errorRate > 2) {
    status = 'warning';
  }
  
  return {
    cpuUsage,
    memoryUsage,
    diskUsage,
    apiResponseTime: randomBetween(50, 500), // milliseconds
    errorRate,
    uptime: randomInt(86400, 2592000), // 1 day to 30 days in seconds
    status
  };
};

export const generateMockAnalyticsDashboardData = (): AnalyticsDashboardData => ({
  metrics: generateMockAnalyticsMetrics(),
  trends: generateMockProcessingTrends(30),
  formatDistribution: generateMockFormatDistribution(),
  providerPerformance: generateMockProviderPerformance(),
  systemHealth: generateMockSystemHealth(),
  costSavings: generateMockCostSavingsBreakdown(),
  qualityMetrics: generateMockQualityMetrics(),
  heatmapData: generateMockHeatmapData(),
  geographicData: generateMockGeographicData(),
  alerts: generateMockAlertThresholds()
});

// Utility functions for data aggregation
export const aggregateDataByPeriod = (
  trends: ProcessingTrend[],
  period: 'daily' | 'weekly' | 'monthly'
): ProcessingTrend[] => {
  if (period === 'daily') return trends;
  
  const groupSize = period === 'weekly' ? 7 : 30;
  const aggregated: ProcessingTrend[] = [];
  
  for (let i = 0; i < trends.length; i += groupSize) {
    const group = trends.slice(i, i + groupSize);
    if (group.length === 0) continue;
    
    const avgVolume = group.reduce((sum, t) => sum + t.volume, 0) / group.length;
    const avgProcessingTime = group.reduce((sum, t) => sum + t.processingTime, 0) / group.length;
    const avgSuccessRate = group.reduce((sum, t) => sum + t.successRate, 0) / group.length;
    const totalErrors = group.reduce((sum, t) => sum + t.errorCount, 0);
    const avgAutomationRate = group.reduce((sum, t) => sum + t.automationRate, 0) / group.length;
    
    aggregated.push({
      date: group[0].date,
      volume: Math.round(avgVolume),
      processingTime: Math.round(avgProcessingTime),
      successRate: avgSuccessRate,
      errorCount: totalErrors,
      automationRate: avgAutomationRate
    });
  }
  
  return aggregated;
};

export const calculateTrendDirection = (data: number[]): 'up' | 'down' | 'stable' => {
  if (data.length < 2) return 'stable';
  
  const first = data[0];
  const last = data[data.length - 1];
  const changePercent = ((last - first) / first) * 100;
  
  if (Math.abs(changePercent) < 2) return 'stable';
  return changePercent > 0 ? 'up' : 'down';
};
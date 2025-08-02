import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Target, TrendingUp, Clock, CheckCircle, AlertTriangle, Award } from 'lucide-react';
import Card from '../ui/Card';
import { GaugeChartData } from '../../types/analytics';
import { useResponsiveChart } from '../../hooks/ui/useResponsiveChart';

interface GaugeMetricsProps {
  gauges: Array<{
    id: string;
    title: string;
    data: GaugeChartData;
    icon: React.ReactNode;
    description?: string;
  }>;
  isLoading?: boolean;
  className?: string;
}

interface AnimatedGaugeProps {
  data: GaugeChartData;
  size?: number;
  title: string;
  icon: React.ReactNode;
  description?: string;
}

const AnimatedGauge: React.FC<AnimatedGaugeProps> = ({
  data,
  size = 160,
  title,
  icon,
  description
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const { currentBreakpoint } = useResponsiveChart();

  // Adjust size based on screen size
  const responsiveSize = React.useMemo(() => {
    switch (currentBreakpoint) {
      case 'xs': return Math.max(120, size * 0.7);
      case 'sm': return Math.max(140, size * 0.8);
      case 'md': return Math.max(150, size * 0.9);
      default: return size;
    }
  }, [currentBreakpoint, size]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = responsiveSize;
    const height = responsiveSize;
    const radius = Math.min(width, height) / 2 - 20;
    const centerX = width / 2;
    const centerY = height / 2;

    const g = svg.append('g')
      .attr('transform', `translate(${centerX}, ${centerY})`);

    // Create scales
    const angleScale = d3.scaleLinear()
      .domain([data.min, data.max])
      .range([-Math.PI * 0.75, Math.PI * 0.75]); // 270 degrees total

    const colorScale = d3.scaleThreshold<number, string>()
      .domain(data.thresholds.map(t => t.value))
      .range(data.thresholds.map(t => t.color));

    // Create arc generators
    const backgroundArc = d3.arc()
      .innerRadius(radius * 0.65)
      .outerRadius(radius * 0.85)
      .startAngle(-Math.PI * 0.75)
      .endAngle(Math.PI * 0.75);

    const valueArc = d3.arc()
      .innerRadius(radius * 0.65)
      .outerRadius(radius * 0.85)
      .startAngle(-Math.PI * 0.75);

    // Draw background arc
    g.append('path')
      .datum({ endAngle: Math.PI * 0.75 })
      .style('fill', '#e5e7eb')
      .attr('d', backgroundArc as any);

    // Draw threshold segments
    data.thresholds.forEach((threshold, i) => {
      const startAngle = i === 0 ? -Math.PI * 0.75 : angleScale(data.thresholds[i - 1].value);
      const endAngle = angleScale(threshold.value);

      const thresholdArc = d3.arc()
        .innerRadius(radius * 0.65)
        .outerRadius(radius * 0.85)
        .startAngle(startAngle)
        .endAngle(endAngle);

      g.append('path')
        .style('fill', threshold.color)
        .style('opacity', 0.3)
        .attr('d', thresholdArc as any);
    });

    // Draw value arc with animation
    const valuePath = g.append('path')
      .datum({ endAngle: -Math.PI * 0.75 })
      .style('fill', colorScale(data.value))
      .attr('d', valueArc as any);

    // Animate the value arc
    valuePath.transition()
      .duration(1500)
      .ease(d3.easeElastic.period(0.4))
      .attrTween('d', function() {
        const interpolate = d3.interpolate(-Math.PI * 0.75, angleScale(data.value));
        return function(t) {
          const currentArc = d3.arc()
            .innerRadius(radius * 0.65)
            .outerRadius(radius * 0.85)
            .startAngle(-Math.PI * 0.75)
            .endAngle(interpolate(t));
          return currentArc({} as any) || '';
        };
      });

    // Draw needle
    const needleLength = radius * 0.6;
    const needleAngle = angleScale(data.value);

    const needleGroup = g.append('g')
      .attr('class', 'needle');

    // Needle line
    needleGroup.append('line')
      .attr('x1', 0)
      .attr('y1', 0)
      .attr('x2', 0)
      .attr('y2', -needleLength)
      .attr('stroke', '#374151')
      .attr('stroke-width', 3)
      .attr('stroke-linecap', 'round')
      .style('opacity', 0)
      .transition()
      .delay(800)
      .duration(700)
      .style('opacity', 1)
      .attr('transform', `rotate(${(needleAngle * 180) / Math.PI})`);

    // Needle center
    needleGroup.append('circle')
      .attr('r', 6)
      .attr('fill', '#374151')
      .style('opacity', 0)
      .transition()
      .delay(800)
      .duration(300)
      .style('opacity', 1);

    // Draw tick marks
    const tickData = d3.range(data.min, data.max + 1, (data.max - data.min) / 10);
    const ticks = g.selectAll('.tick')
      .data(tickData)
      .enter()
      .append('g')
      .attr('class', 'tick')
      .attr('transform', d => `rotate(${(angleScale(d) * 180) / Math.PI})`);

    ticks.append('line')
      .attr('x1', 0)
      .attr('y1', -radius * 0.9)
      .attr('x2', 0)
      .attr('y2', -radius * 0.85)
      .attr('stroke', '#9ca3af')
      .attr('stroke-width', 1);

    // Draw labels for thresholds
    data.thresholds.forEach(threshold => {
      const angle = angleScale(threshold.value);
      const labelRadius = radius * 1.1;
      const x = Math.sin(angle) * labelRadius;
      const y = -Math.cos(angle) * labelRadius;

      g.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .style('font-size', '10px')
        .style('fill', '#6b7280')
        .style('font-weight', '500')
        .text(threshold.value);
    });

    // Draw target indicator if provided
    if (data.target !== undefined) {
      const targetAngle = angleScale(data.target);
      const targetRadius = radius * 0.95;

      g.append('circle')
        .attr('cx', Math.sin(targetAngle) * targetRadius)
        .attr('cy', -Math.cos(targetAngle) * targetRadius)
        .attr('r', 4)
        .attr('fill', '#ef4444')
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 2)
        .style('opacity', 0)
        .transition()
        .delay(1200)
        .duration(300)
        .style('opacity', 1);
    }

    // Center value display
    const valueGroup = g.append('g')
      .attr('class', 'center-value');

    valueGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('y', -5)
      .style('font-size', `${Math.max(16, responsiveSize * 0.12)}px`)
      .style('font-weight', 'bold')
      .style('fill', '#111827')
      .style('opacity', 0)
      .text(data.value.toFixed(1))
      .transition()
      .delay(1000)
      .duration(500)
      .style('opacity', 1);

    valueGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('y', 15)
      .style('font-size', `${Math.max(10, responsiveSize * 0.06)}px`)
      .style('fill', '#6b7280')
      .style('opacity', 0)
      .text('%')
      .transition()
      .delay(1200)
      .duration(300)
      .style('opacity', 1);

  }, [data, responsiveSize]);

  const getStatusColor = () => {
    const threshold = data.thresholds.find(t => data.value <= t.value);
    return threshold?.color || '#6b7280';
  };

  const getStatusLabel = () => {
    const threshold = data.thresholds.find(t => data.value <= t.value);
    return threshold?.label || 'Unknown';
  };

  return (
    <Card className="p-4 text-center">
      <div className="flex items-center justify-center mb-2">
        <div className="p-2 rounded-lg bg-gray-50 text-gray-600">
          {icon}
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-900 mb-1">{title}</h3>

      <svg
        ref={svgRef}
        width={responsiveSize}
        height={responsiveSize}
        className="mx-auto"
      />

      <div className="mt-2 space-y-1">
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white`}
             style={{ backgroundColor: getStatusColor() }}>
          {getStatusLabel()}
        </div>

        {data.target !== undefined && (
          <p className="text-xs text-gray-500">
            Target: {data.target}%
          </p>
        )}

        {description && (
          <p className="text-xs text-gray-600 mt-2">
            {description}
          </p>
        )}
      </div>
    </Card>
  );
};

export const GaugeMetrics: React.FC<GaugeMetricsProps> = ({
  gauges,
  isLoading = false,
  className = ''
}) => {
  if (isLoading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 ${className}`}>
        {Array.from({ length: 4 }, (_, i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-24 mx-auto"></div>
              <div className="h-32 bg-gray-200 rounded-full mx-auto"></div>
              <div className="h-3 bg-gray-200 rounded w-16 mx-auto"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Performance Gauges</h2>
          <p className="text-sm text-gray-600">Real-time key performance indicators</p>
        </div>

        <div className="flex items-center text-sm text-gray-500">
          <Target className="h-4 w-4 mr-1" />
          <span>Target indicators shown in red</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {gauges.map((gauge) => (
          <AnimatedGauge
            key={gauge.id}
            data={gauge.data}
            title={gauge.title}
            icon={gauge.icon}
            description={gauge.description}
          />
        ))}
      </div>

      {/* Summary insights */}
      <Card className="p-6 mt-6">
        <div className="flex items-center mb-4">
          <Award className="h-5 w-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Performance Summary</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
            <p className="text-sm text-gray-600">Metrics on Target</p>
            <p className="text-2xl font-bold text-gray-900">
              {gauges.filter(g => g.data.target && Math.abs(g.data.value - g.data.target) <= (g.data.target * 0.1)).length}
            </p>
            <p className="text-xs text-gray-500">of {gauges.length} total</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
            <p className="text-sm text-gray-600">Average Performance</p>
            <p className="text-2xl font-bold text-gray-900">
              {(gauges.reduce((sum, g) => sum + g.data.value, 0) / gauges.length).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500">across all metrics</p>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
            </div>
            <p className="text-sm text-gray-600">Needs Attention</p>
            <p className="text-2xl font-bold text-gray-900">
              {gauges.filter(g => {
                const lowestThreshold = Math.min(...g.data.thresholds.map(t => t.value));
                return g.data.value <= lowestThreshold;
              }).length}
            </p>
            <p className="text-xs text-gray-500">metrics below target</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

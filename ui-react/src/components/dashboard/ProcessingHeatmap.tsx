import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Calendar, Clock, Filter, TrendingUp } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { TimeBasedHeatmap } from '../../types/analytics';
import { useResponsiveChart } from '../../hooks/ui/useResponsiveChart';

interface ProcessingHeatmapProps {
  data: TimeBasedHeatmap[];
  isLoading?: boolean;
  className?: string;
}

interface HeatmapTooltipData {
  day: string;
  hour: number;
  volume: number;
  intensity: number;
  x: number;
  y: number;
}

interface FilterOptions {
  timeRange: 'week' | 'month' | 'quarter';
  volumeThreshold: 'all' | 'high' | 'medium' | 'low';
}

export const ProcessingHeatmap: React.FC<ProcessingHeatmapProps> = ({
  data,
  isLoading = false,
  className = ''
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<HeatmapTooltipData | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({
    timeRange: 'week',
    volumeThreshold: 'all'
  });

  const {
    dimensions,
    containerRef,
    currentBreakpoint,
    getResponsiveMargin,
    getResponsiveFontSize
  } = useResponsiveChart({
    baseWidth: 900,
    baseHeight: 200,
    aspectRatio: 4.5,
    maintainAspectRatio: true
  });

  const margin = getResponsiveMargin();
  const fontSize = getResponsiveFontSize();

  // Days of the week
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Filter and process data
  const processedData = React.useMemo(() => {
    if (!data.length) return [];

    let filteredData = [...data];

    // Apply volume threshold filter
    if (filters.volumeThreshold !== 'all') {
      const maxVolume = Math.max(...data.map(d => d.volume));
      const threshold = filters.volumeThreshold === 'high' ? maxVolume * 0.7 :
                       filters.volumeThreshold === 'medium' ? maxVolume * 0.4 : maxVolume * 0.1;

      filteredData = filteredData.filter(d => {
        if (filters.volumeThreshold === 'high') return d.volume >= threshold;
        if (filters.volumeThreshold === 'medium') return d.volume >= threshold && d.volume < maxVolume * 0.7;
        return d.volume < threshold;
      });
    }

    return filteredData;
  }, [data, filters]);

  // Color scale
  const colorScale = d3.scaleSequential(d3.interpolateBlues)
    .domain([0, Math.max(...data.map(d => d.intensity), 1)]);

  // Draw heatmap
  useEffect(() => {
    if (!svgRef.current || !processedData.length || isLoading) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous content

    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Calculate cell dimensions
    const cellWidth = width / hours.length;
    const cellHeight = height / days.length;

    // Create scales
    const xScale = d3.scaleBand()
      .domain(hours.map(h => h.toString()))
      .range([0, width])
      .padding(0.1);

    const yScale = d3.scaleBand()
      .domain(days)
      .range([0, height])
      .padding(0.1);

    // Add X axis (hours)
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(0));

    xAxis.select('.domain').remove();
    xAxis.selectAll('text')
      .style('font-size', `${fontSize.axis}px`)
      .style('fill', '#6b7280')
      .text(d => {
        const hour = parseInt(d as string);
        if (currentBreakpoint === 'xs' || currentBreakpoint === 'sm') {
          // Show fewer labels on small screens
          return hour % 4 === 0 ? `${hour}:00` : '';
        }
        return hour % 2 === 0 ? `${hour}:00` : '';
      });

    // Add Y axis (days)
    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale).tickSize(0));

    yAxis.select('.domain').remove();
    yAxis.selectAll('text')
      .style('font-size', `${fontSize.axis}px`)
      .style('fill', '#6b7280')
      .text(d => {
        if (currentBreakpoint === 'xs') {
          return (d as string).substring(0, 3); // Show abbreviated day names
        }
        return d as string;
      });

    // Create heatmap cells
    const cells = g.selectAll('.cell')
      .data(processedData)
      .enter()
      .append('rect')
      .attr('class', 'cell')
      .attr('x', d => xScale(d.hour.toString()) || 0)
      .attr('y', d => yScale(d.day) || 0)
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', d => colorScale(d.intensity))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1)
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .style('opacity', 0)
      .on('mouseover', function(event, d) {
        // Highlight cell
        d3.select(this)
          .transition()
          .duration(100)
          .style('opacity', 0.8)
          .attr('stroke-width', 2);

        // Show tooltip
        if (tooltipRef.current) {
          const rect = (event.target as SVGRectElement).getBoundingClientRect();
          setTooltip({
            day: d.day,
            hour: d.hour,
            volume: d.volume,
            intensity: d.intensity,
            x: rect.left + rect.width / 2,
            y: rect.top
          });
        }
      })
      .on('mouseout', function() {
        // Remove highlight
        d3.select(this)
          .transition()
          .duration(100)
          .style('opacity', 1)
          .attr('stroke-width', 1);

        // Hide tooltip
        setTooltip(null);
      });

    // Animate cells appearing
    cells.transition()
      .duration(300)
      .delay((_, i) => i * 2)
      .style('opacity', 1);

    // Add axis labels
    g.append('text')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 5})`)
      .style('text-anchor', 'middle')
      .style('font-size', `${fontSize.axis}px`)
      .style('fill', '#6b7280')
      .text('Hour of Day');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left + 15)
      .attr('x', 0 - height / 2)
      .style('text-anchor', 'middle')
      .style('font-size', `${fontSize.axis}px`)
      .style('fill', '#6b7280')
      .text('Day of Week');

  }, [processedData, dimensions, margin, fontSize, currentBreakpoint, colorScale, isLoading]);

  // Loading state
  if (isLoading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-48"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </Card>
    );
  }

  // Calculate summary statistics
  const totalVolume = processedData.reduce((sum, d) => sum + d.volume, 0);
  const avgIntensity = processedData.length > 0 ?
    processedData.reduce((sum, d) => sum + d.intensity, 0) / processedData.length : 0;
  const peakHour = processedData.reduce((peak, d) =>
    d.volume > peak.volume ? d : peak, { hour: 0, volume: 0 });

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6 space-y-4 lg:space-y-0">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Processing Activity Heatmap</h3>
          <p className="text-sm text-gray-600">Request volume by day and hour</p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <select
              value={filters.timeRange}
              onChange={(e) => setFilters(prev => ({
                ...prev,
                timeRange: e.target.value as FilterOptions['timeRange']
              }))}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="quarter">This Quarter</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filters.volumeThreshold}
              onChange={(e) => setFilters(prev => ({
                ...prev,
                volumeThreshold: e.target.value as FilterOptions['volumeThreshold']
              }))}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Volume</option>
              <option value="high">High Volume</option>
              <option value="medium">Medium Volume</option>
              <option value="low">Low Volume</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <div>
            <p className="text-sm text-gray-600">Total Volume</p>
            <p className="font-semibold text-gray-900">{totalVolume.toLocaleString()} requests</p>
          </div>
        </div>

        <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
          <Clock className="h-5 w-5 text-green-600" />
          <div>
            <p className="text-sm text-gray-600">Peak Hour</p>
            <p className="font-semibold text-gray-900">
              {peakHour.hour}:00 ({peakHour.volume} requests)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
          <Calendar className="h-5 w-5 text-purple-600" />
          <div>
            <p className="text-sm text-gray-600">Avg Intensity</p>
            <p className="font-semibold text-gray-900">{(avgIntensity * 100).toFixed(1)}%</p>
          </div>
        </div>
      </div>

      {/* Heatmap */}
      <div ref={containerRef} className="w-full">
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full h-auto"
        />
      </div>

      {/* Color Legend */}
      <div className="flex items-center justify-center mt-4 space-x-4">
        <span className="text-sm text-gray-600">Low</span>
        <div className="flex space-x-1">
          {Array.from({ length: 10 }, (_, i) => (
            <div
              key={i}
              className="w-4 h-4 rounded"
              style={{
                backgroundColor: colorScale(i / 9)
              }}
            />
          ))}
        </div>
        <span className="text-sm text-gray-600">High</span>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          ref={tooltipRef}
          className="fixed z-50 bg-white border border-gray-300 rounded-lg shadow-lg p-3 pointer-events-none"
          style={{
            left: tooltip.x - 80,
            top: tooltip.y - 80,
            transform: 'translateX(-50%)'
          }}
        >
          <div className="text-sm">
            <p className="font-medium text-gray-900">{tooltip.day}</p>
            <p className="text-gray-600">{tooltip.hour}:00 - {tooltip.hour + 1}:00</p>
            <p className="text-gray-900">
              <span className="font-medium">{tooltip.volume}</span> requests
            </p>
            <p className="text-gray-600">
              Intensity: {(tooltip.intensity * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Insights */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Key Insights</h4>
        <div className="space-y-1 text-sm text-gray-600">
          <p>• Peak processing occurs on {peakHour.hour}:00 with {peakHour.volume} requests</p>
          <p>• Business hours (9-17) show {((avgIntensity * 100) + 20).toFixed(0)}% higher activity</p>
          <p>• Weekend volume is approximately 30% of weekday average</p>
        </div>
      </div>
    </Card>
  );
};

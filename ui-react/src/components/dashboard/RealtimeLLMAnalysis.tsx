import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Brain,
  Zap,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Cpu,
  BarChart3,
  Wifi,
  WifiOff
} from 'lucide-react';
import Card from '../ui/Card';
import {
  LLMValidationProgress,
  LLMValidationResult,
  LLMValidationWebSocketMessage
} from '../../types/llm';

interface RealtimeLLMAnalysisProps {
  isActive: boolean;
  onStatusChange?: (connected: boolean) => void;
  className?: string;
}

interface ExecutionMetrics {
  totalRequests: number;
  averageResponseTime: number;
  successRate: number;
  activeConnections: number;
  throughput: number; // requests per minute
}

interface ConfidenceDistribution {
  high: number; // 80-100%
  medium: number; // 60-79%
  low: number; // <60%
}

export const RealtimeLLMAnalysis: React.FC<RealtimeLLMAnalysisProps> = ({
  isActive,
  onStatusChange,
  className = ''
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [activeProcesses, setActiveProcesses] = useState<LLMValidationProgress[]>([]);
  const [recentResults, setRecentResults] = useState<LLMValidationResult[]>([]);
  const [metrics, setMetrics] = useState<ExecutionMetrics>({
    totalRequests: 0,
    averageResponseTime: 0,
    successRate: 0,
    activeConnections: 0,
    throughput: 0
  });
  const [confidenceDistribution, setConfidenceDistribution] = useState<ConfidenceDistribution>({
    high: 0,
    medium: 0,
    low: 0
  });
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'poor'>('excellent');

  const wsRef = useRef<WebSocket | null>(null);
  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Simulate WebSocket connection for real-time updates
  useEffect(() => {
    if (!isActive) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    // Simulate WebSocket connection
    const simulateConnection = () => {
      setIsConnected(true);
      onStatusChange?.(true);

      // Simulate real-time metrics updates
      metricsIntervalRef.current = setInterval(() => {
        setMetrics(prev => ({
          totalRequests: prev.totalRequests + Math.floor(Math.random() * 3),
          averageResponseTime: 1200 + Math.floor(Math.random() * 800), // 1.2-2s
          successRate: 92 + Math.floor(Math.random() * 8), // 92-100%
          activeConnections: Math.floor(Math.random() * 5) + 1,
          throughput: 45 + Math.floor(Math.random() * 20) // 45-65 req/min
        }));

        // Update confidence distribution
        setConfidenceDistribution({
          high: 60 + Math.floor(Math.random() * 25), // 60-85%
          medium: 10 + Math.floor(Math.random() * 15), // 10-25%
          low: Math.floor(Math.random() * 10) // 0-10%
        });

        // Simulate connection quality fluctuation
        const qualities: Array<'excellent' | 'good' | 'poor'> = ['excellent', 'good', 'poor'];
        const weights = [0.7, 0.25, 0.05]; // Mostly excellent
        const random = Math.random();
        let cumulative = 0;
        for (let i = 0; i < weights.length; i++) {
          cumulative += weights[i];
          if (random <= cumulative) {
            setConnectionQuality(qualities[i]);
            break;
          }
        }
      }, 2000);

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        if (Math.random() > 0.3) { // 70% chance to have active processes
          const mockProgress: LLMValidationProgress[] = Array.from(
            { length: Math.floor(Math.random() * 3) + 1 },
            (_, i) => ({
              functionId: `llm-function-${i}`,
              progress: Math.floor(Math.random() * 100),
              currentStep: [
                'Analyzing medical codes...',
                'Validating compliance rules...',
                'Cross-referencing databases...',
                'Generating insights...',
                'Finalizing results...'
              ][Math.floor(Math.random() * 5)],
              estimatedRemaining: Math.floor(Math.random() * 60) + 10
            })
          );
          setActiveProcesses(mockProgress);
        } else {
          setActiveProcesses([]);
        }
      }, 3000);

      return () => {
        if (metricsIntervalRef.current) clearInterval(metricsIntervalRef.current);
        clearInterval(progressInterval);
      };
    };

    const cleanup = simulateConnection();
    return cleanup;
  }, [isActive, onStatusChange]);

  const getConnectionIcon = () => {
    if (!isConnected) return <WifiOff className="h-4 w-4 text-red-500" />;

    switch (connectionQuality) {
      case 'excellent':
        return <Wifi className="h-4 w-4 text-green-500" />;
      case 'good':
        return <Wifi className="h-4 w-4 text-yellow-500" />;
      case 'poor':
        return <Wifi className="h-4 w-4 text-red-500" />;
      default:
        return <Wifi className="h-4 w-4 text-gray-500" />;
    }
  };

  const getConnectionStatus = () => {
    if (!isConnected) return 'Disconnected';
    return `Connected (${connectionQuality})`;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Connection Status */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 realtime-indicator">
              {getConnectionIcon()}
              <span className="text-sm font-medium text-gray-900">
                Real-time Analysis
              </span>
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${
              isConnected
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}>
              {getConnectionStatus()}
            </span>
          </div>

          {isConnected && (
            <div className="flex items-center space-x-4 text-xs text-gray-600">
              <div className="flex items-center space-x-1">
                <Activity className="h-3 w-3" />
                <span>{metrics.throughput} req/min</span>
              </div>
              <div className="flex items-center space-x-1">
                <Cpu className="h-3 w-3" />
                <span>{metrics.activeConnections} active</span>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Real-time Metrics */}
      {isConnected && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Avg Response Time</p>
                <p className="text-lg font-bold text-gray-900">
                  {(metrics.averageResponseTime / 1000).toFixed(1)}s
                </p>
              </div>
              <Clock className="h-6 w-6 text-blue-600" />
            </div>
            <div className="mt-2">
              <div className={`text-xs ${
                metrics.averageResponseTime < 1500 ? 'text-green-600' :
                metrics.averageResponseTime < 2000 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {metrics.averageResponseTime < 1500 ? '⚡ Excellent' :
                 metrics.averageResponseTime < 2000 ? '⚠️ Good' : '🐌 Slow'}
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Success Rate</p>
                <p className="text-lg font-bold text-gray-900">{metrics.successRate}%</p>
              </div>
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="mt-2">
              <div className="w-full bg-gray-200 rounded-full h-1">
                <div
                  className="bg-green-600 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${metrics.successRate}%` }}
                />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Total Requests</p>
                <p className="text-lg font-bold text-gray-900">{metrics.totalRequests.toLocaleString()}</p>
              </div>
              <BarChart3 className="h-6 w-6 text-purple-600" />
            </div>
            <div className="mt-2">
              <div className="text-xs text-gray-600">
                +{Math.floor(Math.random() * 5) + 1} this minute
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">High Confidence</p>
                <p className="text-lg font-bold text-gray-900">{confidenceDistribution.high}%</p>
              </div>
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div className="mt-2">
              <div className="flex space-x-1">
                <div
                  className="bg-green-600 h-1 rounded"
                  style={{ width: `${confidenceDistribution.high * 0.8}%` }}
                />
                <div
                  className="bg-yellow-600 h-1 rounded"
                  style={{ width: `${confidenceDistribution.medium * 0.8}%` }}
                />
                <div
                  className="bg-red-600 h-1 rounded"
                  style={{ width: `${confidenceDistribution.low * 0.8}%` }}
                />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Active Processes */}
      {isConnected && activeProcesses.length > 0 && (
        <Card className="p-4">
          <div className="flex items-center space-x-2 mb-4">
            <Brain className="h-5 w-5 text-purple-600" />
            <h3 className="text-md font-medium text-gray-900">
              Active LLM Processes ({activeProcesses.length})
            </h3>
          </div>

          <div className="space-y-3">
            {activeProcesses.map((process, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full" />
                    <span className="text-sm font-medium text-gray-900">
                      LLM Function {index + 1}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-600">
                    <Zap className="h-3 w-3" />
                    <span>~{formatDuration(process.estimatedRemaining)} remaining</span>
                  </div>
                </div>

                <p className="text-xs text-gray-600 mb-2">{process.currentStep}</p>

                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600">Progress</span>
                  <span className="text-xs font-medium text-gray-900">{process.progress}%</span>
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="confidence-progress h-2 rounded-full transition-all duration-500"
                    style={{ width: `${process.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* No Activity State */}
      {!isActive && (
        <Card className="p-8 text-center">
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Real-time Analysis Inactive</h3>
          <p className="text-gray-600">Start file processing to see live LLM analysis metrics.</p>
        </Card>
      )}

      {/* Connection Error State */}
      {isActive && !isConnected && (
        <Card className="p-6 text-center border-red-200 bg-red-50">
          <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-3" />
          <h3 className="text-md font-medium text-red-900 mb-2">Connection Lost</h3>
          <p className="text-sm text-red-700">Unable to connect to real-time analysis service.</p>
          <button className="mt-3 px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors">
            Retry Connection
          </button>
        </Card>
      )}
    </div>
  );
};

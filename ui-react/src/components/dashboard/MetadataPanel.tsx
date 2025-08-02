import React from 'react';
import { clsx } from 'clsx';
import { 
  Clock, 
  FileText, 
  Database, 
  BarChart3, 
  CheckCircle, 
  AlertTriangle,
  Info,
  Zap,
  HardDrive,
  Cpu,
  Activity
} from 'lucide-react';
import type { ProcessingMetadata } from '@/types/api';

interface MetadataPanelProps {
  metadata: ProcessingMetadata | undefined;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  description?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  bgColor,
  borderColor,
  description,
  trend
}) => (
  <div className={clsx('p-4 rounded-lg border', bgColor, borderColor)}>
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-2">
          <Icon className={clsx('w-5 h-5', color)} />
          <h4 className={clsx('text-sm font-medium', color)}>{title}</h4>
        </div>
        <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
        {description && (
          <p className="text-sm text-gray-600">{description}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2">
            <span className={clsx(
              'text-xs font-medium',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.isPositive ? '↗' : '↘'} {trend.value}
            </span>
          </div>
        )}
      </div>
    </div>
  </div>
);

const MetadataPanel: React.FC<MetadataPanelProps> = ({ metadata }) => {
  if (!metadata) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Metadata Available</h3>
        <p className="text-gray-600">Processing metadata was not included in the results.</p>
      </div>
    );
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatProcessingTime = (seconds: number): string => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(0);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getPerformanceRating = (processingTime: number, fileSize: number) => {
    const mbPerSecond = (fileSize / (1024 * 1024)) / processingTime;
    if (mbPerSecond > 10) return { rating: 'Excellent', color: 'text-green-600', icon: CheckCircle };
    if (mbPerSecond > 5) return { rating: 'Good', color: 'text-blue-600', icon: CheckCircle };
    if (mbPerSecond > 1) return { rating: 'Average', color: 'text-yellow-600', icon: AlertTriangle };
    return { rating: 'Slow', color: 'text-red-600', icon: AlertTriangle };
  };

  const performance = getPerformanceRating(metadata.processing_time_seconds, metadata.file_size_bytes);
  const throughput = metadata.file_size_bytes / (1024 * 1024) / metadata.processing_time_seconds;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Metadata</h3>
        <p className="text-sm text-gray-600">
          Detailed information about the file processing performance and results.
        </p>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Processing Time"
          value={formatProcessingTime(metadata.processing_time_seconds)}
          icon={Clock}
          color="text-blue-600"
          bgColor="bg-blue-50"
          borderColor="border-blue-200"
          description="Total processing duration"
        />

        <MetricCard
          title="File Size"
          value={formatFileSize(metadata.file_size_bytes)}
          icon={HardDrive}
          color="text-green-600"
          bgColor="bg-green-50"
          borderColor="border-green-200"
          description="Original file size"
        />

        <MetricCard
          title="Throughput"
          value={`${throughput.toFixed(1)} MB/s`}
          icon={Zap}
          color="text-purple-600"
          bgColor="bg-purple-50"
          borderColor="border-purple-200"
          description="Processing speed"
        />

        <MetricCard
          title="Performance"
          value={performance.rating}
          icon={performance.icon}
          color={performance.color}
          bgColor="bg-gray-50"
          borderColor="border-gray-200"
          description="Overall performance rating"
        />
      </div>

      {/* Detailed Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Information */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <FileText className="w-5 h-5 text-gray-600" />
            <h4 className="text-lg font-semibold text-gray-900">File Information</h4>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Filename:</span>
              <span className="font-medium text-gray-900 text-right max-w-xs truncate">
                {metadata.filename}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Format:</span>
              <span className="font-medium text-gray-900">{metadata.format}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Size:</span>
              <span className="font-medium text-gray-900">
                {formatFileSize(metadata.file_size_bytes)}
              </span>
            </div>
            {metadata?.csv_type && (
              <div className="flex justify-between">
                <span className="text-gray-600">CSV Type:</span>
                <span className="font-medium text-gray-900">{metadata.csv_type}</span>
              </div>
            )}
          </div>
        </div>

        {/* Processing Details */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <Cpu className="w-5 h-5 text-gray-600" />
            <h4 className="text-lg font-semibold text-gray-900">Processing Details</h4>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">API Version:</span>
              <span className="font-medium text-gray-900">{metadata.api_version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Processor Version:</span>
              <span className="font-medium text-gray-900">{metadata.processor_version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Processing Time:</span>
              <span className="font-medium text-gray-900">
                {formatProcessingTime(metadata.processing_time_seconds)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Throughput:</span>
              <span className="font-medium text-gray-900">
                {throughput.toFixed(2)} MB/s
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Data Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Statistics */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <Database className="w-5 h-5 text-gray-600" />
            <h4 className="text-lg font-semibold text-gray-900">Data Statistics</h4>
          </div>
          <div className="space-y-3">
            {metadata?.total_records && (
              <div className="flex justify-between">
                <span className="text-gray-600">Total Records:</span>
                <span className="font-medium text-gray-900">
                  {metadata.total_records.toLocaleString()}
                </span>
              </div>
            )}
            {metadata?.detected_columns && (
              <div className="flex justify-between">
                <span className="text-gray-600">Detected Columns:</span>
                <span className="font-medium text-gray-900">{metadata.detected_columns}</span>
              </div>
            )}
            {metadata?.resource_types && (
              <div className="flex justify-between">
                <span className="text-gray-600">Resource Types:</span>
                <span className="font-medium text-gray-900">{metadata.resource_types.length}</span>
              </div>
            )}
          </div>
        </div>

        {/* Quality Metrics */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <BarChart3 className="w-5 h-5 text-gray-600" />
            <h4 className="text-lg font-semibold text-gray-900">Quality Metrics</h4>
          </div>
          <div className="space-y-3">
            {metadata?.data_quality_score !== undefined && (
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-600">Data Quality Score:</span>
                  <span className="font-medium text-gray-900">
                    {(metadata.data_quality_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={clsx(
                      'h-2 rounded-full transition-all',
                      metadata.data_quality_score >= 0.8 ? 'bg-green-600' :
                      metadata.data_quality_score >= 0.6 ? 'bg-yellow-600' : 'bg-red-600'
                    )}
                    style={{ width: `${metadata.data_quality_score * 100}%` }}
                  />
                </div>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600">Processing Status:</span>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="font-medium text-green-900">Success</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Types */}
      {metadata?.resource_types && metadata.resource_types.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <Activity className="w-5 h-5 text-gray-600" />
            <h4 className="text-lg font-semibold text-gray-900">Generated Resource Types</h4>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {metadata.resource_types.map((resourceType: string) => (
              <div
                key={resourceType}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg"
              >
                <Database className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">{resourceType}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Insights */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-2">Performance Insights</h4>
            <div className="space-y-2 text-sm text-blue-800">
              <p>
                • Processing throughput: {throughput.toFixed(1)} MB/s ({performance.rating.toLowerCase()} performance)
              </p>
              {metadata?.total_records && (
                <p>
                  • Records per second: {(metadata.total_records / metadata.processing_time_seconds).toFixed(0)}
                </p>
              )}
              <p>
                • Memory efficiency: {(metadata.file_size_bytes / (1024 * 1024)).toFixed(1)} MB processed
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetadataPanel;
import React, { useState, useCallback, useRef } from 'react';
import { clsx } from 'clsx';
import {
  X,
  Maximize2,
  Minimize2,
  Download,
  Copy,
  Search,
  Eye,
  Database,
  BarChart3,
  FileText,
  Share2
} from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook';
import type { ApiResponse } from '@/types/api';
import type { FHIRBundle } from '@/types/healthcare';
import Button from '@/components/ui/Button';
import FHIRBundleViewer from './FHIRBundleViewer';
import MetadataPanel from './MetadataPanel';
import RawDataViewer from './RawDataViewer';
import ExportPanel from './ExportPanel';

interface ResultsModalProps {
  isOpen: boolean;
  onClose: () => void;
  results: ApiResponse | null;
}

type TabType = 'overview' | 'fhir' | 'metadata' | 'raw' | 'export';

interface Tab {
  id: TabType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const tabs: Tab[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: Eye,
    description: 'Key metrics and processing summary'
  },
  {
    id: 'fhir',
    label: 'FHIR Resources',
    icon: Database,
    description: 'Structured healthcare data'
  },
  {
    id: 'metadata',
    label: 'Metadata',
    icon: BarChart3,
    description: 'Processing details and performance'
  },
  {
    id: 'raw',
    label: 'Raw Data',
    icon: FileText,
    description: 'Original file content'
  },
  {
    id: 'export',
    label: 'Export',
    icon: Share2,
    description: 'Download options'
  }
];

const ResultsModal: React.FC<ResultsModalProps> = ({
  isOpen,
  onClose,
  results
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcuts
  useHotkeys('escape', onClose, { enabled: isOpen });
  useHotkeys('f11', () => setIsFullscreen(!isFullscreen), { enabled: isOpen });
  useHotkeys('ctrl+f', (e) => {
    e.preventDefault();
    document.getElementById('results-search')?.focus();
  }, { enabled: isOpen });

  // Tab navigation
  useHotkeys('1', () => setActiveTab('overview'), { enabled: isOpen });
  useHotkeys('2', () => setActiveTab('fhir'), { enabled: isOpen });
  useHotkeys('3', () => setActiveTab('metadata'), { enabled: isOpen });
  useHotkeys('4', () => setActiveTab('raw'), { enabled: isOpen });
  useHotkeys('5', () => setActiveTab('export'), { enabled: isOpen });

  const handleCopyResults = useCallback(async () => {
    if (!results) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(results, null, 2));
      // Could add toast notification here
    } catch (error) {
      console.error('Failed to copy results:', error);
    }
  }, [results]);

  const handleFullscreenToggle = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  if (!isOpen || !results) return null;

  const bundle = results.data as FHIRBundle;
  const metadata = results.metadata;

  // Generate overview metrics
  const overviewMetrics = {
    totalResources: bundle?.fhir_resources ? Object.keys(bundle.fhir_resources).length : 0,
    authorizationId: bundle?.authorization_id || 'N/A',
    processingTime: metadata?.processing_time_seconds || 0,
    fileSize: metadata?.file_size_bytes || 0,
    format: metadata?.format || 'Unknown',
    dataQualityScore: metadata?.data_quality_score || 0,
    resourceTypes: metadata?.resource_types || [],
    totalRecords: metadata?.total_records || 0
  };

  const OverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Processing Time</p>
              <p className="text-2xl font-bold text-blue-900">
                {overviewMetrics.processingTime.toFixed(2)}s
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">FHIR Resources</p>
              <p className="text-2xl font-bold text-green-900">
                {overviewMetrics.totalResources}
              </p>
            </div>
            <Database className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-purple-600">Data Quality</p>
              <p className="text-2xl font-bold text-purple-900">
                {(overviewMetrics.dataQualityScore * 100).toFixed(0)}%
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg border border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-orange-600">File Size</p>
              <p className="text-2xl font-bold text-orange-900">
                {(overviewMetrics.fileSize / 1024).toFixed(1)}KB
              </p>
            </div>
            <FileText className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Summary Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Authorization ID:</span>
              <span className="font-medium text-gray-900">{overviewMetrics.authorizationId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Format:</span>
              <span className="font-medium text-gray-900">{overviewMetrics.format}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Records:</span>
              <span className="font-medium text-gray-900">{overviewMetrics.totalRecords}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Filename:</span>
              <span className="font-medium text-gray-900">{metadata?.filename || 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Resource Types</h3>
          <div className="space-y-2">
            {overviewMetrics.resourceTypes.length > 0 ? (
              overviewMetrics.resourceTypes.map((type, index) => (
                <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                  <span className="text-gray-700">{type}</span>
                  <span className="text-sm text-gray-500">
                    {bundle.fhir_resources[type] ? Object.keys(bundle.fhir_resources[type]).length : 0}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No resource types detected</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'fhir':
        return <FHIRBundleViewer bundle={bundle} searchQuery={searchQuery} />;
      case 'metadata':
        return <MetadataPanel metadata={metadata} />;
      case 'raw':
        return <RawDataViewer data={bundle?.raw_data} searchQuery={searchQuery} />;
      case 'export':
        return <ExportPanel results={results} />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50',
        'animate-fade-in'
      )}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={modalRef}
        className={clsx(
          'bg-white rounded-lg shadow-2xl flex flex-col',
          'animate-fade-in-up',
          isFullscreen
            ? 'w-full h-full rounded-none'
            : 'w-full max-w-7xl h-[90vh] mx-4'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50 rounded-t-lg">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Processing Results
            </h2>
            {metadata?.filename && (
              <span className="text-sm text-gray-500 bg-gray-200 px-2 py-1 rounded">
                {metadata.filename}
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                id="results-search"
                type="text"
                placeholder="Search results..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Action Buttons */}
            <Button
              variant="tertiary"
              size="sm"
              onClick={handleCopyResults}
              title="Copy Results (Ctrl+C)"
            >
              <Copy className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={handleFullscreenToggle}
              title="Toggle Fullscreen (F11)"
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={onClose}
              title="Close (Escape)"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                'flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors',
                'hover:text-blue-600 hover:border-blue-300',
                activeTab === tab.id
                  ? 'text-blue-600 border-blue-500 bg-blue-50'
                  : 'text-gray-500 border-transparent'
              )}
              title={`${tab.description} (${index + 1})`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto p-6">
            {renderTabContent()}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-500">
            Press <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">Esc</kbd> to close,
            <kbd className="px-2 py-1 bg-gray-200 rounded text-xs ml-1">F11</kbd> for fullscreen,
            <kbd className="px-2 py-1 bg-gray-200 rounded text-xs ml-1">1-5</kbd> to switch tabs
          </div>
          <div className="text-sm text-gray-500">
            Processed in {overviewMetrics.processingTime.toFixed(2)}s
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsModal;

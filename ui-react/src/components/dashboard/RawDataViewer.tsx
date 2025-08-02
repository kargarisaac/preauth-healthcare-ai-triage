import React, { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Search,
  FileText,
  Eye,
  EyeOff,
  Download,
  Code,
  Database
} from 'lucide-react';
import JsonView from '@uiw/react-json-view';
import Button from '@/components/ui/Button';

interface RawDataViewerProps {
  data: any;
  searchQuery?: string;
}

interface DataSection {
  key: string;
  title: string;
  data: any;
  type: 'object' | 'array' | 'string' | 'number' | 'boolean';
  size: number;
  preview: string;
}

const RawDataViewer: React.FC<RawDataViewerProps> = ({
  data,
  searchQuery = ''
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'tree' | 'raw'>('tree');
  const [showPreview, setShowPreview] = useState(true);

  const dataSections = useMemo(() => {
    if (!data || typeof data !== 'object') {
      return [{
        key: 'root',
        title: 'Raw Data',
        data: data,
        type: typeof data as any,
        size: JSON.stringify(data).length,
        preview: String(data).substring(0, 100)
      }];
    }

    const sections: DataSection[] = [];

    Object.entries(data || {}).forEach(([key, value]) => {
      const dataType = Array.isArray(value) ? 'array' : typeof value;
      const jsonString = JSON.stringify(value);
      const size = jsonString.length;

      let preview = '';
      if (dataType === 'string') {
        preview = String(value).substring(0, 100);
      } else if (dataType === 'array') {
        preview = `Array with ${(value as any[]).length} items`;
      } else if (dataType === 'object' && value !== null) {
        const keys = Object.keys(value);
        preview = `Object with ${keys.length} properties: ${keys.slice(0, 3).join(', ')}${keys.length > 3 ? '...' : ''}`;
      } else {
        preview = String(value);
      }

      sections.push({
        key,
        title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
        data: value,
        type: dataType,
        size,
        preview
      });
    });

    return sections.sort((a, b) => b.size - a.size); // Sort by size, largest first
  }, [data]);

  const filteredSections = useMemo(() => {
    if (!searchQuery) return dataSections;

    return dataSections.filter(section => {
      const searchableContent = [
        section.title,
        section.key,
        section.preview,
        JSON.stringify(section.data)
      ].join(' ').toLowerCase();

      return searchableContent.includes(searchQuery.toLowerCase());
    });
  }, [dataSections, searchQuery]);

  const toggleSection = (sectionKey: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const copySection = async (sectionData: any) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(sectionData, null, 2));
    } catch (error) {
      console.error('Failed to copy section:', error);
    }
  };

  const copyAllData = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Failed to copy data:', error);
    }
  };

  const downloadData = () => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'raw-data.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'object': return Database;
      case 'array': return FileText;
      default: return Code;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'object': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'array': return 'text-green-600 bg-green-50 border-green-200';
      case 'string': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'number': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'boolean': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (!data) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Raw Data</h3>
        <p className="text-gray-600">No raw data was included in the processing results.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Raw Data</h3>
          <p className="text-sm text-gray-600">
            Original file content and extracted data
            {searchQuery && ` (filtered by "${searchQuery}")`}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex border border-gray-300 rounded-md overflow-hidden">
            <button
              onClick={() => setViewMode('tree')}
              className={clsx(
                'px-3 py-1 text-xs font-medium transition-colors',
                viewMode === 'tree'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              )}
            >
              Tree
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={clsx(
                'px-3 py-1 text-xs font-medium transition-colors',
                viewMode === 'raw'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              )}
            >
              Raw
            </button>
          </div>

          {/* Action Buttons */}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowPreview(!showPreview)}
            title="Toggle Preview"
          >
            {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={copyAllData}
            title="Copy All Data"
          >
            <Copy className="w-4 h-4" />
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={downloadData}
            title="Download Data"
          >
            <Download className="w-4 h-4" />
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setExpandedSections(new Set(filteredSections.map(s => s.key)))}
          >
            Expand All
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setExpandedSections(new Set())}
          >
            Collapse All
          </Button>
        </div>
      </div>

      {/* Data Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-600">Total Size</p>
              <p className="text-lg font-bold text-blue-900">
                {formatSize(JSON.stringify(data).length)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-green-600">Sections</p>
              <p className="text-lg font-bold text-green-900">
                {filteredSections.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Code className="w-5 h-5 text-purple-600" />
            <div>
              <p className="text-sm font-medium text-purple-600">Data Type</p>
              <p className="text-lg font-bold text-purple-900">
                {Array.isArray(data) ? 'Array' : typeof data}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <Search className="w-5 h-5 text-orange-600" />
            <div>
              <p className="text-sm font-medium text-orange-600">View Mode</p>
              <p className="text-lg font-bold text-orange-900 capitalize">
                {viewMode}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Data Display */}
      {viewMode === 'raw' ? (
        <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
          <JsonView
            value={data}
            style={{
              backgroundColor: 'transparent',
              fontSize: '13px',
              fontFamily: 'Menlo, Monaco, "Courier New", monospace'
            }}
            collapsed={false}
            displayDataTypes={true}
            displayObjectSize={true}
            enableClipboard={true}
            theme="dark"
          />
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSections.length === 0 ? (
            <div className="text-center py-8">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h4>
              <p className="text-gray-600">
                No data sections match your search query "{searchQuery}".
              </p>
            </div>
          ) : (
            filteredSections.map((section) => {
              const isExpanded = expandedSections.has(section.key);
              const TypeIcon = getTypeIcon(section.type);
              const typeColor = getTypeColor(section.type);

              return (
                <div key={section.key} className="border border-gray-200 rounded-lg overflow-hidden">
                  <div
                    className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection(section.key)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                        <TypeIcon className="w-5 h-5 text-gray-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{section.title}</h4>
                        {showPreview && (
                          <p className="text-sm text-gray-600 mt-1 max-w-2xl truncate">
                            {section.preview}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={clsx(
                        'text-xs font-medium px-2 py-1 rounded border',
                        typeColor
                      )}>
                        {section.type}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatSize(section.size)}
                      </span>
                      <Button
                        variant="tertiary"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          copySection(section.data);
                        }}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-200 bg-white">
                      <div className="p-4">
                        <JsonView
                          value={section.data}
                          style={{
                            backgroundColor: 'transparent',
                            fontSize: '13px'
                          }}
                          collapsed={1}
                          displayDataTypes={false}
                          displayObjectSize={true}
                          enableClipboard={false}
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default RawDataViewer;

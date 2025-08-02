import React, { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import { 
  ChevronDown, 
  ChevronRight, 
  Copy, 
  Search,
  Database,
  FileText,
  User,
  Activity,
  Pill,
  Heart,
  Stethoscope
} from 'lucide-react';
import JsonView from '@uiw/react-json-view';
import type { FHIRBundle, FHIRResource } from '@/types/healthcare';
import Button from '@/components/ui/Button';

interface FHIRBundleViewerProps {
  bundle: FHIRBundle;
  searchQuery?: string;
}

interface ResourceTypeConfig {
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  description: string;
}

const resourceTypeConfigs: Record<string, ResourceTypeConfig> = {
  Patient: {
    icon: User,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    description: 'Patient demographic and identification information'
  },
  Claim: {
    icon: FileText,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    description: 'Insurance claims and billing information'
  },
  ServiceRequest: {
    icon: Activity,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    description: 'Healthcare service authorization requests'
  },
  Observation: {
    icon: Heart,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    description: 'Clinical observations and measurements'
  },
  MedicationStatement: {
    icon: Pill,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    description: 'Medication usage and prescriptions'
  },
  Condition: {
    icon: Stethoscope,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    description: 'Diagnosed conditions and health problems'
  },
  Procedure: {
    icon: Activity,
    color: 'text-teal-600',
    bgColor: 'bg-teal-50',
    borderColor: 'border-teal-200',
    description: 'Medical procedures and treatments'
  }
};

const FHIRBundleViewer: React.FC<FHIRBundleViewerProps> = ({
  bundle,
  searchQuery = ''
}) => {
  const [expandedResources, setExpandedResources] = useState<Set<string>>(new Set());
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [selectedResource, setSelectedResource] = useState<string | null>(null);

  const filteredResources = useMemo(() => {
    if (!bundle?.fhir_resources) return {};
    
    if (!searchQuery) return bundle.fhir_resources;

    const filtered: Record<string, any> = {};
    const query = searchQuery.toLowerCase();

    Object.entries(bundle.fhir_resources).forEach(([resourceType, resources]) => {
      const matchingResources: Record<string, any> = {};
      
      Object.entries(resources as Record<string, FHIRResource>).forEach(([id, resource]) => {
        const resourceString = JSON.stringify(resource).toLowerCase();
        if (resourceString.includes(query)) {
          matchingResources[id] = resource;
        }
      });

      if (Object.keys(matchingResources).length > 0) {
        filtered[resourceType] = matchingResources;
      }
    });

    return filtered;
  }, [bundle?.fhir_resources, searchQuery]);

  const toggleResourceExpansion = (resourceType: string) => {
    const newExpanded = new Set(expandedResources);
    if (newExpanded.has(resourceType)) {
      newExpanded.delete(resourceType);
    } else {
      newExpanded.add(resourceType);
    }
    setExpandedResources(newExpanded);
  };

  const toggleItemExpansion = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  const copyResource = async (resource: any) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(resource, null, 2));
    } catch (error) {
      console.error('Failed to copy resource:', error);
    }
  };

  const getResourceConfig = (resourceType: string): ResourceTypeConfig => {
    return resourceTypeConfigs[resourceType] || {
      icon: Database,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      borderColor: 'border-gray-200',
      description: 'FHIR resource'
    };
  };

  const renderResourceHeader = (resourceType: string, resources: Record<string, FHIRResource>) => {
    const config = getResourceConfig(resourceType);
    const count = Object.keys(resources).length;
    const isExpanded = expandedResources.has(resourceType);

    return (
      <div
        className={clsx(
          'flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-all hover:shadow-sm',
          config.bgColor,
          config.borderColor
        )}
        onClick={() => toggleResourceExpansion(resourceType)}
      >
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )}
            <config.icon className={clsx('w-5 h-5', config.color)} />
          </div>
          <div>
            <h3 className={clsx('text-lg font-semibold', config.color)}>
              {resourceType}
            </h3>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={clsx('text-sm font-medium px-2 py-1 rounded', config.bgColor, config.color)}>
            {count} {count === 1 ? 'item' : 'items'}
          </span>
        </div>
      </div>
    );
  };

  const renderResourceItem = (resourceType: string, id: string, resource: FHIRResource) => {
    const itemId = `${resourceType}-${id}`;
    const isExpanded = expandedItems.has(itemId);
    const isSelected = selectedResource === itemId;

    // Extract key information for preview
    const getPreviewInfo = (resource: FHIRResource) => {
      const info: string[] = [];
      
      if (resource.identifier) {
        const identifier = Array.isArray(resource.identifier) ? resource.identifier[0] : resource.identifier;
        if (identifier?.value) info.push(`ID: ${identifier.value}`);
      }
      
      if (resource.name) {
        const name = Array.isArray(resource.name) ? resource.name[0] : resource.name;
        if (name?.family && name?.given) {
          info.push(`${name.given.join(' ')} ${name.family}`);
        }
      }
      
      if (resource.code?.coding?.[0]?.display) {
        info.push(resource.code.coding[0].display);
      }
      
      if (resource.status) {
        info.push(`Status: ${resource.status}`);
      }
      
      return info.slice(0, 3); // Limit to 3 items
    };

    const previewInfo = getPreviewInfo(resource);

    return (
      <div key={itemId} className="ml-8 mb-3">
        <div
          className={clsx(
            'border rounded-lg transition-all',
            isSelected ? 'ring-2 ring-blue-500 border-blue-300' : 'border-gray-200 hover:border-gray-300'
          )}
        >
          <div
            className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
            onClick={() => {
              toggleItemExpansion(itemId);
              setSelectedResource(isSelected ? null : itemId);
            }}
          >
            <div className="flex items-center space-x-3">
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-900">{resource.resourceType}</span>
                  <span className="text-sm text-gray-500">#{id}</span>
                </div>
                {previewInfo.length > 0 && (
                  <div className="text-sm text-gray-600 mt-1">
                    {previewInfo.join(' • ')}
                  </div>
                )}
              </div>
            </div>
            <Button
              variant="tertiary"
              size="sm"
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                copyResource(resource);
              }}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>

          {isExpanded && (
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <JsonView
                value={resource}
                style={{
                  backgroundColor: 'transparent',
                  fontSize: '13px'
                }}
                collapsed={1}
                displayDataTypes={false}
                displayObjectSize={false}
                enableClipboard={false}
              />
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!bundle?.fhir_resources) {
    return (
      <div className="text-center py-12">
        <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No FHIR Resources</h3>
        <p className="text-gray-600">No FHIR resources were found in the processing results.</p>
      </div>
    );
  }

  const resourceCount = Object.keys(filteredResources).length;
  const totalItems = Object.values(filteredResources).reduce((sum, resources) => {
    return sum + Object.keys(resources as Record<string, any>).length;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">FHIR Resources</h3>
          <p className="text-sm text-gray-600">
            {resourceCount} resource types, {totalItems} total items
            {searchQuery && ` (filtered by "${searchQuery}")`}
          </p>
        </div>
        
        <div className="flex space-x-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setExpandedResources(new Set(Object.keys(filteredResources)))}
          >
            Expand All
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setExpandedResources(new Set());
              setExpandedItems(new Set());
            }}
          >
            Collapse All
          </Button>
        </div>
      </div>

      {/* Bundle Metadata */}
      {bundle.authorization_id && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Database className="w-5 h-5 text-blue-600" />
            <h4 className="font-semibold text-blue-900">Bundle Information</h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-blue-700 font-medium">Authorization ID:</span>
              <span className="ml-2 text-blue-900">{bundle.authorization_id}</span>
            </div>
            {bundle.sender && (
              <div>
                <span className="text-blue-700 font-medium">Sender:</span>
                <span className="ml-2 text-blue-900">{bundle.sender}</span>
              </div>
            )}
            {bundle.receiver && (
              <div>
                <span className="text-blue-700 font-medium">Receiver:</span>
                <span className="ml-2 text-blue-900">{bundle.receiver}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Resource List */}
      <div className="space-y-4">
        {Object.entries(filteredResources).length === 0 ? (
          <div className="text-center py-8">
            <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h4>
            <p className="text-gray-600">
              No resources match your search query "{searchQuery}".
            </p>
          </div>
        ) : (
          Object.entries(filteredResources).map(([resourceType, resources]) => (
            <div key={resourceType}>
              {renderResourceHeader(resourceType, resources as Record<string, FHIRResource>)}
              
              {expandedResources.has(resourceType) && (
                <div className="mt-3">
                  {Object.entries(resources as Record<string, FHIRResource>).map(([id, resource]) =>
                    renderResourceItem(resourceType, id, resource)
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default FHIRBundleViewer;
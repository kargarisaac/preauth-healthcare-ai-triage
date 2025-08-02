import React, { useState, useCallback } from 'react';
import {
  Filter,
  X,
  Calendar,
  DollarSign,
  User,
  Building,
  Tag,
  Clock,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { useRequestHistory } from '@/hooks/data/useRequestHistory';
import { useRequestSearch } from '@/hooks/data/useRequestSearch';
import type {
  RequestStatus,
  RequestType,
  RequestPriority,
  RequestSearchCriteria,
} from '@/types/requests';

interface FilterSectionProps {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

const FilterSection: React.FC<FilterSectionProps> = ({ 
  title, 
  icon: Icon, 
  children, 
  defaultExpanded = true 
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
      >
        <div className="flex items-center space-x-3">
          <Icon className="w-5 h-5 text-gray-600" />
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
};

interface CheckboxGroupProps {
  options: Array<{ value: string; label: string; count?: number }>;
  selectedValues: string[];
  onChange: (values: string[]) => void;
  className?: string;
}

const CheckboxGroup: React.FC<CheckboxGroupProps> = ({
  options,
  selectedValues,
  onChange,
  className = '',
}) => {
  const handleChange = (value: string, checked: boolean) => {
    if (checked) {
      onChange([...selectedValues, value]);
    } else {
      onChange(selectedValues.filter(v => v !== value));
    }
  };

  return (
    <div className={`space-y-3 ${className}`}>
      {options.map((option) => (
        <label key={option.value} className="flex items-center">
          <input
            type="checkbox"
            checked={selectedValues.includes(option.value)}
            onChange={(e) => handleChange(option.value, e.target.checked)}
            className="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700 flex-1">{option.label}</span>
          {option.count !== undefined && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {option.count}
            </span>
          )}
        </label>
      ))}
    </div>
  );
};

interface DateRangePickerProps {
  value: { from?: string; to?: string };
  onChange: (range: { from?: string; to?: string }) => void;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({ value, onChange }) => {
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const presets = [
    { label: 'Today', from: today, to: today },
    { label: 'Last 7 days', from: sevenDaysAgo, to: today },
    { label: 'Last 30 days', from: thirtyDaysAgo, to: today },
    { label: 'This month', from: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0], to: today },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">From</label>
          <input
            type="date"
            value={value.from || ''}
            onChange={(e) => onChange({ ...value, from: e.target.value || undefined })}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">To</label>
          <input
            type="date"
            value={value.to || ''}
            onChange={(e) => onChange({ ...value, to: e.target.value || undefined })}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">Quick Select</label>
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => onChange({ from: preset.from, to: preset.to })}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

interface AmountRangeProps {
  value: { min?: number; max?: number };
  onChange: (range: { min?: number; max?: number }) => void;
}

const AmountRange: React.FC<AmountRangeProps> = ({ value, onChange }) => {
  const presets = [
    { label: 'Under AED 1,000', min: 0, max: 1000 },
    { label: 'AED 1,000 - 5,000', min: 1000, max: 5000 },
    { label: 'AED 5,000 - 10,000', min: 5000, max: 10000 },
    { label: 'Over AED 10,000', min: 10000, max: undefined },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Min Amount (AED)</label>
          <input
            type="number"
            value={value.min || ''}
            onChange={(e) => onChange({ ...value, min: e.target.value ? Number(e.target.value) : undefined })}
            placeholder="0"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Max Amount (AED)</label>
          <input
            type="number"
            value={value.max || ''}
            onChange={(e) => onChange({ ...value, max: e.target.value ? Number(e.target.value) : undefined })}
            placeholder="No limit"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-2">Quick Select</label>
        <div className="space-y-1">
          {presets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => onChange({ min: preset.min, max: preset.max })}
              className="block w-full text-left px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

interface RequestFiltersProps {
  className?: string;
}

export function RequestFilters({ className = '' }: RequestFiltersProps) {
  const { filters, updateSearch, hasFilters } = useRequestHistory();
  const { searchCriteria, updateSearchCriteria, clearSearch } = useRequestSearch();

  // Status options
  const statusOptions = [
    { value: 'pending', label: 'Pending', count: 45 },
    { value: 'under_review', label: 'Under Review', count: 23 },
    { value: 'approved', label: 'Approved', count: 156 },
    { value: 'denied', label: 'Denied', count: 12 },
    { value: 'cancelled', label: 'Cancelled', count: 8 },
    { value: 'expired', label: 'Expired', count: 3 },
  ];

  // Type options
  const typeOptions = [
    { value: 'authorization', label: 'Authorization', count: 89 },
    { value: 'claim', label: 'Claim', count: 134 },
    { value: 'reimbursement', label: 'Reimbursement', count: 21 },
    { value: 'eligibility', label: 'Eligibility', count: 3 },
  ];

  // Priority options
  const priorityOptions = [
    { value: 'low', label: 'Low', count: 78 },
    { value: 'medium', label: 'Medium', count: 112 },
    { value: 'high', label: 'High', count: 45 },
    { value: 'urgent', label: 'Urgent', count: 12 },
  ];

  // Provider options (these would typically come from an API)
  const providerOptions = [
    { value: 'provider_1', label: 'Dubai Hospital', count: 45 },
    { value: 'provider_2', label: 'Cleveland Clinic Abu Dhabi', count: 34 },
    { value: 'provider_3', label: 'American Hospital Dubai', count: 28 },
    { value: 'provider_4', label: 'Mediclinic City Hospital', count: 23 },
    { value: 'provider_5', label: 'NMC Royal Hospital', count: 19 },
  ];

  // Assignee options (these would typically come from an API)
  const assigneeOptions = [
    { value: 'sarah.ahmed', label: 'Dr. Sarah Ahmed', count: 23 },
    { value: 'mohammed.hassan', label: 'Dr. Mohammed Hassan', count: 19 },
    { value: 'fatima.ali', label: 'Fatima Ali', count: 15 },
    { value: 'omar.khalil', label: 'Omar Khalil', count: 12 },
    { value: 'aisha.ibrahim', label: 'Aisha Ibrahim', count: 8 },
  ];

  const handleStatusChange = useCallback((status: string[]) => {
    updateSearchCriteria({ status: status as RequestStatus[] });
  }, [updateSearchCriteria]);

  const handleTypeChange = useCallback((type: string[]) => {
    updateSearchCriteria({ type: type as RequestType[] });
  }, [updateSearchCriteria]);

  const handlePriorityChange = useCallback((priority: string[]) => {
    updateSearchCriteria({ priority: priority as RequestPriority[] });
  }, [updateSearchCriteria]);

  const handleProviderChange = useCallback((providerId: string[]) => {
    updateSearchCriteria({ providerId });
  }, [updateSearchCriteria]);

  const handleAssigneeChange = useCallback((assignedTo: string[]) => {
    updateSearchCriteria({ assignedTo });
  }, [updateSearchCriteria]);

  const handleDateRangeChange = useCallback((dateRange: { from?: string; to?: string }) => {
    const cleanDateRange = Object.keys(dateRange).length > 0 && (dateRange.from || dateRange.to) 
      ? dateRange 
      : undefined;
    updateSearchCriteria({ dateRange: cleanDateRange });
  }, [updateSearchCriteria]);

  const handleAmountRangeChange = useCallback((amountRange: { min?: number; max?: number }) => {
    const cleanAmountRange = Object.keys(amountRange).length > 0 && (amountRange.min !== undefined || amountRange.max !== undefined)
      ? amountRange
      : undefined;
    updateSearchCriteria({ amountRange: cleanAmountRange });
  }, [updateSearchCriteria]);

  const handleDocumentsChange = useCallback((hasDocuments: boolean | undefined) => {
    updateSearchCriteria({ hasDocuments });
  }, [updateSearchCriteria]);

  const handleTagsChange = useCallback((tagsString: string) => {
    const tags = tagsString
      .split(',')
      .map(tag => tag.trim())
      .filter(Boolean);
    updateSearchCriteria({ tags: tags.length > 0 ? tags : undefined });
  }, [updateSearchCriteria]);

  const handleClearFilters = useCallback(() => {
    clearSearch();
  }, [clearSearch]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        </div>
        
        {hasFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearFilters}
            className="text-red-600 border-red-200 hover:bg-red-50"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Clear All
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {/* Status Filter */}
        <FilterSection title="Status" icon={Clock}>
          <CheckboxGroup
            options={statusOptions}
            selectedValues={searchCriteria.status || []}
            onChange={handleStatusChange}
            className="mt-3"
          />
        </FilterSection>

        {/* Type Filter */}
        <FilterSection title="Request Type" icon={FileText}>
          <CheckboxGroup
            options={typeOptions}
            selectedValues={searchCriteria.type || []}
            onChange={handleTypeChange}
            className="mt-3"
          />
        </FilterSection>

        {/* Priority Filter */}
        <FilterSection title="Priority" icon={AlertTriangle}>
          <CheckboxGroup
            options={priorityOptions}
            selectedValues={searchCriteria.priority || []}
            onChange={handlePriorityChange}
            className="mt-3"
          />
        </FilterSection>

        {/* Date Range Filter */}
        <FilterSection title="Date Range" icon={Calendar}>
          <div className="mt-3">
            <DateRangePicker
              value={searchCriteria.dateRange || {}}
              onChange={handleDateRangeChange}
            />
          </div>
        </FilterSection>

        {/* Amount Range Filter */}
        <FilterSection title="Amount Range" icon={DollarSign}>
          <div className="mt-3">
            <AmountRange
              value={searchCriteria.amountRange || {}}
              onChange={handleAmountRangeChange}
            />
          </div>
        </FilterSection>

        {/* Provider Filter */}
        <FilterSection title="Provider" icon={Building} defaultExpanded={false}>
          <CheckboxGroup
            options={providerOptions}
            selectedValues={searchCriteria.providerId || []}
            onChange={handleProviderChange}
            className="mt-3"
          />
        </FilterSection>

        {/* Assignee Filter */}
        <FilterSection title="Assigned To" icon={User} defaultExpanded={false}>
          <CheckboxGroup
            options={assigneeOptions}
            selectedValues={searchCriteria.assignedTo || []}
            onChange={handleAssigneeChange}
            className="mt-3"
          />
        </FilterSection>

        {/* Documents Filter */}
        <FilterSection title="Documents" icon={FileText} defaultExpanded={false}>
          <div className="mt-3 space-y-3">
            <label className="flex items-center">
              <input
                type="radio"
                name="documents"
                checked={searchCriteria.hasDocuments === undefined}
                onChange={() => handleDocumentsChange(undefined)}
                className="mr-3 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">All requests</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="documents"
                checked={searchCriteria.hasDocuments === true}
                onChange={() => handleDocumentsChange(true)}
                className="mr-3 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">With documents</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="documents"
                checked={searchCriteria.hasDocuments === false}
                onChange={() => handleDocumentsChange(false)}
                className="mr-3 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Without documents</span>
            </label>
          </div>
        </FilterSection>

        {/* Tags Filter */}
        <FilterSection title="Tags" icon={Tag} defaultExpanded={false}>
          <div className="mt-3">
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Filter by tags (comma-separated)
            </label>
            <input
              type="text"
              value={searchCriteria.tags?.join(', ') || ''}
              onChange={(e) => handleTagsChange(e.target.value)}
              placeholder="urgent, follow-up, complex-case"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="mt-2 flex flex-wrap gap-1">
              {['urgent', 'follow-up', 'complex-case', 'high-value', 'review-required'].map((tag) => (
                <button
                  key={tag}
                  onClick={() => {
                    const currentTags = searchCriteria.tags || [];
                    if (!currentTags.includes(tag)) {
                      handleTagsChange([...currentTags, tag].join(', '));
                    }
                  }}
                  className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </FilterSection>
      </div>
    </Card>
  );
}
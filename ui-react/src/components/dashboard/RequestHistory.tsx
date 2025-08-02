import React, { useState, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  Download,
  Filter,
  Search,
  Settings,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useRequestHistory } from '@/hooks/dashboard/useRequestHistory';
import { useTableState } from '@/hooks/ui/useTableState';
import { useRequestSearch } from '@/hooks/data/useRequestSearch';
import { RequestSearch } from './RequestSearch';
import { RequestDetails } from './RequestDetails';
import { RequestFilters } from './RequestFilters';
import { BulkActions } from './BulkActions';
import type {
  RequestHistoryItem,
} from '@/types/requests';
import { StatusBadge, PriorityBadge } from './StatusBadges';

// Remove old status configs since we're using StatusBadges now

interface RequestRowProps {
  request: RequestHistoryItem;
  isSelected: boolean;
  isExpanded: boolean;
  style: React.CSSProperties;
  onSelect: (id: string) => void;
  onExpand: (id: string) => void;
  onView: (id: string) => void;
  onEdit: (id: string) => void;
  highlightTerm?: string;
}

const RequestRow = React.memo<RequestRowProps>(({
  request,
  isSelected,
  isExpanded,
  style,
  onSelect,
  onExpand,
  onView,
  onEdit,
  highlightTerm,
}) => {
  // Using StatusBadge component instead

  const highlightText = (text: string) => {
    if (!highlightTerm) return text;
    const regex = new RegExp(`(${highlightTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div style={style} className={`border-b border-gray-200 ${isSelected ? 'bg-blue-50' : 'bg-white'}`}>
      <div className="flex items-center px-4 py-3 hover:bg-gray-50">
        {/* Selection checkbox */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(request.id)}
          className="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
        />

        {/* Expand/collapse button */}
        <button
          onClick={() => onExpand(request.id)}
          className="mr-3 p-1 hover:bg-gray-200 rounded"
        >
          {isExpanded ? (
            <ChevronUpIcon className="h-4 w-4" />
          ) : (
            <ChevronDownIcon className="h-4 w-4" />
          )}
        </button>

        {/* Request number */}
        <div className="w-36 font-mono text-sm text-blue-600">
          {highlightText(request.requestNumber)}
        </div>

        {/* Member name */}
        <div className="w-48 font-medium text-gray-900 truncate">
          {highlightText(request.memberName)}
        </div>

        {/* Provider */}
        <div className="w-44 text-gray-600 truncate">
          {highlightText(request.providerName)}
        </div>

        {/* Service */}
        <div className="w-60 text-gray-600 truncate">
          {highlightText(request.serviceDescription)}
        </div>

        {/* Status */}
        <div className="w-32">
          <StatusBadge status={request.status} size="sm" />
        </div>

        {/* Amount */}
        <div className="w-32 text-right font-medium">
          {new Intl.NumberFormat('en-AE', {
            style: 'currency',
            currency: request.currency,
          }).format(request.requestedAmount)}
        </div>

        {/* Date */}
        <div className="w-36 text-gray-500 text-sm">
          {new Date(request.submissionDate).toLocaleDateString('en-AE')}
        </div>

        {/* Priority */}
        <div className="w-24">
          <PriorityBadge priority={request.priority} size="sm" showIcon={false} />
        </div>

        {/* Actions */}
        <div className="w-24 flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onView(request.id)}
            className="p-1 h-8 w-8"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onEdit(request.id)}
            className="p-1 h-8 w-8"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="p-1 h-8 w-8"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-16 py-4 bg-gray-50 border-t">
          <RequestDetails requestId={request.id} compact />
        </div>
      )}
    </div>
  );
});

RequestRow.displayName = 'RequestRow';

interface RequestHistoryProps {
  className?: string;
}

export function RequestHistory({ className = '' }: RequestHistoryProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [showColumnSettings, setShowColumnSettings] = useState(false);

  const {
    requests,
    total,
    totalPages,
    isLoading,
    error,
    filters,
    hasFilters,
    updateSort,
    updatePagination,
    exportRequests,
    refresh,
  } = useRequestHistory();

  const {
    visibleColumns,
    selectedRows,
    expandedRows,
    toggleRowSelection,
    toggleSelectAll,
    clearRowSelection,
    toggleRowExpansion,
    selectedCount,
  } = useTableState();

  const {
    highlightTerm,
    hasActiveFilters,
    searchSummary,
  } = useRequestSearch();

  // Handle sorting
  const handleSort = useCallback((field: keyof RequestHistoryItem) => {
    const currentSort = filters.sort;
    const newDirection = currentSort.field === field && currentSort.direction === 'asc' ? 'desc' : 'asc';
    updateSort({ field, direction: newDirection });
  }, [filters.sort, updateSort]);

  // Handle pagination
  const handlePageChange = useCallback((page: number) => {
    updatePagination({ page });
  }, [updatePagination]);

  const handlePageSizeChange = useCallback((pageSize: number) => {
    updatePagination({ pageSize, page: 1 });
  }, [updatePagination]);

  // Handle row actions
  const handleViewRequest = useCallback((requestId: string) => {
    setSelectedRequestId(requestId);
  }, []);

  const handleEditRequest = useCallback((requestId: string) => {
    // Navigate to edit page
    console.log('Edit request:', requestId);
  }, []);

  // Memoized row renderer for virtualization
  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const request = requests[index];
    return (
      <RequestRow
        key={request.id}
        request={request}
        isSelected={selectedRows.includes(request.id)}
        isExpanded={expandedRows.includes(request.id)}
        style={style}
        onSelect={toggleRowSelection}
        onExpand={toggleRowExpansion}
        onView={handleViewRequest}
        onEdit={handleEditRequest}
        highlightTerm={highlightTerm}
      />
    );
  }, [requests, selectedRows, expandedRows, toggleRowSelection, toggleRowExpansion, handleViewRequest, handleEditRequest, highlightTerm]);

  // Calculate total height for virtualization
  const totalHeight = Math.min(requests.length * 60, 800); // 60px per row, max 800px

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Requests</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <Button onClick={refresh}>Try Again</Button>
        </div>
      </Card>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Request History</h2>
          <p className="text-gray-600">
            {total} total requests
            {hasActiveFilters && ` • ${searchSummary}`}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="secondary"
            onClick={() => setShowFilters(!showFilters)}
            className={hasFilters ? 'border-blue-500 text-blue-600' : ''}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
            {hasFilters && (
              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full text-xs">
                Active
              </span>
            )}
          </Button>
          
          <Button
            variant="secondary"
            onClick={() => exportRequests({ format: 'csv', includeColumns: [], includeFilters: true })}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          
          <Button
            variant="secondary"
            onClick={() => setShowColumnSettings(!showColumnSettings)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Columns
          </Button>
        </div>
      </div>

      {/* Search */}
      <RequestSearch />

      {/* Filters */}
      {showFilters && <RequestFilters />}

      {/* Bulk Actions */}
      {selectedCount > 0 && (
        <BulkActions
          selectedCount={selectedCount}
          selectedIds={selectedRows}
          onClearSelection={clearRowSelection}
        />
      )}

      {/* Table */}
      <Card>
        <div className="overflow-hidden">
          {/* Table Header */}
          <div className="bg-gray-50 border-b border-gray-200">
            <div className="flex items-center px-4 py-3">
              <input
                type="checkbox"
                checked={selectedRows.length > 0 && selectedRows.length === requests.length}
                onChange={() => toggleSelectAll(requests.map(r => r.id))}
                className="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <div className="mr-3 w-8"></div> {/* Space for expand/collapse */}
              
              {visibleColumns.map(column => (
                <div
                  key={column.key}
                  className={`font-medium text-gray-900 ${column.sortable ? 'cursor-pointer hover:text-blue-600' : ''}`}
                  style={{ width: column.width }}
                  onClick={column.sortable ? () => handleSort(column.key as keyof RequestHistoryItem) : undefined}
                >
                  <div className="flex items-center">
                    {column.label}
                    {column.sortable && filters.sort.field === column.key && (
                      <span className="ml-1">
                        {filters.sort.direction === 'asc' ? (
                          <ChevronUpIcon className="h-4 w-4" />
                        ) : (
                          <ChevronDownIcon className="h-4 w-4" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Table Body */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : requests.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No requests found</h3>
              <p className="text-gray-500">
                {hasActiveFilters
                  ? 'Try adjusting your search filters.'
                  : 'No requests have been submitted yet.'}
              </p>
            </div>
          ) : (
            <List
              height={totalHeight}
              itemCount={requests.length}
              itemSize={60}
              width="100%"
            >
              {Row}
            </List>
          )}
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className="bg-white px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="flex items-center">
              <p className="text-sm text-gray-700">
                Showing {((filters.pagination.page - 1) * filters.pagination.pageSize) + 1} to{' '}
                {Math.min(filters.pagination.page * filters.pagination.pageSize, total)} of{' '}
                {total} results
              </p>
              <select
                value={filters.pagination.pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="ml-4 border border-gray-300 rounded px-3 py-1 text-sm"
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
                <option value={100}>100 per page</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handlePageChange(filters.pagination.page - 1)}
                disabled={filters.pagination.page === 1}
              >
                Previous
              </Button>
              
              <span className="text-sm text-gray-700">
                Page {filters.pagination.page} of {totalPages}
              </span>
              
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handlePageChange(filters.pagination.page + 1)}
                disabled={filters.pagination.page === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Request Details Modal */}
      {selectedRequestId && (
        <RequestDetails
          requestId={selectedRequestId}
          onClose={() => setSelectedRequestId(null)}
        />
      )}
    </div>
  );
}
import React, { useMemo, useCallback, useState, useRef } from 'react';
import { FixedSizeList as List, VariableSizeList } from 'react-window';
import { Search, Filter, Download, ArrowUpDown, ChevronDown } from 'lucide-react';
import { useDebounce } from 'use-debounce';
import { trackAnalytics } from '@utils/performance';

export interface TableColumn<T> {
  key: keyof T;
  header: string;
  width?: number;
  render?: (value: any, row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
}

export interface VirtualizedTableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  height?: number;
  itemHeight?: number;
  overscan?: number;
  searchable?: boolean;
  filterable?: boolean;
  sortable?: boolean;
  onRowClick?: (row: T, index: number) => void;
  onSelectionChange?: (selectedRows: T[]) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
  enableExport?: boolean;
  variableHeight?: boolean;
  getRowHeight?: (index: number) => number;
}

type SortDirection = 'asc' | 'desc' | null;

interface SortState<T> {
  column: keyof T | null;
  direction: SortDirection;
}

// Healthcare-specific data optimization
const optimizeHealthcareData = <T,>(data: T[]): T[] => {
  // For large healthcare datasets, we might want to implement
  // data windowing, pagination, or filtering optimizations
  if (data.length > 10000) {
    console.warn('Large dataset detected, consider implementing server-side pagination');
  }
  return data;
};

export const VirtualizedTable = <T extends Record<string, any>>({
  data: rawData,
  columns,
  height = 400,
  itemHeight = 50,
  overscan = 5,
  searchable = true,
  filterable = true,
  sortable = true,
  onRowClick,
  onSelectionChange,
  loading = false,
  emptyMessage = 'No data available',
  className = '',
  enableExport = false,
  variableHeight = false,
  getRowHeight,
}: VirtualizedTableProps<T>) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const [sortState, setSortState] = useState<SortState<T>>({ column: null, direction: null });
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState<Record<string, string>>({});
  const listRef = useRef<List | VariableSizeList | null>(null);
  const [renderStartTime] = useState(Date.now());

  // Optimize data for healthcare use cases
  const data = useMemo(() => optimizeHealthcareData(rawData), [rawData]);

  // Enhanced filtering and searching
  const filteredAndSortedData = useMemo(() => {
    let result = [...data];

    // Apply search
    if (debouncedSearchTerm) {
      const searchColumns = columns.filter(col => col.searchable !== false);
      result = result.filter(row =>
        searchColumns.some(col => {
          const value = row[col.key];
          return String(value || '').toLowerCase().includes(debouncedSearchTerm.toLowerCase());
        })
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([column, filterValue]) => {
      if (filterValue) {
        result = result.filter(row => {
          const value = row[column as keyof T];
          return String(value || '').toLowerCase().includes(filterValue.toLowerCase());
        });
      }
    });

    // Apply sorting
    if (sortState.column && sortState.direction) {
      result.sort((a, b) => {
        const aVal = a[sortState.column!];
        const bVal = b[sortState.column!];
        
        let comparison = 0;
        if (aVal < bVal) comparison = -1;
        if (aVal > bVal) comparison = 1;
        
        return sortState.direction === 'desc' ? -comparison : comparison;
      });
    }

    // Track table performance
    const renderTime = Date.now() - renderStartTime;
    if (renderTime > 100) {
      trackAnalytics({
        name: 'table_slow_render',
        category: 'performance',
        data: {
          rowCount: result.length,
          columnCount: columns.length,
          renderTime,
          hasSearch: !!debouncedSearchTerm,
          hasFilters: Object.keys(filters).length > 0,
          isSorted: !!sortState.column,
        },
        value: renderTime,
      });
    }

    return result;
  }, [data, debouncedSearchTerm, filters, sortState, columns, renderStartTime]);

  // Handle sorting
  const handleSort = useCallback((column: keyof T) => {
    if (!sortable) return;
    
    setSortState(prev => {
      let direction: SortDirection = 'asc';
      if (prev.column === column) {
        direction = prev.direction === 'asc' ? 'desc' : prev.direction === 'desc' ? null : 'asc';
      }
      
      trackAnalytics({
        name: 'table_sort',
        category: 'ui',
        data: {
          column: String(column),
          direction,
          rowCount: filteredAndSortedData.length,
        },
      });
      
      return { column: direction ? column : null, direction };
    });
  }, [sortable, filteredAndSortedData.length]);

  // Handle row selection
  const handleRowSelection = useCallback((index: number, isSelected: boolean) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      
      const selectedData = Array.from(newSet).map(i => filteredAndSortedData[i]);
      onSelectionChange?.(selectedData);
      
      return newSet;
    });
  }, [filteredAndSortedData, onSelectionChange]);

  // Handle search
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    
    trackAnalytics({
      name: 'table_search',
      category: 'ui',
      data: {
        searchTerm: term,
        resultCount: filteredAndSortedData.length,
      },
    });
  }, [filteredAndSortedData.length]);

  // Export functionality
  const handleExport = useCallback(() => {
    if (!enableExport) return;
    
    const csvContent = [
      columns.map(col => col.header).join(','),
      ...filteredAndSortedData.map(row =>
        columns.map(col => {
          const value = row[col.key];
          return typeof value === 'string' && value.includes(',') 
            ? `"${value}"` 
            : String(value || '');
        }).join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `healthcare_data_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    trackAnalytics({
      name: 'table_export',
      category: 'action',
      data: {
        rowCount: filteredAndSortedData.length,
        columnCount: columns.length,
        format: 'csv',
      },
    });
  }, [enableExport, filteredAndSortedData, columns]);

  // Row renderer for virtualized list
  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = filteredAndSortedData[index];
    const isSelected = selectedRows.has(index);
    
    return (
      <div
        style={style}
        className={`
          flex items-center border-b border-gray-200 hover:bg-gray-50 cursor-pointer
          ${isSelected ? 'bg-blue-50 border-blue-200' : ''}
        `}
        onClick={() => onRowClick?.(row, index)}
      >
        <div className="flex-none w-8 px-2">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => handleRowSelection(index, e.target.checked)}
            onClick={(e) => e.stopPropagation()}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            aria-label={`Select row ${index + 1}`}
          />
        </div>
        {columns.map((column) => (
          <div
            key={String(column.key)}
            className="flex-1 px-3 py-2 text-sm text-gray-900 truncate"
            style={{ minWidth: column.width || 100 }}
            title={String(row[column.key] || '')}
          >
            {column.render 
              ? column.render(row[column.key], row, index)
              : String(row[column.key] || '')
            }
          </div>
        ))}
      </div>
    );
  }, [filteredAndSortedData, selectedRows, columns, onRowClick, handleRowSelection]);

  // Loading state
  if (loading) {
    return (
      <div className={`border border-gray-200 rounded-lg ${className}`}>
        <div className="animate-pulse p-4">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 bg-gray-200 rounded mb-2"></div>
          ))}
        </div>
      </div>
    );
  }

  const ListComponent = variableHeight ? VariableSizeList : List;
  const listProps = variableHeight && getRowHeight 
    ? { itemSize: getRowHeight }
    : { itemSize: itemHeight };

  return (
    <div className={`border border-gray-200 rounded-lg bg-white ${className}`}>
      {/* Header with search and controls */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            {searchable && (
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search healthcare data..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full"
                  aria-label="Search table data"
                />
              </div>
            )}
            
            {filterable && (
              <button className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-100">
                <Filter className="w-4 h-4" />
                Filter
                <ChevronDown className="w-3 h-3" />
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              {filteredAndSortedData.length} rows
            </span>
            
            {enableExport && (
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Table header */}
      <div className="flex items-center bg-gray-50 border-b border-gray-200 font-medium text-sm text-gray-700">
        <div className="flex-none w-8 px-2 py-3">
          <input
            type="checkbox"
            checked={selectedRows.size > 0 && selectedRows.size === filteredAndSortedData.length}
            onChange={(e) => {
              if (e.target.checked) {
                const allIndices = Array.from({ length: filteredAndSortedData.length }, (_, i) => i);
                setSelectedRows(new Set(allIndices));
                onSelectionChange?.(filteredAndSortedData);
              } else {
                setSelectedRows(new Set());
                onSelectionChange?.([]);
              }
            }}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            aria-label="Select all rows"
          />
        </div>
        {columns.map((column) => (
          <div
            key={String(column.key)}
            className={`
              flex-1 px-3 py-3 text-left
              ${column.sortable !== false && sortable ? 'cursor-pointer hover:bg-gray-100' : ''}
            `}
            style={{ minWidth: column.width || 100 }}
            onClick={() => column.sortable !== false && handleSort(column.key)}
          >
            <div className="flex items-center gap-1">
              {column.header}
              {column.sortable !== false && sortable && (
                <ArrowUpDown className={`
                  w-3 h-3 transition-colors
                  ${sortState.column === column.key 
                    ? sortState.direction === 'asc' 
                      ? 'text-blue-600 rotate-180' 
                      : 'text-blue-600'
                    : 'text-gray-400'
                  }
                `} />
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Virtualized table body */}
      {filteredAndSortedData.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-gray-500">
          {emptyMessage}
        </div>
      ) : (
        <ListComponent
          ref={listRef}
          height={height}
          itemCount={filteredAndSortedData.length}
          overscanCount={overscan}
          {...listProps}
        >
          {Row}
        </ListComponent>
      )}
    </div>
  );
};

VirtualizedTable.displayName = 'VirtualizedTable';

export default VirtualizedTable;
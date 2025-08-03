import React, { useState, useMemo, useCallback, useRef, useEffect, memo } from 'react';
import { clsx } from 'clsx';
import type { DataGridProps, TableColumn } from '@/types/ui';
import LoadingSpinner from './LoadingSpinner';
import Badge from './Badge';
import Pagination from './Pagination';
import Tooltip from './Tooltip';

const DataGrid = <T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  rowKey = 'id',
  size = 'md',
  bordered = false,
  hoverable = true,
  striped = false,
  sortable = true,
  filterable = false,
  searchable = false,
  searchPlaceholder = 'Search...',
  virtualScroll = false,
  rowHeight = 48,
  overscan = 5,
  stickyHeader = true,
  resizable = false,
  selectable = false,
  selectedRowKeys = [],
  onRowClick,
  onSort,
  onFilter,
  onSearch,
  onSelectionChange,
  className,
  emptyText = 'No data available',
  pagination = false,
}: DataGridProps<T>) => {
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 0 });
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  
  const containerRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLTableElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const paddingClasses = {
    sm: 'px-2 py-1',
    md: 'px-4 py-3',
    lg: 'px-6 py-4',
  };

  // Get row key function - memoized for performance
  const getRowKey = useCallback((record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] || index.toString();
  }, [rowKey]);

  // Virtual scrolling calculations
  const containerHeight = virtualScroll ? 400 : 'auto';
  const totalHeight = data.length * rowHeight;
  const viewportHeight = virtualScroll ? 400 : totalHeight;

  // Calculate visible range for virtual scrolling
  const updateVisibleRange = useCallback(() => {
    if (!virtualScroll || !bodyRef.current) return;

    const scrollTop = bodyRef.current.scrollTop;
    const start = Math.floor(scrollTop / rowHeight);
    const visibleCount = Math.ceil(viewportHeight / rowHeight);
    const end = Math.min(start + visibleCount + overscan, data.length);

    setVisibleRange({ start: Math.max(0, start - overscan), end });
  }, [virtualScroll, rowHeight, viewportHeight, overscan, data.length]);

  useEffect(() => {
    if (virtualScroll) {
      updateVisibleRange();
    }
  }, [virtualScroll, updateVisibleRange, data.length]);

  // Handle selection
  const handleSelectAll = (checked: boolean) => {
    if (!selectable || !onSelectionChange) return;

    const newSelectedKeys = checked ? data.map((record, index) => getRowKey(record, index)) : [];
    const newSelectedRows = checked ? [...data] : [];
    onSelectionChange(newSelectedKeys, newSelectedRows);
  };

  const handleSelectRow = (record: T, index: number, checked: boolean) => {
    if (!selectable || !onSelectionChange) return;

    const key = getRowKey(record, index);
    let newSelectedKeys = [...selectedRowKeys];
    let newSelectedRows: T[] = [];

    if (checked) {
      newSelectedKeys.push(key);
    } else {
      newSelectedKeys = newSelectedKeys.filter(k => k !== key);
    }

    newSelectedRows = data.filter((r, i) => newSelectedKeys.includes(getRowKey(r, i)));
    onSelectionChange(newSelectedKeys, newSelectedRows);
  };

  // Handle sorting
  const handleSort = (column: TableColumn<T>) => {
    if (!column.sortable || !sortable) return;

    const key = column.dataIndex?.toString() || column.key;
    let direction: 'asc' | 'desc' = 'asc';

    if (sortKey === key && sortDirection === 'asc') {
      direction = 'desc';
    }

    setSortKey(key);
    setSortDirection(direction);
    onSort?.(key, direction);
  };

  // Handle search
  const handleSearch = (value: string) => {
    setSearchTerm(value);
    onSearch?.(value);
  };

  // Handle column resize
  const handleColumnResize = (columnKey: string, width: number) => {
    setColumnWidths(prev => ({ ...prev, [columnKey]: width }));
  };

  // Render cell content - memoized for performance
  const renderCell = useCallback((column: TableColumn<T>, record: T, index: number) => {
    if (column.render) {
      return column.render(
        column.dataIndex ? record[column.dataIndex] : record,
        record,
        index
      );
    }

    const value = column.dataIndex ? record[column.dataIndex] : record[column.key];
    
    if (value === null || value === undefined) {
      return <span className="text-gray-400">-</span>;
    }

    if (typeof value === 'boolean') {
      return value ? (
        <Badge variant="success" size="sm">Yes</Badge>
      ) : (
        <Badge variant="default" size="sm">No</Badge>
      );
    }

    if (typeof value === 'number') {
      return value.toLocaleString();
    }

    if (value instanceof Date) {
      return value.toLocaleDateString();
    }

    return value.toString();
  }, []);

  // Render sort icon
  const renderSortIcon = (column: TableColumn<T>) => {
    if (!column.sortable || !sortable) return null;

    const key = column.dataIndex?.toString() || column.key;
    const isActive = sortKey === key;

    return (
      <div className="ml-2 flex flex-col">
        <svg
          className={clsx(
            'w-3 h-3 -mb-1',
            isActive && sortDirection === 'asc' ? 'text-primary-600' : 'text-gray-400'
          )}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
        </svg>
        <svg
          className={clsx(
            'w-3 h-3',
            isActive && sortDirection === 'desc' ? 'text-primary-600' : 'text-gray-400'
          )}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </div>
    );
  };

  // Render resize handle
  const renderResizeHandle = (column: TableColumn<T>) => {
    if (!resizable) return null;

    return (
      <div
        className="absolute right-0 top-0 w-1 h-full bg-transparent hover:bg-primary-300 cursor-col-resize"
        onMouseDown={(e) => {
          e.preventDefault();
          const startX = e.clientX;
          const startWidth = columnWidths[column.key] || 150;

          const handleMouseMove = (e: MouseEvent) => {
            const newWidth = Math.max(50, startWidth + (e.clientX - startX));
            handleColumnResize(column.key, newWidth);
          };

          const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
          };

          document.addEventListener('mousemove', handleMouseMove);
          document.addEventListener('mouseup', handleMouseUp);
        }}
      />
    );
  };

  // Get visible data for virtual scrolling - memoized
  const visibleData = useMemo(() => {
    return virtualScroll 
      ? data.slice(visibleRange.start, visibleRange.end)
      : data;
  }, [virtualScroll, data, visibleRange.start, visibleRange.end]);

  // Table header
  const tableHeader = (
    <table 
      ref={headerRef}
      className="min-w-full divide-y divide-gray-200"
    >
      <thead className="bg-gray-50">
        <tr>
          {selectable && (
            <th className={clsx('relative', paddingClasses[size])}>
              <input
                type="checkbox"
                checked={selectedRowKeys.length === data.length && data.length > 0}
                onChange={(e) => handleSelectAll(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </th>
          )}
          {columns.map((column, index) => (
            <th
              key={column.key}
              className={clsx(
                'relative font-semibold text-gray-900 text-left border-b border-gray-200',
                paddingClasses[size],
                sizeClasses[size],
                column.sortable && sortable && 'cursor-pointer hover:bg-gray-100 transition-colors',
                column.className,
                {
                  'border-r border-gray-200': bordered && index < columns.length - 1,
                }
              )}
              style={{ 
                width: columnWidths[column.key] || column.width,
                minWidth: 50,
              }}
              onClick={() => handleSort(column)}
            >
              <div className={clsx(
                'flex items-center',
                column.align === 'center' && 'justify-center',
                column.align === 'right' && 'justify-end'
              )}>
                {column.title}
                {renderSortIcon(column)}
              </div>
              {renderResizeHandle(column)}
            </th>
          ))}
        </tr>
      </thead>
    </table>
  );

  // Virtual scrolling body
  const virtualBody = (
    <div
      ref={bodyRef}
      className="overflow-auto"
      style={{ height: containerHeight }}
      onScroll={updateVisibleRange}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: visibleRange.start * rowHeight,
            left: 0,
            right: 0,
          }}
        >
          <table className="min-w-full">
            <tbody className="bg-white divide-y divide-gray-200">
              {visibleData.map((record, relativeIndex) => {
                const actualIndex = visibleRange.start + relativeIndex;
                const key = getRowKey(record, actualIndex);
                const isSelected = selectedRowKeys.includes(key);

                return (
                  <tr
                    key={key}
                    className={clsx(
                      'transition-colors',
                      {
                        'hover:bg-gray-50': hoverable,
                        'bg-gray-50': striped && actualIndex % 2 === 1,
                        'bg-blue-50': isSelected,
                        'cursor-pointer': onRowClick,
                      }
                    )}
                    style={{ height: rowHeight }}
                    onClick={() => onRowClick?.(record, actualIndex)}
                  >
                    {selectable && (
                      <td className={paddingClasses[size]}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleSelectRow(record, actualIndex, e.target.checked)}
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </td>
                    )}
                    {columns.map((column, colIndex) => (
                      <td
                        key={column.key}
                        className={clsx(
                          paddingClasses[size],
                          sizeClasses[size],
                          column.className,
                          {
                            'border-r border-gray-200': bordered && colIndex < columns.length - 1,
                            'text-center': column.align === 'center',
                            'text-right': column.align === 'right',
                          }
                        )}
                        style={{ width: columnWidths[column.key] || column.width }}
                      >
                        {renderCell(column, record, actualIndex)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // Regular table body
  const regularBody = (
    <table className="min-w-full divide-y divide-gray-200">
      <tbody className="bg-white divide-y divide-gray-200">
        {data.map((record, rowIndex) => {
          const key = getRowKey(record, rowIndex);
          const isSelected = selectedRowKeys.includes(key);

          return (
            <tr
              key={key}
              className={clsx(
                'transition-colors',
                {
                  'hover:bg-gray-50': hoverable,
                  'bg-gray-50': striped && rowIndex % 2 === 1,
                  'bg-blue-50': isSelected,
                  'cursor-pointer': onRowClick,
                }
              )}
              onClick={() => onRowClick?.(record, rowIndex)}
            >
              {selectable && (
                <td className={paddingClasses[size]}>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => handleSelectRow(record, rowIndex, e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                </td>
              )}
              {columns.map((column, colIndex) => (
                <td
                  key={column.key}
                  className={clsx(
                    paddingClasses[size],
                    sizeClasses[size],
                    column.className,
                    {
                      'border-r border-gray-200': bordered && colIndex < columns.length - 1,
                      'text-center': column.align === 'center',
                      'text-right': column.align === 'right',
                    }
                  )}
                  style={{ width: columnWidths[column.key] || column.width }}
                >
                  {renderCell(column, record, rowIndex)}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );

  // Empty state
  const emptyState = (
    <div className="px-6 py-12 text-center text-gray-500">
      <div className="flex flex-col items-center">
        <svg className="w-12 h-12 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-lg font-medium text-gray-900 mb-1">No data found</p>
        <p className="text-sm text-gray-500">{emptyText}</p>
      </div>
    </div>
  );

  return (
    <div className={clsx('bg-white rounded-lg shadow-soft border border-gray-200', className)}>
      {/* Search and selection info */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          {searchable && (
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="block w-64 pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          )}
          
          {selectable && selectedRowKeys.length > 0 && (
            <div className="text-sm text-gray-600">
              {selectedRowKeys.length} of {data.length} selected
            </div>
          )}
        </div>

        {/* Data stats */}
        <div className="text-sm text-gray-500">
          {data.length} {data.length === 1 ? 'record' : 'records'}
        </div>
      </div>

      {/* Table content */}
      <div ref={containerRef} className="relative">
        {/* Header */}
        {stickyHeader && (
          <div className="sticky top-0 z-10 bg-white">
            {tableHeader}
          </div>
        )}

        {/* Body */}
        {loading ? (
          <div className="px-6 py-12 text-center">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-sm text-gray-500">Loading data...</p>
          </div>
        ) : data.length === 0 ? (
          emptyState
        ) : virtualScroll ? (
          virtualBody
        ) : (
          <div className="overflow-auto">
            {!stickyHeader && tableHeader}
            {regularBody}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && data.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200">
          <Pagination {...pagination} />
        </div>
      )}
    </div>
  );
};

// Healthcare-specific DataGrid variants
export const PatientDataGrid = <T extends Record<string, any>>(props: DataGridProps<T>) => {
  return (
    <DataGrid
      {...props}
      size="md"
      hoverable={true}
      searchable={true}
      selectable={true}
      stickyHeader={true}
      virtualScroll={props.data.length > 100}
      searchPlaceholder="Search patients..."
      emptyText="No patients found"
    />
  );
};

export const AuthorizationDataGrid = <T extends Record<string, any>>(props: DataGridProps<T>) => {
  return (
    <DataGrid
      {...props}
      size="md"
      hoverable={true}
      searchable={true}
      sortable={true}
      stickyHeader={true}
      resizable={true}
      virtualScroll={props.data.length > 200}
      searchPlaceholder="Search authorizations..."
      emptyText="No authorization records found"
    />
  );
};

// Memoized DataGrid component for performance
const MemoizedDataGrid = memo(DataGrid) as typeof DataGrid;
MemoizedDataGrid.displayName = 'DataGrid';

export default MemoizedDataGrid;
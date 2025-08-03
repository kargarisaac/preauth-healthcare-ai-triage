import React, { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import type { TableProps, TableColumn } from '@/types/ui';
import LoadingSpinner from './LoadingSpinner';
import Badge from './Badge';
import Tooltip from './Tooltip';

const Table = <T extends Record<string, any>>({
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
  onRowClick,
  onSort,
  onFilter,
  onSearch,
  className,
  emptyText = 'No data available',
  scroll,
}: TableProps<T>) => {
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [searchTerm, setSearchTerm] = useState('');

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

  // Get row key function
  const getRowKey = (record: T, index: number): string => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] || index.toString();
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

  // Render cell content
  const renderCell = (column: TableColumn<T>, record: T, index: number) => {
    if (column.render) {
      return column.render(
        column.dataIndex ? record[column.dataIndex] : record,
        record,
        index
      );
    }

    const value = column.dataIndex ? record[column.dataIndex] : record[column.key];
    
    // Handle different data types
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
  };

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

  // Table header
  const tableHeader = (
    <thead className="bg-gray-50 border-b border-gray-200">
      <tr>
        {columns.map((column, index) => (
          <th
            key={column.key}
            className={clsx(
              'font-semibold text-gray-900 text-left',
              paddingClasses[size],
              sizeClasses[size],
              column.sortable && sortable && 'cursor-pointer hover:bg-gray-100 transition-colors',
              column.className,
              {
                'border-r border-gray-200': bordered && index < columns.length - 1,
                'sticky left-0 bg-gray-50 z-10': column.fixed === 'left',
                'sticky right-0 bg-gray-50 z-10': column.fixed === 'right',
              }
            )}
            style={{ width: column.width }}
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
          </th>
        ))}
      </tr>
    </thead>
  );

  // Table body
  const tableBody = (
    <tbody className="bg-white divide-y divide-gray-200">
      {data.map((record, rowIndex) => (
        <tr
          key={getRowKey(record, rowIndex)}
          className={clsx(
            'transition-colors',
            {
              'hover:bg-gray-50': hoverable,
              'bg-gray-50': striped && rowIndex % 2 === 1,
              'cursor-pointer': onRowClick,
            }
          )}
          onClick={() => onRowClick?.(record, rowIndex)}
        >
          {columns.map((column, colIndex) => (
            <td
              key={column.key}
              className={clsx(
                paddingClasses[size],
                sizeClasses[size],
                column.className,
                {
                  'border-r border-gray-200': bordered && colIndex < columns.length - 1,
                  'sticky left-0 bg-white z-10': column.fixed === 'left',
                  'sticky right-0 bg-white z-10': column.fixed === 'right',
                  'text-center': column.align === 'center',
                  'text-right': column.align === 'right',
                }
              )}
              style={{ width: column.width }}
            >
              {renderCell(column, record, rowIndex)}
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );

  // Empty state
  const emptyState = (
    <tbody>
      <tr>
        <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
          <div className="flex flex-col items-center">
            <svg className="w-12 h-12 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-lg font-medium text-gray-900 mb-1">No data found</p>
            <p className="text-sm text-gray-500">{emptyText}</p>
          </div>
        </td>
      </tr>
    </tbody>
  );

  return (
    <div className={clsx('bg-white rounded-lg shadow-soft border border-gray-200', className)}>
      {/* Search bar */}
      {searchable && (
        <div className="p-4 border-b border-gray-200">
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
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        </div>
      )}

      {/* Table container */}
      <div
        className="overflow-auto"
        style={{
          maxHeight: scroll?.y,
          maxWidth: scroll?.x,
        }}
      >
        <table className="min-w-full divide-y divide-gray-200">
          {tableHeader}
          {loading ? (
            <tbody>
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center">
                  <LoadingSpinner size="lg" />
                  <p className="mt-4 text-sm text-gray-500">Loading data...</p>
                </td>
              </tr>
            </tbody>
          ) : data.length === 0 ? (
            emptyState
          ) : (
            tableBody
          )}
        </table>
      </div>
    </div>
  );
};

// Healthcare-specific table variants
export const PatientTable = <T extends Record<string, any>>(props: TableProps<T>) => {
  return (
    <Table
      {...props}
      size="md"
      hoverable={true}
      searchable={true}
      searchPlaceholder="Search patients..."
      emptyText="No patients found"
    />
  );
};

export const AuthorizationTable = <T extends Record<string, any>>(props: TableProps<T>) => {
  return (
    <Table
      {...props}
      size="md"
      hoverable={true}
      searchable={true}
      sortable={true}
      searchPlaceholder="Search authorizations..."
      emptyText="No authorization records found"
    />
  );
};

export const MedicalRecordsTable = <T extends Record<string, any>>(props: TableProps<T>) => {
  return (
    <Table
      {...props}
      size="sm"
      hoverable={true}
      striped={true}
      searchable={true}
      searchPlaceholder="Search medical records..."
      emptyText="No medical records found"
    />
  );
};

export default Table;
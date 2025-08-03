import React, { useState } from 'react';
import { clsx } from 'clsx';
import type { PaginationProps } from '@/types/ui';

const Pagination: React.FC<PaginationProps> = ({
  current,
  total,
  pageSize,
  showSizeChanger = false,
  showQuickJumper = false,
  showTotal = false,
  pageSizeOptions = [10, 20, 50, 100],
  size = 'md',
  simple = false,
  onChange,
  onShowSizeChange,
  className,
}) => {
  const [jumpValue, setJumpValue] = useState('');

  const totalPages = Math.ceil(total / pageSize);
  const startItem = (current - 1) * pageSize + 1;
  const endItem = Math.min(current * pageSize, total);

  const sizeClasses = {
    sm: {
      button: 'px-2 py-1 text-xs',
      input: 'px-2 py-1 text-xs w-12',
      select: 'px-2 py-1 text-xs',
    },
    md: {
      button: 'px-3 py-2 text-sm',
      input: 'px-3 py-2 text-sm w-16',
      select: 'px-3 py-2 text-sm',
    },
    lg: {
      button: 'px-4 py-2 text-base',
      input: 'px-4 py-2 text-base w-20',
      select: 'px-4 py-2 text-base',
    },
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== current) {
      onChange?.(page, pageSize);
    }
  };

  const handleSizeChange = (newSize: number) => {
    const newPage = Math.ceil((startItem - 1) / newSize) + 1;
    onShowSizeChange?.(newPage, newSize);
    onChange?.(newPage, newSize);
  };

  const handleJumpToPage = () => {
    const page = parseInt(jumpValue, 10);
    if (!isNaN(page)) {
      handlePageChange(page);
      setJumpValue('');
    }
  };

  const getPageNumbers = () => {
    if (simple || totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const pages: (number | string)[] = [];
    
    if (current <= 4) {
      // Show first 5 pages, ..., last page
      pages.push(...[1, 2, 3, 4, 5]);
      if (totalPages > 6) pages.push('...', totalPages);
    } else if (current >= totalPages - 3) {
      // Show first page, ..., last 5 pages
      pages.push(1, '...');
      for (let i = totalPages - 4; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page, ..., current-1, current, current+1, ..., last page
      pages.push(1, '...', current - 1, current, current + 1, '...', totalPages);
    }

    return pages;
  };

  const renderTotalInfo = () => {
    if (!showTotal) return null;

    const totalText = typeof showTotal === 'function' 
      ? showTotal(total, [startItem, endItem])
      : `Showing ${startItem}-${endItem} of ${total} items`;

    return (
      <div className={clsx('text-gray-600', size === 'sm' ? 'text-xs' : 'text-sm')}>
        {totalText}
      </div>
    );
  };

  const renderSizeChanger = () => {
    if (!showSizeChanger) return null;

    return (
      <div className="flex items-center space-x-2">
        <span className={clsx('text-gray-600', size === 'sm' ? 'text-xs' : 'text-sm')}>
          Show
        </span>
        <select
          value={pageSize}
          onChange={(e) => handleSizeChange(Number(e.target.value))}
          className={clsx(
            'border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500',
            sizeClasses[size].select
          )}
        >
          {pageSizeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <span className={clsx('text-gray-600', size === 'sm' ? 'text-xs' : 'text-sm')}>
          per page
        </span>
      </div>
    );
  };

  const renderQuickJumper = () => {
    if (!showQuickJumper) return null;

    return (
      <div className="flex items-center space-x-2">
        <span className={clsx('text-gray-600', size === 'sm' ? 'text-xs' : 'text-sm')}>
          Go to
        </span>
        <input
          type="number"
          min={1}
          max={totalPages}
          value={jumpValue}
          onChange={(e) => setJumpValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleJumpToPage()}
          className={clsx(
            'border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500',
            sizeClasses[size].input
          )}
          placeholder="Page"
        />
        <button
          onClick={handleJumpToPage}
          disabled={!jumpValue || isNaN(parseInt(jumpValue, 10))}
          className={clsx(
            'btn btn-secondary',
            sizeClasses[size].button,
            size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : 'btn-md'
          )}
        >
          Go
        </button>
      </div>
    );
  };

  if (totalPages === 0) return null;

  if (simple) {
    return (
      <div className={clsx('flex items-center justify-between', className)}>
        {renderTotalInfo()}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handlePageChange(current - 1)}
            disabled={current === 1}
            className={clsx(
              'btn btn-secondary',
              sizeClasses[size].button,
              size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : 'btn-md'
            )}
          >
            Previous
          </button>
          <span className={clsx('text-gray-600', size === 'sm' ? 'text-xs' : 'text-sm')}>
            {current} / {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(current + 1)}
            disabled={current === totalPages}
            className={clsx(
              'btn btn-secondary',
              sizeClasses[size].button,
              size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : 'btn-md'
            )}
          >
            Next
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4', className)}>
      <div className="flex flex-wrap items-center gap-4">
        {renderTotalInfo()}
        {renderSizeChanger()}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Previous button */}
        <button
          onClick={() => handlePageChange(current - 1)}
          disabled={current === 1}
          className={clsx(
            'btn btn-secondary',
            sizeClasses[size].button,
            size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : 'btn-md'
          )}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        {/* Page numbers */}
        <div className="flex items-center space-x-1">
          {getPageNumbers().map((pageNum, index) => {
            if (pageNum === '...') {
              return (
                <span
                  key={`ellipsis-${index}`}
                  className={clsx('px-2 text-gray-400', size === 'sm' ? 'text-xs' : 'text-sm')}
                >
                  ...
                </span>
              );
            }

            const isActive = pageNum === current;
            return (
              <button
                key={pageNum}
                onClick={() => handlePageChange(pageNum as number)}
                className={clsx(
                  'border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500',
                  sizeClasses[size].button,
                  isActive
                    ? 'bg-primary-500 text-white border-primary-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                )}
              >
                {pageNum}
              </button>
            );
          })}
        </div>

        {/* Next button */}
        <button
          onClick={() => handlePageChange(current + 1)}
          disabled={current === totalPages}
          className={clsx(
            'btn btn-secondary',
            sizeClasses[size].button,
            size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : 'btn-md'
          )}
        >
          Next
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        {renderQuickJumper()}
      </div>
    </div>
  );
};

// Healthcare-specific pagination for patient lists
export const PatientPagination: React.FC<PaginationProps & {
  patientCount?: number;
  activePatients?: number;
}> = ({ patientCount, activePatients, ...props }) => {
  const customShowTotal = (total: number, range: [number, number]) => {
    const activeText = activePatients ? ` (${activePatients} active)` : '';
    return `Showing ${range[0]}-${range[1]} of ${total} patients${activeText}`;
  };

  return (
    <Pagination
      {...props}
      showTotal={customShowTotal}
      pageSizeOptions={[5, 10, 25, 50]}
    />
  );
};

// Medical records pagination
export const RecordsPagination: React.FC<PaginationProps & {
  recordType?: string;
}> = ({ recordType = 'records', ...props }) => {
  const customShowTotal = (total: number, range: [number, number]) => {
    return `Showing ${range[0]}-${range[1]} of ${total} ${recordType}`;
  };

  return (
    <Pagination
      {...props}
      showTotal={customShowTotal}
      showSizeChanger={true}
      showQuickJumper={true}
      pageSizeOptions={[10, 25, 50, 100]}
    />
  );
};

export default Pagination;
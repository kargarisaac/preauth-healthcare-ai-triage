import { useState, useCallback, useMemo } from 'react';
import type {
  RequestTableColumn,
  RequestTableState,
  RequestHistoryItem,
  RequestSortOptions,
} from '@/types/requests';

// Default column configuration
const defaultColumns: RequestTableColumn[] = [
  { key: 'requestNumber', label: 'Request #', sortable: true, visible: true, width: 150 },
  { key: 'memberName', label: 'Member', sortable: true, visible: true, width: 200 },
  { key: 'providerName', label: 'Provider', sortable: true, visible: true, width: 180 },
  { key: 'serviceDescription', label: 'Service', sortable: false, visible: true, width: 250 },
  { key: 'status', label: 'Status', sortable: true, visible: true, width: 120, format: 'status' },
  { key: 'requestedAmount', label: 'Amount', sortable: true, visible: true, width: 120, format: 'currency' },
  { key: 'submissionDate', label: 'Submitted', sortable: true, visible: true, width: 140, format: 'date' },
  { key: 'priority', label: 'Priority', sortable: true, visible: true, width: 100, format: 'priority' },
  { key: 'actions', label: 'Actions', sortable: false, visible: true, width: 100 },
];

// Local storage keys
const STORAGE_KEYS = {
  COLUMNS: 'nazmito_table_columns',
  COLUMN_ORDER: 'nazmito_table_column_order',
  PAGE_SIZE: 'nazmito_table_page_size',
} as const;

export function useTableState() {
  // Initialize columns from localStorage or defaults
  const [columns, setColumns] = useState<RequestTableColumn[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.COLUMNS);
      if (saved) {
        const savedColumns = JSON.parse(saved);
        // Merge with defaults to handle new columns
        return defaultColumns.map(defaultCol => {
          const savedCol = savedColumns.find((c: RequestTableColumn) => c.key === defaultCol.key);
          return savedCol ? { ...defaultCol, ...savedCol } : defaultCol;
        });
      }
    } catch (error) {
      console.warn('Failed to load table columns from localStorage:', error);
    }
    return defaultColumns;
  });

  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [expandedRows, setExpandedRows] = useState<string[]>([]);

  // Column visibility
  const toggleColumnVisibility = useCallback((columnKey: keyof RequestHistoryItem | 'actions') => {
    setColumns(prev => {
      const updated = prev.map(col =>
        col.key === columnKey ? { ...col, visible: !col.visible } : col
      );
      
      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.COLUMNS, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to save table columns to localStorage:', error);
      }
      
      return updated;
    });
  }, []);

  // Column width adjustment
  const updateColumnWidth = useCallback((columnKey: keyof RequestHistoryItem | 'actions', width: number) => {
    setColumns(prev => {
      const updated = prev.map(col =>
        col.key === columnKey ? { ...col, width } : col
      );
      
      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.COLUMNS, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to save table columns to localStorage:', error);
      }
      
      return updated;
    });
  }, []);

  // Column reordering
  const reorderColumns = useCallback((startIndex: number, endIndex: number) => {
    setColumns(prev => {
      const result = Array.from(prev);
      const [removed] = result.splice(startIndex, 1);
      result.splice(endIndex, 0, removed);
      
      // Save to localStorage
      try {
        localStorage.setItem(STORAGE_KEYS.COLUMNS, JSON.stringify(result));
      } catch (error) {
        console.warn('Failed to save table columns to localStorage:', error);
      }
      
      return result;
    });
  }, []);

  // Reset columns to default
  const resetColumns = useCallback(() => {
    setColumns(defaultColumns);
    try {
      localStorage.removeItem(STORAGE_KEYS.COLUMNS);
    } catch (error) {
      console.warn('Failed to remove table columns from localStorage:', error);
    }
  }, []);

  // Row selection
  const toggleRowSelection = useCallback((rowId: string) => {
    setSelectedRows(prev =>
      prev.includes(rowId)
        ? prev.filter(id => id !== rowId)
        : [...prev, rowId]
    );
  }, []);

  const selectAllRows = useCallback((allRowIds: string[]) => {
    setSelectedRows(allRowIds);
  }, []);

  const clearRowSelection = useCallback(() => {
    setSelectedRows([]);
  }, []);

  const toggleSelectAll = useCallback((allRowIds: string[]) => {
    if (selectedRows.length === allRowIds.length) {
      clearRowSelection();
    } else {
      selectAllRows(allRowIds);
    }
  }, [selectedRows.length, selectAllRows, clearRowSelection]);

  // Row expansion
  const toggleRowExpansion = useCallback((rowId: string) => {
    setExpandedRows(prev =>
      prev.includes(rowId)
        ? prev.filter(id => id !== rowId)
        : [...prev, rowId]
    );
  }, []);

  const expandAllRows = useCallback((allRowIds: string[]) => {
    setExpandedRows(allRowIds);
  }, []);

  const collapseAllRows = useCallback(() => {
    setExpandedRows([]);
  }, []);

  // Bulk row operations
  const selectRowRange = useCallback((startRowId: string, endRowId: string, allRowIds: string[]) => {
    const startIndex = allRowIds.indexOf(startRowId);
    const endIndex = allRowIds.indexOf(endRowId);
    
    if (startIndex !== -1 && endIndex !== -1) {
      const minIndex = Math.min(startIndex, endIndex);
      const maxIndex = Math.max(startIndex, endIndex);
      const rangeIds = allRowIds.slice(minIndex, maxIndex + 1);
      
      setSelectedRows(prev => {
        const newSelection = new Set([...prev, ...rangeIds]);
        return Array.from(newSelection);
      });
    }
  }, []);

  // Computed values
  const visibleColumns = useMemo(
    () => columns.filter(col => col.visible),
    [columns]
  );

  const isAllSelected = useMemo(
    () => (allRowIds: string[]) => selectedRows.length > 0 && selectedRows.length === allRowIds.length,
    [selectedRows.length]
  );

  const isPartiallySelected = useMemo(
    () => (allRowIds: string[]) => selectedRows.length > 0 && selectedRows.length < allRowIds.length,
    [selectedRows.length]
  );

  const selectedCount = useMemo(
    () => selectedRows.length,
    [selectedRows.length]
  );

  const expandedCount = useMemo(
    () => expandedRows.length,
    [expandedRows.length]
  );

  // Table state object
  const tableState: RequestTableState = {
    columns,
    selectedRows,
    expandedRows,
    filters: {
      search: {},
      sort: { field: 'submissionDate', direction: 'desc' },
      pagination: { page: 1, pageSize: 25 },
    },
    isLoading: false,
  };

  return {
    // State
    columns,
    visibleColumns,
    selectedRows,
    expandedRows,
    tableState,

    // Column operations
    toggleColumnVisibility,
    updateColumnWidth,
    reorderColumns,
    resetColumns,

    // Row selection
    toggleRowSelection,
    selectAllRows,
    clearRowSelection,
    toggleSelectAll,
    selectRowRange,

    // Row expansion
    toggleRowExpansion,
    expandAllRows,
    collapseAllRows,

    // Computed values
    isAllSelected,
    isPartiallySelected,
    selectedCount,
    expandedCount,

    // Utilities
    hasSelectedRows: selectedCount > 0,
    hasExpandedRows: expandedCount > 0,
  };
}
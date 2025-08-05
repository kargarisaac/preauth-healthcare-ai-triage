import React, { useState, useMemo } from 'react';
import {
  Calendar,
  FileText,
  Eye,
  Download,
  Play,
  Filter,
  Search,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';
import { Table, Badge, StatusBadge, Button, Input, Select, DatePicker, Card } from '../ui';
import type { TableColumn } from '../../types/ui';

interface FileRecord {
  id: string;
  filename: string;
  upload_date: string;
  file_size: number;
  source: 'eClaimLink' | 'Shafafiya' | 'CSV';
  status: 'processing' | 'completed' | 'error' | 'pending';
  processed_date?: string;
  total_claims?: number;
  approved_claims?: number;
  total_amount?: number;
  error_message?: string;
  analysis_status?: 'not_started' | 'in_progress' | 'completed' | 'failed';
}

interface PatientHistoryTableProps {
  patientId: string;
  data: FileRecord[];
  isLoading?: boolean;
  onViewDetails?: (record: FileRecord) => void;
  onReanalyze?: (record: FileRecord) => void;
  onDownload?: (record: FileRecord) => void;
  className?: string;
}

const PatientHistoryTable: React.FC<PatientHistoryTableProps> = ({
  patientId,
  data,
  isLoading = false,
  onViewDetails,
  onReanalyze,
  onDownload,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<{ start?: Date; end?: Date }>({});
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' }>({
    key: 'upload_date',
    direction: 'desc'
  });

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSourceIcon = (source: string) => {
    return <FileText className="h-4 w-4 text-gray-500" />;
  };

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = data.filter((record) => {
      // Search filter
      if (searchTerm && !record.filename.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Status filter
      if (statusFilter !== 'all' && record.status !== statusFilter) {
        return false;
      }
      
      // Source filter
      if (sourceFilter !== 'all' && record.source !== sourceFilter) {
        return false;
      }
      
      // Date range filter
      if (dateRange.start || dateRange.end) {
        const recordDate = new Date(record.upload_date);
        if (dateRange.start && recordDate < dateRange.start) return false;
        if (dateRange.end && recordDate > dateRange.end) return false;
      }
      
      return true;
    });

    // Sort data
    filtered.sort((a, b) => {
      const aVal = a[sortConfig.key as keyof FileRecord];
      const bVal = b[sortConfig.key as keyof FileRecord];
      
      if (aVal === undefined || bVal === undefined) return 0;
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortConfig.direction === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
      }
      
      return 0;
    });

    return filtered;
  }, [data, searchTerm, statusFilter, sourceFilter, dateRange, sortConfig]);

  const columns: TableColumn<FileRecord>[] = [
    {
      key: 'filename',
      title: 'File Name',
      dataIndex: 'filename',
      sortable: true,
      render: (filename: string, record: FileRecord) => (
        <div className="flex items-center space-x-3">
          {getSourceIcon(record.source)}
          <div>
            <div className="font-medium text-gray-900">{filename}</div>
            <div className="text-xs text-gray-500">{formatFileSize(record.file_size)}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'upload_date',
      title: 'Upload Date',
      dataIndex: 'upload_date',
      sortable: true,
      render: (date: string) => (
        <div className="text-sm text-gray-900">{formatDate(date)}</div>
      ),
    },
    {
      key: 'source',
      title: 'Source',
      dataIndex: 'source',
      sortable: true,
      render: (source: string) => (
        <Badge 
          variant={
            source === 'eClaimLink' ? 'primary' :
            source === 'Shafafiya' ? 'info' : 'default'
          }
          size="sm"
        >
          {source}
        </Badge>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      sortable: true,
      render: (status: string, record: FileRecord) => (
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <StatusBadge status={status} />
          {record.error_message && (
            <div className="text-xs text-red-600 mt-1" title={record.error_message}>
              Error details available
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'claims_summary',
      title: 'Claims Summary',
      render: (_, record: FileRecord) => {
        if (!record.total_claims) {
          return <span className="text-gray-400">-</span>;
        }
        
        return (
          <div className="text-sm">
            <div className="text-gray-900">
              {record.total_claims} claims
            </div>
            {record.approved_claims !== undefined && (
              <div className="text-gray-500">
                {record.approved_claims} approved
              </div>
            )}
          </div>
        );
      },
    },
    {
      key: 'total_amount',
      title: 'Total Amount',
      dataIndex: 'total_amount',
      sortable: true,
      render: (amount?: number) => (
        amount ? (
          <span className="font-medium text-gray-900">
            {formatCurrency(amount)}
          </span>
        ) : (
          <span className="text-gray-400">-</span>
        )
      ),
    },
    {
      key: 'analysis_status',
      title: 'Analysis',
      dataIndex: 'analysis_status',
      render: (analysisStatus: string = 'not_started', record: FileRecord) => {
        const canAnalyze = record.status === 'completed';
        
        return (
          <div className="flex items-center space-x-2">
            <Badge 
              variant={
                analysisStatus === 'completed' ? 'success' :
                analysisStatus === 'in_progress' ? 'warning' :
                analysisStatus === 'failed' ? 'error' : 'default'
              }
              size="sm"
            >
              {analysisStatus === 'not_started' ? 'Ready' : 
               analysisStatus === 'in_progress' ? 'Running' :
               analysisStatus === 'completed' ? 'Done' : 'Failed'}
            </Badge>
            {canAnalyze && analysisStatus !== 'in_progress' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onReanalyze?.(record)}
                className="ml-2"
              >
                <Play className="h-3 w-3 mr-1" />
                {analysisStatus === 'not_started' ? 'Analyze' : 'Re-analyze'}
              </Button>
            )}
          </div>
        );
      },
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (_, record: FileRecord) => (
        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onViewDetails?.(record)}
          >
            <Eye className="h-3 w-3 mr-1" />
            View
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onDownload?.(record)}
            disabled={record.status !== 'completed'}
          >
            <Download className="h-3 w-3 mr-1" />
            Download
          </Button>
        </div>
      ),
    },
  ];

  const handleSort = (key: string, direction: 'asc' | 'desc') => {
    setSortConfig({ key, direction });
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setSourceFilter('all');
    setDateRange({});
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-64">
            <Input
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full"
              icon={<Search className="h-4 w-4" />}
            />
          </div>
          
          <Select
            value={statusFilter}
            onChange={(value) => setStatusFilter(value)}
            options={[
              { value: 'all', label: 'All Statuses' },
              { value: 'completed', label: 'Completed' },
              { value: 'processing', label: 'Processing' },
              { value: 'pending', label: 'Pending' },
              { value: 'error', label: 'Error' },
            ]}
            className="min-w-32"
          />
          
          <Select
            value={sourceFilter}
            onChange={(value) => setSourceFilter(value)}
            options={[
              { value: 'all', label: 'All Sources' },
              { value: 'eClaimLink', label: 'eClaimLink' },
              { value: 'Shafafiya', label: 'Shafafiya' },
              { value: 'CSV', label: 'CSV' },
            ]}
            className="min-w-32"
          />
          
          <div className="flex items-center space-x-2">
            <DatePicker
              placeholder="Start Date"
              value={dateRange.start}
              onChange={(date) => setDateRange({ ...dateRange, start: date })}
            />
            <span className="text-gray-500">to</span>
            <DatePicker
              placeholder="End Date"
              value={dateRange.end}
              onChange={(date) => setDateRange({ ...dateRange, end: date })}
            />
          </div>
          
          {(searchTerm || statusFilter !== 'all' || sourceFilter !== 'all' || dateRange.start || dateRange.end) && (
            <Button variant="secondary" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing {filteredAndSortedData.length} of {data.length} files
        </span>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Completed</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>Processing</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Pending</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Error</span>
          </div>
        </div>
      </div>

      {/* Table */}
      <Table
        columns={columns}
        data={filteredAndSortedData}
        loading={isLoading}
        rowKey="id"
        size="md"
        hoverable={true}
        sortable={true}
        onSort={handleSort}
        emptyText="No files found for this patient"
        className="bg-white"
      />
    </div>
  );
};

export default PatientHistoryTable;
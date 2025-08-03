import React, { useState, useCallback, useMemo, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import { usePerformanceMonitor, useOperationPerformance } from '@hooks/performance/usePerformanceMonitor';
import { useAccessibility } from '@hooks/accessibility/useAccessibility';
import { trackHealthcareMetric, trackFileProcessing, trackUserInteraction } from '@utils/performance';
import { AnimatedProgress, AnimatedButton } from '@components/ui/MicroInteractions';
import { VirtualizedTable, TableColumn } from '@components/ui/VirtualizedTable';

interface FileProcessingResult {
  fileName: string;
  fileSize: number;
  processingTime: number;
  status: 'processing' | 'completed' | 'failed' | 'validating';
  fhirBundle?: any;
  validationErrors?: string[];
  progress: number;
  metadata?: {
    patientCount?: number;
    claimCount?: number;
    procedureCount?: number;
    diagnosisCount?: number;
  };
}

interface HealthcareDataProcessorProps {
  onFileProcessed?: (result: FileProcessingResult) => void;
  onBatchComplete?: (results: FileProcessingResult[]) => void;
  maxFileSize?: number; // MB
  acceptedFormats?: string[];
  enableBatchProcessing?: boolean;
  enableRealTimeValidation?: boolean;
  className?: string;
}

const SUPPORTED_FORMATS = {
  'text/xml': 'XML (eClaimLink, Shafafiya)',
  'text/csv': 'CSV (Healthcare Data)',
  'application/json': 'JSON (FHIR Bundle)',
  'application/pdf': 'PDF (Claims Document)',
};

const HEALTHCARE_VALIDATION_RULES = {
  patientId: /^[A-Z]{2}\d{12}$/, // UAE Emirates ID format
  insuranceNumber: /^\d{10,15}$/, // Insurance number format
  icdCode: /^[A-Z]\d{2}(\.\d{1,2})?$/, // ICD-10 format
  cptCode: /^\d{5}$/, // CPT code format
};

export const HealthcareDataProcessor: React.FC<HealthcareDataProcessorProps> = React.memo(({
  onFileProcessed,
  onBatchComplete,
  maxFileSize = 50, // 50MB default
  acceptedFormats = Object.keys(SUPPORTED_FORMATS),
  enableBatchProcessing = true,
  enableRealTimeValidation = true,
  className = '',
}) => {
  const [files, setFiles] = useState<FileProcessingResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingQueue, setProcessingQueue] = useState<File[]>([]);
  const [globalProgress, setGlobalProgress] = useState(0);
  
  const processingWorkerRef = useRef<Worker | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const { metrics, trackInteraction } = usePerformanceMonitor({
    componentName: 'HealthcareDataProcessor',
    trackRenders: true,
    trackMemory: true,
    trackInteractions: true,
  });
  
  const { announceFileProcessingStatus, announceHealthcareError } = useAccessibility({
    announcePageChanges: false,
    announceErrors: true,
  });
  
  const {
    startOperation: startFileProcessing,
    endOperation: endFileProcessing,
  } = useOperationPerformance('file_processing');

  // Validate healthcare-specific data
  const validateHealthcareData = useCallback((data: any, fileName: string): string[] => {
    const errors: string[] = [];
    
    try {
      // Check for required healthcare fields
      if (!data.patientId && !data.patient_id && !data.memberId) {
        errors.push('Missing patient/member identification');
      }
      
      // Validate Emirates ID format if present
      const patientId = data.patientId || data.patient_id || data.memberId;
      if (patientId && !HEALTHCARE_VALIDATION_RULES.patientId.test(patientId)) {
        errors.push('Invalid Emirates ID format');
      }
      
      // Validate insurance number
      const insuranceNumber = data.insuranceNumber || data.insurance_number;
      if (insuranceNumber && !HEALTHCARE_VALIDATION_RULES.insuranceNumber.test(insuranceNumber)) {
        errors.push('Invalid insurance number format');
      }
      
      // Validate medical codes
      if (data.diagnosisCodes) {
        const invalidIcdCodes = data.diagnosisCodes.filter(
          (code: string) => !HEALTHCARE_VALIDATION_RULES.icdCode.test(code)
        );
        if (invalidIcdCodes.length > 0) {
          errors.push(`Invalid ICD-10 codes: ${invalidIcdCodes.join(', ')}`);
        }
      }
      
      if (data.procedureCodes) {
        const invalidCptCodes = data.procedureCodes.filter(
          (code: string) => !HEALTHCARE_VALIDATION_RULES.cptCode.test(code)
        );
        if (invalidCptCodes.length > 0) {
          errors.push(`Invalid CPT codes: ${invalidCptCodes.join(', ')}`);
        }
      }
      
      // Healthcare-specific business rules
      if (data.dateOfService) {
        const serviceDate = new Date(data.dateOfService);
        const today = new Date();
        const maxPastDays = 365 * 2; // 2 years
        
        if (serviceDate > today) {
          errors.push('Service date cannot be in the future');
        }
        
        if ((today.getTime() - serviceDate.getTime()) / (1000 * 60 * 60 * 24) > maxPastDays) {
          errors.push('Service date is too old (max 2 years)');
        }
      }
      
    } catch (error) {
      errors.push(`Validation error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    
    return errors;
  }, []);

  // Process individual file
  const processFile = useCallback(async (file: File): Promise<FileProcessingResult> => {
    const startTime = Date.now();
    startFileProcessing({ fileName: file.name, fileSize: file.size });
    
    announceFileProcessingStatus('started', file.name);
    
    const result: FileProcessingResult = {
      fileName: file.name,
      fileSize: file.size,
      processingTime: 0,
      status: 'processing',
      progress: 0,
      validationErrors: [],
    };

    try {
      // Simulate progress updates
      const updateProgress = (progress: number, status?: FileProcessingResult['status']) => {
        setFiles(prev => prev.map(f => 
          f.fileName === file.name 
            ? { ...f, progress, ...(status && { status }) }
            : f
        ));
      };

      updateProgress(10, 'processing');
      
      // Read file content
      const content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = reject;
        reader.readAsText(file);
      });
      
      updateProgress(30);

      // Parse content based on file type
      let parsedData: any;
      if (file.type === 'text/xml' || file.name.endsWith('.xml')) {
        // XML processing would go here
        parsedData = { type: 'xml', content }; // Simplified
      } else if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        // CSV processing would go here
        parsedData = { type: 'csv', content }; // Simplified
      } else if (file.type === 'application/json' || file.name.endsWith('.json')) {
        parsedData = JSON.parse(content);
      }
      
      updateProgress(60, 'validating');

      // Validate healthcare data
      if (enableRealTimeValidation) {
        const validationErrors = validateHealthcareData(parsedData, file.name);
        result.validationErrors = validationErrors;
        
        if (validationErrors.length > 0) {
          announceHealthcareError(
            `File ${file.name} has ${validationErrors.length} validation errors`,
            'file processing'
          );
        }
      }
      
      updateProgress(80);

      // Simulate FHIR mapping
      await new Promise(resolve => setTimeout(resolve, 500));
      result.fhirBundle = {
        resourceType: 'Bundle',
        id: `bundle-${Date.now()}`,
        timestamp: new Date().toISOString(),
        // ... FHIR bundle structure
      };
      
      // Extract metadata
      result.metadata = {
        patientCount: Math.floor(Math.random() * 100) + 1,
        claimCount: Math.floor(Math.random() * 200) + 10,
        procedureCount: Math.floor(Math.random() * 500) + 50,
        diagnosisCount: Math.floor(Math.random() * 150) + 20,
      };
      
      updateProgress(100, 'completed');
      result.status = 'completed';
      
      announceFileProcessingStatus('completed', file.name);
      
    } catch (error) {
      result.status = 'failed';
      result.validationErrors = [error instanceof Error ? error.message : 'Unknown processing error'];
      
      announceFileProcessingStatus('failed', file.name);
      announceHealthcareError(
        error instanceof Error ? error.message : 'Unknown error',
        `processing ${file.name}`
      );
    }
    
    const processingTime = Date.now() - startTime;
    result.processingTime = processingTime;
    
    // Track performance metrics
    trackHealthcareMetric('fileProcessingTime', processingTime);
    trackFileProcessing(file.type, file.size, processingTime);
    endFileProcessing(result.status === 'completed', {
      fileName: file.name,
      hasValidationErrors: (result.validationErrors?.length || 0) > 0,
    });
    
    return result;
  }, [enableRealTimeValidation, validateHealthcareData, announceFileProcessingStatus, announceHealthcareError, startFileProcessing, endFileProcessing]);

  // Handle file drop
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!enableBatchProcessing && acceptedFiles.length > 1) {
      announceHealthcareError('Multiple file upload is disabled', 'file selection');
      return;
    }
    
    trackInteraction('file_drop', 'DropZone', {
      fileCount: acceptedFiles.length,
      totalSize: acceptedFiles.reduce((sum, file) => sum + file.size, 0),
    });
    
    // Validate file sizes
    const oversizedFiles = acceptedFiles.filter(file => file.size > maxFileSize * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      announceHealthcareError(
        `Files too large: ${oversizedFiles.map(f => f.name).join(', ')}. Maximum size is ${maxFileSize}MB`,
        'file validation'
      );
      return;
    }
    
    setIsProcessing(true);
    
    // Initialize file results
    const initialResults: FileProcessingResult[] = acceptedFiles.map(file => ({
      fileName: file.name,
      fileSize: file.size,
      processingTime: 0,
      status: 'processing' as const,
      progress: 0,
    }));
    
    setFiles(prev => [...prev, ...initialResults]);

    try {
      // Process files (parallel processing for better performance)
      const results = await Promise.all(
        acceptedFiles.map(file => processFile(file))
      );
      
      // Update results
      setFiles(prev => {
        const updated = [...prev];
        results.forEach(result => {
          const index = updated.findIndex(f => f.fileName === result.fileName);
          if (index !== -1) {
            updated[index] = result;
          }
        });
        return updated;
      });
      
      // Notify completion
      results.forEach(result => onFileProcessed?.(result));
      onBatchComplete?.(results);
      
    } catch (error) {
      announceHealthcareError(
        error instanceof Error ? error.message : 'Batch processing failed',
        'batch processing'
      );
    } finally {
      setIsProcessing(false);
    }
  }, [enableBatchProcessing, maxFileSize, processFile, onFileProcessed, onBatchComplete, trackInteraction, announceHealthcareError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFormats.reduce((acc, format) => ({ ...acc, [format]: [] }), {}),
    maxFiles: enableBatchProcessing ? 10 : 1,
    disabled: isProcessing,
  });

  // Table columns for file results
  const tableColumns: TableColumn<FileProcessingResult>[] = useMemo(() => [
    {
      key: 'fileName',
      header: 'File Name',
      width: 200,
      render: (value, row) => (
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-400" />
          <span className="font-medium">{value}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: 120,
      render: (value, row) => {
        const statusConfig = {
          processing: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50' },
          validating: { icon: Zap, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          completed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
          failed: { icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50' },
        };
        
        const config = statusConfig[value];
        const Icon = config.icon;
        
        return (
          <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color} ${config.bg}`}>
            <Icon className="w-3 h-3" />
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </div>
        );
      },
    },
    {
      key: 'progress',
      header: 'Progress',
      width: 150,
      render: (value, row) => (
        <AnimatedProgress
          value={value}
          height={6}
          color={row.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}
          showPercentage={false}
        />
      ),
    },
    {
      key: 'processingTime',
      header: 'Processing Time',
      width: 120,
      render: (value) => value > 0 ? `${(value / 1000).toFixed(1)}s` : '-',
    },
    {
      key: 'metadata',
      header: 'Healthcare Data',
      width: 200,
      render: (value, row) => {
        if (!value || row.status !== 'completed') return '-';
        
        return (
          <div className="text-xs text-gray-600">
            <div>Patients: {value.patientCount || 0}</div>
            <div>Claims: {value.claimCount || 0}</div>
          </div>
        );
      },
    },
    {
      key: 'validationErrors',
      header: 'Validation',
      width: 100,
      render: (value, row) => {
        if (!value || value.length === 0) {
          return row.status === 'completed' ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : '-';
        }
        
        return (
          <div className="flex items-center gap-1 text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-xs">{value.length} errors</span>
          </div>
        );
      },
    },
  ], []);

  const clearCompleted = useCallback(() => {
    setFiles(prev => prev.filter(f => f.status === 'processing' || f.status === 'validating'));
    trackInteraction('clear_completed', 'ClearButton');
  }, [trackInteraction]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <input {...getInputProps()} aria-label="Upload healthcare files" />
        
        <Upload className={`mx-auto w-12 h-12 mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
        
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {isDragActive ? 'Drop files here' : 'Upload Healthcare Files'}
        </h3>
        
        <p className="text-gray-600 mb-4">
          {isDragActive
            ? 'Release to start processing'
            : `Drag & drop files here, or click to select. Max ${maxFileSize}MB per file.`
          }
        </p>
        
        <div className="text-sm text-gray-500">
          <div className="mb-2">Supported formats:</div>
          <div className="flex flex-wrap justify-center gap-2">
            {Object.entries(SUPPORTED_FORMATS).map(([mime, description]) => (
              <span key={mime} className="px-2 py-1 bg-gray-100 rounded text-xs">
                {description}
              </span>
            ))}
          </div>
        </div>
        
        {isProcessing && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
            <div className="text-blue-600">
              <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mb-2" />
              Processing files...
            </div>
          </div>
        )}
      </div>

      {/* File Results Table */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h4 className="text-lg font-semibold text-gray-900">
              Processing Results ({files.length} files)
            </h4>
            
            <div className="flex items-center gap-2">
              {files.some(f => f.status === 'completed' || f.status === 'failed') && (
                <AnimatedButton
                  variant="secondary"
                  size="sm"
                  onClick={clearCompleted}
                >
                  Clear Completed
                </AnimatedButton>
              )}
            </div>
          </div>
          
          <VirtualizedTable
            data={files}
            columns={tableColumns}
            height={400}
            itemHeight={60}
            searchable={false}
            filterable={false}
            sortable={true}
            enableExport={true}
          />
        </div>
      )}
      
      {/* Performance Metrics (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-600">
          <h5 className="font-semibold mb-2">Performance Metrics</h5>
          <div className="grid grid-cols-2 gap-4">
            <div>Render Count: {metrics.renderCount}</div>
            <div>Avg Render Time: {metrics.averageRenderTime.toFixed(2)}ms</div>
            <div>Slow Renders: {metrics.slowRenders}</div>
            <div>Memory Usage: {metrics.memoryUsage?.toFixed(1)}MB</div>
          </div>
        </div>
      )}
    </div>
  );
});

HealthcareDataProcessor.displayName = 'HealthcareDataProcessor';
import React, { useState } from 'react';
import { clsx } from 'clsx';
import {
  Download,
  FileText,
  Database,
  Printer,
  Share2,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileJson,
  FileSpreadsheet,
  FileImage
} from 'lucide-react';
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import type { ApiResponse } from '@/types/api';
import type { FHIRBundle } from '@/types/healthcare';
import Button from '@/components/ui/Button';

interface ExportPanelProps {
  results: ApiResponse;
}

interface ExportFormat {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  fileExtension: string;
  supportedData: ('fhir' | 'metadata' | 'raw' | 'all')[];
}

const exportFormats: ExportFormat[] = [
  {
    id: 'json',
    name: 'JSON',
    description: 'Complete data in JSON format',
    icon: FileJson,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    fileExtension: 'json',
    supportedData: ['fhir', 'metadata', 'raw', 'all']
  },
  {
    id: 'csv',
    name: 'CSV',
    description: 'FHIR resources as spreadsheet',
    icon: FileSpreadsheet,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    fileExtension: 'csv',
    supportedData: ['fhir']
  },
  {
    id: 'pdf',
    name: 'PDF Report',
    description: 'Professional processing report',
    icon: FileText,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    fileExtension: 'pdf',
    supportedData: ['all']
  },
  {
    id: 'png',
    name: 'PNG Image',
    description: 'Visual summary as image',
    icon: FileImage,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    fileExtension: 'png',
    supportedData: ['all']
  }
];

interface ExportOption {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const exportOptions: ExportOption[] = [
  {
    id: 'fhir',
    name: 'FHIR Resources Only',
    description: 'Structured healthcare data resources',
    icon: Database
  },
  {
    id: 'metadata',
    name: 'Metadata Only',
    description: 'Processing metadata and performance metrics',
    icon: FileText
  },
  {
    id: 'raw',
    name: 'Raw Data Only',
    description: 'Original file content',
    icon: FileText
  },
  {
    id: 'all',
    name: 'Complete Results',
    description: 'All data including FHIR, metadata, and raw data',
    icon: Share2
  }
];

const ExportPanel: React.FC<ExportPanelProps> = ({ results }) => {
  const [selectedFormat, setSelectedFormat] = useState<string>('json');
  const [selectedData, setSelectedData] = useState<string>('all');
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  const bundle = results.data as FHIRBundle;
  const metadata = results.metadata;

  const formatFileName = (format: string, data: string): string => {
    const timestamp = new Date().toISOString().split('T')[0];
    const dataType = data === 'all' ? 'complete' : data;
    return `healthcare-preauth-${dataType}-${timestamp}.${format}`;
  };

  const prepareData = (dataType: string) => {
    switch (dataType) {
      case 'fhir':
        return {
          resourceType: bundle?.resourceType,
          id: bundle?.id,
          meta: bundle?.meta,
          type: bundle?.type,
          timestamp: bundle?.timestamp,
          total: bundle?.total,
          authorization_id: bundle?.authorization_id,
          sender: bundle?.sender,
          receiver: bundle?.receiver,
          fhir_resources: bundle?.fhir_resources
        };
      case 'metadata':
        return metadata;
      case 'raw':
        return bundle?.raw_data;
      case 'all':
      default:
        return results;
    }
  };

  const convertToCSV = (): string => {
    if (!bundle?.fhir_resources) {
      throw new Error('No FHIR resources available for CSV export');
    }

    const csvRows: string[] = [];

    // Add bundle info header
    csvRows.push('Bundle Information');
    csvRows.push(`Authorization ID,${bundle.authorization_id || 'N/A'}`);
    csvRows.push(`Sender,${bundle.sender || 'N/A'}`);
    csvRows.push(`Receiver,${bundle.receiver || 'N/A'}`);
    csvRows.push(`Total Resources,${bundle.total || 0}`);
    csvRows.push('');

    // Process each resource type
    Object.entries(bundle.fhir_resources).forEach(([resourceType, resources]) => {
      csvRows.push(`${resourceType} Resources`);

      const resourceArray = Object.values(resources as Record<string, any>);
      if (resourceArray.length === 0) return;

      // Get all unique keys from all resources of this type
      const allKeys = new Set<string>();
      resourceArray.forEach(resource => {
        Object.keys(resource).forEach(key => allKeys.add(key));
      });

      // Create header row
      const headers = Array.from(allKeys);
      csvRows.push(headers.join(','));

      // Create data rows
      resourceArray.forEach(resource => {
        const row = headers.map(header => {
          const value = resource[header];
          if (value === undefined || value === null) return '';
          if (typeof value === 'object') return JSON.stringify(value);
          return String(value).replace(/,/g, ';'); // Replace commas to avoid CSV issues
        });
        csvRows.push(row.join(','));
      });

      csvRows.push(''); // Empty row between resource types
    });

    return csvRows.join('\n');
  };

  const generatePDFReport = async (): Promise<Blob> => {
    const pdf = new jsPDF();
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    let yPosition = 20;

    // Title
    pdf.setFontSize(20);
    pdf.setFont('helvetica', 'bold');
    pdf.text('Healthcare AI Platform Processing Report', pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 20;

    // Bundle Information
    pdf.setFontSize(16);
    pdf.text('Bundle Information', 20, yPosition);
    yPosition += 10;

    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'normal');
    const bundleInfo = [
      `Authorization ID: ${bundle?.authorization_id || 'N/A'}`,
      `Sender: ${bundle?.sender || 'N/A'}`,
      `Receiver: ${bundle?.receiver || 'N/A'}`,
      `Total Resources: ${bundle?.total || 0}`,
      `Processing Time: ${metadata?.processing_time_seconds?.toFixed(2) || 0}s`,
      `File Size: ${metadata?.file_size_bytes ? (metadata.file_size_bytes / 1024).toFixed(1) + ' KB' : 'N/A'}`,
      `Format: ${metadata?.format || 'Unknown'}`
    ];

    bundleInfo.forEach(info => {
      pdf.text(info, 20, yPosition);
      yPosition += 8;
    });

    yPosition += 10;

    // Resource Types
    if (bundle?.fhir_resources) {
      pdf.setFontSize(16);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Resource Summary', 20, yPosition);
      yPosition += 10;

      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'normal');

      Object.entries(bundle.fhir_resources).forEach(([resourceType, resources]) => {
        const count = Object.keys(resources as Record<string, any>).length;
        pdf.text(`${resourceType}: ${count} items`, 20, yPosition);
        yPosition += 8;

        if (yPosition > pageHeight - 30) {
          pdf.addPage();
          yPosition = 20;
        }
      });
    }

    // Metadata
    if (metadata) {
      yPosition += 10;
      pdf.setFontSize(16);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Processing Metadata', 20, yPosition);
      yPosition += 10;

      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'normal');
      const metadataInfo = [
        `Filename: ${metadata.filename}`,
        `API Version: ${metadata.api_version}`,
        `Processor Version: ${metadata.processor_version}`,
        `Data Quality Score: ${metadata?.data_quality_score ? (metadata.data_quality_score * 100).toFixed(1) + '%' : 'N/A'}`
      ];

      metadataInfo.forEach(info => {
        pdf.text(info, 20, yPosition);
        yPosition += 8;

        if (yPosition > pageHeight - 30) {
          pdf.addPage();
          yPosition = 20;
        }
      });
    }

    return new Promise((resolve) => {
      resolve(new Blob([pdf.output('blob')], { type: 'application/pdf' }));
    });
  };

  const captureAsPNG = async (): Promise<Blob> => {
    // Create a temporary div with the summary content
    const summaryDiv = document.createElement('div');
    summaryDiv.style.cssText = `
      width: 800px;
      padding: 40px;
      background: white;
      font-family: Arial, sans-serif;
      position: absolute;
      left: -9999px;
      top: 0;
    `;

    summaryDiv.innerHTML = `
      <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #1f2937; margin-bottom: 10px;">Healthcare AI Platform Processing Report</h1>
        <p style="color: #6b7280; margin: 0;">Generated on ${new Date().toLocaleDateString()}</p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
          <h3 style="color: #1f2937; margin-top: 0;">Bundle Information</h3>
          <p><strong>Authorization ID:</strong> ${bundle?.authorization_id || 'N/A'}</p>
          <p><strong>Total Resources:</strong> ${bundle?.total || 0}</p>
          <p><strong>Processing Time:</strong> ${metadata?.processing_time_seconds?.toFixed(2) || 0}s</p>
        </div>

        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
          <h3 style="color: #1f2937; margin-top: 0;">File Information</h3>
          <p><strong>Filename:</strong> ${metadata?.filename || 'N/A'}</p>
          <p><strong>Size:</strong> ${metadata?.file_size_bytes ? (metadata.file_size_bytes / 1024).toFixed(1) + ' KB' : 'N/A'}</p>
          <p><strong>Format:</strong> ${metadata?.format || 'Unknown'}</p>
        </div>
      </div>

      ${bundle?.fhir_resources ? `
        <div style="background: #f9fafb; padding: 20px; border-radius: 8px;">
          <h3 style="color: #1f2937; margin-top: 0;">Resource Types</h3>
          ${Object.entries(bundle.fhir_resources).map(([type, resources]) =>
            `<p><strong>${type}:</strong> ${Object.keys(resources as Record<string, any>).length} items</p>`
          ).join('')}
        </div>
      ` : ''}
    `;

    document.body.appendChild(summaryDiv);

    const canvas = await html2canvas(summaryDiv, {
      backgroundColor: '#ffffff',
      scale: 2,
      logging: false
    });

    document.body.removeChild(summaryDiv);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob!);
      }, 'image/png');
    });
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportStatus({ type: null, message: '' });

    try {
      const data = prepareData(selectedData);
      const fileName = formatFileName(selectedFormat, selectedData);

      let blob: Blob;

      switch (selectedFormat) {
        case 'json':
          blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
          break;

        case 'csv':
          if (selectedData !== 'fhir') {
            throw new Error('CSV export is only available for FHIR resources');
          }
          const csvContent = convertToCSV(data);
          blob = new Blob([csvContent], { type: 'text/csv' });
          break;

        case 'pdf':
          blob = await generatePDFReport();
          break;

        case 'png':
          blob = await captureAsPNG();
          break;

        default:
          throw new Error('Unsupported export format');
      }

      saveAs(blob, fileName);

      setExportStatus({
        type: 'success',
        message: `Successfully exported ${fileName}`
      });

    } catch (error) {
      console.error('Export failed:', error);
      setExportStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Export failed'
      });
    } finally {
      setIsExporting(false);
    }
  };

  const selectedFormatConfig = exportFormats.find(f => f.id === selectedFormat);
  const selectedDataConfig = exportOptions.find(o => o.id === selectedData);
  const isValidCombination = selectedFormatConfig?.supportedData.includes(selectedData as any);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Export Options</h3>
        <p className="text-sm text-gray-600">
          Choose your preferred format and data selection for export.
        </p>
      </div>

      {/* Format Selection */}
      <div>
        <h4 className="text-md font-semibold text-gray-900 mb-3">Export Format</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {exportFormats.map((format) => (
            <div
              key={format.id}
              className={clsx(
                'p-4 rounded-lg border cursor-pointer transition-all hover:shadow-sm',
                selectedFormat === format.id
                  ? `${format.bgColor} ${format.borderColor} ring-2 ring-blue-500`
                  : 'bg-white border-gray-200 hover:border-gray-300'
              )}
              onClick={() => setSelectedFormat(format.id)}
            >
              <div className="flex items-center space-x-3 mb-2">
                <format.icon className={clsx('w-6 h-6',
                  selectedFormat === format.id ? format.color : 'text-gray-400'
                )} />
                <h5 className="font-semibold text-gray-900">{format.name}</h5>
              </div>
              <p className="text-sm text-gray-600">{format.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Data Selection */}
      <div>
        <h4 className="text-md font-semibold text-gray-900 mb-3">Data Selection</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exportOptions.map((option) => {
            const isSupported = selectedFormatConfig?.supportedData.includes(option.id as any);

            return (
              <div
                key={option.id}
                className={clsx(
                  'p-4 rounded-lg border cursor-pointer transition-all',
                  !isSupported && 'opacity-50 cursor-not-allowed',
                  selectedData === option.id && isSupported
                    ? 'bg-blue-50 border-blue-200 ring-2 ring-blue-500'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                )}
                onClick={() => isSupported && setSelectedData(option.id)}
              >
                <div className="flex items-center space-x-3 mb-2">
                  <option.icon className={clsx('w-5 h-5',
                    selectedData === option.id && isSupported ? 'text-blue-600' : 'text-gray-400'
                  )} />
                  <h5 className="font-semibold text-gray-900">{option.name}</h5>
                  {!isSupported && (
                    <span className="text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded">
                      Not supported
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{option.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Export Preview */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-2">Export Preview</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <p><strong>Format:</strong> {selectedFormatConfig?.name || 'Unknown'}</p>
          <p><strong>Data:</strong> {selectedDataConfig?.name || 'Unknown'}</p>
          <p><strong>Filename:</strong> {formatFileName(selectedFormat, selectedData)}</p>
          {!isValidCombination && (
            <div className="flex items-center space-x-2 mt-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span>This combination is not supported</span>
            </div>
          )}
        </div>
      </div>

      {/* Export Status */}
      {exportStatus.type && (
        <div className={clsx(
          'flex items-center space-x-2 p-4 rounded-lg',
          exportStatus.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        )}>
          {exportStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{exportStatus.message}</span>
        </div>
      )}

      {/* Export Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          {isValidCombination ? (
            'Ready to export'
          ) : (
            'Please select a valid format and data combination'
          )}
        </div>

        <div className="flex space-x-3">
          <Button
            variant="secondary"
            onClick={() => window.print()}
            disabled={isExporting}
          >
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>

          <Button
            variant="primary"
            onClick={handleExport}
            disabled={isExporting || !isValidCombination}
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExportPanel;
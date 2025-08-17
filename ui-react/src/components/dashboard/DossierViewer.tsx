import React, { useState, useCallback, useEffect } from 'react';
import { clsx } from 'clsx';
import {
  X,
  Maximize2,
  Minimize2,
  Download,
  Printer,
  Share2,
  Copy,
  FileText,
  ExternalLink,
  RefreshCw,
  Eye,
  FileDown,
  Mail
} from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { useToast } from '@/contexts/ToastContext';
import type { DossierResponse } from '@/types/api';

interface DossierViewerProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: string;
  dossierData?: {
    html_content: string;
    pdf_url?: string;
    executive_summary: string;
  };
}

const DossierViewer: React.FC<DossierViewerProps> = ({
  isOpen,
  onClose,
  analysisId,
  dossierData: initialDossierData
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [dossierData, setDossierData] = useState(initialDossierData);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'summary' | 'full'>('summary');
  
  const { showToast } = useToast();

  // Keyboard shortcuts
  useHotkeys('escape', onClose, { enabled: isOpen });
  useHotkeys('f11', () => setIsFullscreen(!isFullscreen), { enabled: isOpen });
  useHotkeys('ctrl+p', (e) => {
    e.preventDefault();
    handlePrint();
  }, { enabled: isOpen });

  // Fetch dossier data if not provided initially
  useEffect(() => {
    if (isOpen && !dossierData) {
      fetchDossierData();
    }
  }, [isOpen, analysisId]);

  const fetchDossierData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/dossier/${analysisId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch dossier: ${response.status}`);
      }
      
      const result: DossierResponse = await response.json();
      
      if (result.success) {
        setDossierData({
          html_content: result.html_content,
          pdf_url: result.pdf_url,
          executive_summary: result.executive_summary
        });
      } else {
        throw new Error(result.error || 'Failed to load dossier');
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dossier';
      setError(errorMessage);
      showToast({
        type: 'error',
        title: 'Dossier Load Failed',
        message: errorMessage
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = useCallback(() => {
    fetchDossierData();
  }, [analysisId]);

  const handleDownloadPDF = useCallback(async () => {
    if (dossierData?.pdf_url) {
      try {
        const link = document.createElement('a');
        link.href = dossierData.pdf_url;
        link.download = `dossier-${analysisId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast({
          type: 'success',
          title: 'Download Started',
          message: 'PDF dossier download has begun'
        });
      } catch (err) {
        showToast({
          type: 'error',
          title: 'Download Failed',
          message: 'Failed to download PDF dossier'
        });
      }
    } else {
      // Generate PDF from HTML content
      try {
        const response = await fetch(`/api/dossier/${analysisId}/pdf`, {
          method: 'POST'
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `dossier-${analysisId}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          showToast({
            type: 'success',
            title: 'PDF Generated',
            message: 'PDF dossier has been generated and downloaded'
          });
        } else {
          throw new Error('PDF generation failed');
        }
      } catch (err) {
        showToast({
          type: 'error',
          title: 'PDF Generation Failed',
          message: 'Failed to generate PDF from dossier content'
        });
      }
    }
  }, [dossierData, analysisId, showToast]);

  const handlePrint = useCallback(() => {
    if (dossierData?.html_content) {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head>
              <title>Medical Dossier - ${analysisId}</title>
              <style>
                @media print {
                  body { font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.5; }
                  h1, h2, h3 { page-break-after: avoid; }
                  table { page-break-inside: avoid; }
                  .no-print { display: none; }
                }
                body { max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
                .section { margin-bottom: 20px; }
                .signature-line { border-top: 1px solid #333; width: 200px; margin-top: 30px; }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>Medical Pre-Authorization Dossier</h1>
                <p>Analysis ID: ${analysisId}</p>
                <p>Generated: ${new Date().toLocaleDateString()}</p>
              </div>
              ${dossierData.html_content}
              <div class="signature-line">
                <p>Medical Director Signature</p>
              </div>
            </body>
          </html>
        `);
        printWindow.document.close();
        printWindow.print();
      }
    }
  }, [dossierData, analysisId]);

  const handleCopyContent = useCallback(async () => {
    if (activeView === 'summary' && dossierData?.executive_summary) {
      try {
        await navigator.clipboard.writeText(dossierData.executive_summary);
        showToast({
          type: 'success',
          title: 'Copied',
          message: 'Executive summary copied to clipboard'
        });
      } catch (err) {
        showToast({
          type: 'error',
          title: 'Copy Failed',
          message: 'Failed to copy content to clipboard'
        });
      }
    } else if (activeView === 'full' && dossierData?.html_content) {
      try {
        // Extract text content from HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = dossierData.html_content;
        const textContent = tempDiv.textContent || tempDiv.innerText || '';
        await navigator.clipboard.writeText(textContent);
        showToast({
          type: 'success',
          title: 'Copied',
          message: 'Dossier content copied to clipboard'
        });
      } catch (err) {
        showToast({
          type: 'error',
          title: 'Copy Failed',
          message: 'Failed to copy content to clipboard'
        });
      }
    }
  }, [activeView, dossierData, showToast]);

  const handleShare = useCallback(async () => {
    if (navigator.share && dossierData) {
      try {
        await navigator.share({
          title: `Medical Dossier - ${analysisId}`,
          text: dossierData.executive_summary,
          url: window.location.href
        });
      } catch (err) {
        // Fallback to copy URL
        try {
          await navigator.clipboard.writeText(window.location.href);
          showToast({
            type: 'success',
            title: 'URL Copied',
            message: 'Dossier URL copied to clipboard'
          });
        } catch (copyErr) {
          showToast({
            type: 'error',
            title: 'Share Failed',
            message: 'Failed to share dossier'
          });
        }
      }
    }
  }, [analysisId, dossierData, showToast]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div
        className={clsx(
          'bg-white rounded-lg shadow-2xl flex flex-col',
          isFullscreen
            ? 'w-full h-full rounded-none'
            : 'w-full max-w-6xl h-[90vh] mx-4'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center space-x-4">
            <FileText className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Medical Pre-Authorization Dossier
              </h2>
              <p className="text-sm text-gray-600">Analysis ID: {analysisId}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* View Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveView('summary')}
                className={clsx(
                  'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                  activeView === 'summary'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                Summary
              </button>
              <button
                onClick={() => setActiveView('full')}
                className={clsx(
                  'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                  activeView === 'full'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                Full Report
              </button>
            </div>

            {/* Action Buttons */}
            <Button
              variant="tertiary"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              title="Refresh Dossier"
            >
              <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={handleCopyContent}
              title="Copy Content"
            >
              <Copy className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={handlePrint}
              title="Print (Ctrl+P)"
            >
              <Printer className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={handleDownloadPDF}
              title="Download PDF"
            >
              <Download className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={handleShare}
              title="Share Dossier"
            >
              <Share2 className="w-4 h-4" />
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title="Toggle Fullscreen (F11)"
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>

            <Button
              variant="tertiary"
              size="sm"
              onClick={onClose}
              title="Close (Escape)"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Loading dossier...</p>
              </div>
            </div>
          ) : error ? (
            <div className="h-full flex items-center justify-center">
              <Card className="p-8 text-center max-w-md">
                <FileText className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Failed to Load Dossier
                </h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <Button onClick={handleRefresh} variant="primary">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </Card>
            </div>
          ) : !dossierData ? (
            <div className="h-full flex items-center justify-center">
              <Card className="p-8 text-center max-w-md">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No Dossier Available
                </h3>
                <p className="text-gray-600">
                  The dossier for this analysis is not yet available.
                </p>
              </Card>
            </div>
          ) : (
            <div className="h-full overflow-y-auto">
              {activeView === 'summary' ? (
                <div className="p-6">
                  <Card>
                    <div className="p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Executive Summary
                      </h3>
                      <div className="prose max-w-none">
                        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                          {dossierData.executive_summary}
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              ) : (
                <div className="p-6">
                  <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
                    <div 
                      className="p-8 prose prose-blue max-w-none"
                      dangerouslySetInnerHTML={{ __html: dossierData.html_content }}
                      style={{
                        fontFamily: '"Times New Roman", serif',
                        lineHeight: '1.6'
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50 text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>Professional medical dossier for insurance review</span>
            {dossierData?.pdf_url && (
              <a
                href={dossierData.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 flex items-center"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                View PDF
              </a>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span>Generated: {new Date().toLocaleDateString()}</span>
            <span>•</span>
            <span>Press Esc to close</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DossierViewer;
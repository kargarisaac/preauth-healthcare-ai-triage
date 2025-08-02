import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  Building,
  FileText,
  Clock,
  DollarSign,
  Tag,
  Download,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Stethoscope,
  Pill,
  FileCheck,
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useRequestHistory } from '@/hooks/dashboard/useRequestHistory';
import type {
  RequestHistoryItem,
  RequestStatusHistory,
  RequestAuditTrail,
  RequestDocument,
} from '@/types/requests';

// Status configuration
const STATUS_CONFIGS = {
  approved: { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100', label: 'Approved' },
  pending: { icon: Clock, color: 'text-yellow-600', bgColor: 'bg-yellow-100', label: 'Pending' },
  denied: { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-100', label: 'Denied' },
  under_review: { icon: AlertTriangle, color: 'text-blue-600', bgColor: 'bg-blue-100', label: 'Under Review' },
  cancelled: { icon: XCircle, color: 'text-gray-600', bgColor: 'bg-gray-100', label: 'Cancelled' },
  expired: { icon: Clock, color: 'text-gray-600', bgColor: 'bg-gray-100', label: 'Expired' },
} as const;

interface RequestDetailsProps {
  requestId: string;
  compact?: boolean;
  onClose?: () => void;
}

interface TabPanelProps {
  children: React.ReactNode;
  isActive: boolean;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, isActive }) => {
  if (!isActive) return null;
  return <div>{children}</div>;
};

interface StatusTimelineProps {
  statusHistory: RequestStatusHistory[];
}

const StatusTimeline: React.FC<StatusTimelineProps> = ({ statusHistory }) => {
  const sortedHistory = [...statusHistory].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <div className="space-y-4">
      {sortedHistory.map((entry, index) => {
        const config = STATUS_CONFIGS[entry.status];
        const StatusIcon = config.icon;
        const isFirst = index === 0;

        return (
          <div key={entry.id} className="flex items-start">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${config.bgColor}`}>
              <StatusIcon className={`w-4 h-4 ${config.color}`} />
            </div>
            <div className="ml-4 flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className={`text-sm font-medium ${isFirst ? 'text-gray-900' : 'text-gray-600'}`}>
                  Status changed to {config.label}
                </p>
                <time className="text-xs text-gray-500">
                  {new Date(entry.timestamp).toLocaleString()}
                </time>
              </div>
              <p className="text-sm text-gray-600">by {entry.updatedBy}</p>
              {entry.reason && (
                <p className="text-sm text-gray-500 mt-1">Reason: {entry.reason}</p>
              )}
              {entry.notes && (
                <p className="text-sm text-gray-500 mt-1">Notes: {entry.notes}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

interface DocumentListProps {
  documents: RequestDocument[];
}

const DocumentList: React.FC<DocumentListProps> = ({ documents }) => {
  const getDocumentIcon = (type: RequestDocument['type']) => {
    switch (type) {
      case 'medical_report':
        return FileCheck;
      case 'prescription':
        return Pill;
      case 'lab_result':
        return Activity;
      case 'imaging':
        return Eye;
      case 'authorization_form':
        return FileText;
      default:
        return FileText;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-3">
      {documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-2" />
          <p>No documents attached</p>
        </div>
      ) : (
        documents.map((document) => {
          const Icon = getDocumentIcon(document.type);

          return (
            <div key={document.id} className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <Icon className="w-6 h-6 text-blue-600 mr-3" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {document.name}
                </p>
                <p className="text-xs text-gray-500">
                  {document.type.replace('_', ' ')} • {formatFileSize(document.size)} •
                  Uploaded {new Date(document.uploadedAt).toLocaleDateString()}
                </p>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => window.open(document.url, '_blank')}
                  className="p-2"
                >
                  <Eye className="w-4 h-4" />
                </Button>
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = document.url;
                    link.download = document.name;
                    link.click();
                  }}
                  className="p-2"
                >
                  <Download className="w-4 h-4" />
                </Button>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
};

interface AuditTrailProps {
  auditTrail: RequestAuditTrail[];
}

const AuditTrail: React.FC<AuditTrailProps> = ({ auditTrail }) => {
  const sortedTrail = [...auditTrail].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <div className="space-y-3">
      {sortedTrail.map((entry) => (
        <div key={entry.id} className="border-l-2 border-gray-200 pl-4 py-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-900">{entry.action}</p>
            <time className="text-xs text-gray-500">
              {new Date(entry.timestamp).toLocaleString()}
            </time>
          </div>
          <p className="text-sm text-gray-600">by {entry.performedBy}</p>
          {entry.details && Object.keys(entry.details).length > 0 && (
            <div className="mt-2 text-xs text-gray-500">
              <details>
                <summary className="cursor-pointer">View details</summary>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                  {JSON.stringify(entry.details, null, 2)}
                </pre>
              </details>
            </div>
          )}
          {entry.ipAddress && (
            <p className="text-xs text-gray-400">IP: {entry.ipAddress}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export function RequestDetails({ requestId, compact = false, onClose }: RequestDetailsProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [requestData, setRequestData] = useState<{
    request: RequestHistoryItem;
    statusHistory: RequestStatusHistory[];
    auditTrail: RequestAuditTrail[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { fetchRequestDetails } = useRequestHistory();

  useEffect(() => {
    const loadRequestDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchRequestDetails(requestId);
        setRequestData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load request details');
      } finally {
        setIsLoading(false);
      }
    };

    loadRequestDetails();
  }, [requestId, fetchRequestDetails]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Request</h3>
        <p className="text-gray-500">{error}</p>
      </div>
    );
  }

  if (!requestData) {
    return (
      <div className="text-center py-8">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Request Not Found</h3>
        <p className="text-gray-500">The requested details could not be found.</p>
      </div>
    );
  }

  const { request, statusHistory, auditTrail } = requestData;
  const statusConfig = STATUS_CONFIGS[request.status];
  const StatusIcon = statusConfig.icon;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FileText },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'documents', label: 'Documents', icon: FileText, count: request.documents.length },
    { id: 'audit', label: 'Audit Trail', icon: Activity },
  ];

  const content = (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          <div className={`p-3 rounded-full ${statusConfig.bgColor}`}>
            <StatusIcon className={`h-6 w-6 ${statusConfig.color}`} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Request #{request.requestNumber}
            </h2>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Submitted {new Date(request.submissionDate).toLocaleDateString()}</span>
              <span>•</span>
              <span className={statusConfig.color}>{statusConfig.label}</span>
              <span>•</span>
              <span>{request.priority} priority</span>
            </div>
          </div>
        </div>
        {onClose && (
          <Button variant="tertiary" onClick={onClose} className="p-2">
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>

      {!compact && (
        <>
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {tab.label}
                    {tab.count !== undefined && tab.count > 0 && (
                      <span className="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                        {tab.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="min-h-[400px]">
            <TabPanel isActive={activeTab === 'overview'}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Member Information */}
                <Card className="p-4">
                  <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                    <User className="w-5 h-5 mr-2" />
                    Member Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Name</label>
                      <p className="text-gray-900">{request.memberName}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Member ID</label>
                      <p className="text-gray-900">{request.memberId}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Emirates ID</label>
                      <p className="text-gray-900">{request.emiratesId}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Date of Birth</label>
                      <p className="text-gray-900">{new Date(request.dateOfBirth).toLocaleDateString()}</p>
                    </div>
                  </div>
                </Card>

                {/* Provider Information */}
                <Card className="p-4">
                  <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                    <Building className="w-5 h-5 mr-2" />
                    Provider Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Provider</label>
                      <p className="text-gray-900">{request.providerName}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Provider ID</label>
                      <p className="text-gray-900">{request.providerId}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Type</label>
                      <p className="text-gray-900">{request.providerType}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Facility</label>
                      <p className="text-gray-900">{request.facility}</p>
                    </div>
                  </div>
                </Card>

                {/* Clinical Information */}
                <Card className="p-4">
                  <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                    <Stethoscope className="w-5 h-5 mr-2" />
                    Clinical Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Diagnosis</label>
                      <p className="text-gray-900">{request.diagnosis}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Diagnosis Codes</label>
                      <p className="text-gray-900">{request.diagnosisCodes.join(', ')}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Procedure</label>
                      <p className="text-gray-900">{request.procedure}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Procedure Codes</label>
                      <p className="text-gray-900">{request.procedureCodes.join(', ')}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-500">Service Description</label>
                      <p className="text-gray-900">{request.serviceDescription}</p>
                    </div>
                  </div>
                </Card>

                {/* Financial Information */}
                <Card className="p-4">
                  <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
                    <DollarSign className="w-5 h-5 mr-2" />
                    Financial Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500">Requested Amount</label>
                      <p className="text-gray-900 text-lg font-semibold">
                        {new Intl.NumberFormat('en-AE', {
                          style: 'currency',
                          currency: request.currency,
                        }).format(request.requestedAmount)}
                      </p>
                    </div>
                    {request.approvedAmount && (
                      <div>
                        <label className="text-sm font-medium text-gray-500">Approved Amount</label>
                        <p className="text-gray-900 text-lg font-semibold">
                          {new Intl.NumberFormat('en-AE', {
                            style: 'currency',
                            currency: request.currency,
                          }).format(request.approvedAmount)}
                        </p>
                      </div>
                    )}
                  </div>
                </Card>
              </div>

              {/* Additional Information */}
              {(request.tags.length > 0 || request.notes) && (
                <div className="space-y-4">
                  {request.tags.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-500 mb-2 block">Tags</label>
                      <div className="flex flex-wrap gap-2">
                        {request.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            <Tag className="w-3 h-3 mr-1" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {request.notes && (
                    <div>
                      <label className="text-sm font-medium text-gray-500 mb-2 block">Notes</label>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-gray-900 whitespace-pre-wrap">{request.notes}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabPanel>

            <TabPanel isActive={activeTab === 'timeline'}>
              <Card className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Status Timeline</h3>
                <StatusTimeline statusHistory={statusHistory} />
              </Card>
            </TabPanel>

            <TabPanel isActive={activeTab === 'documents'}>
              <Card className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Attached Documents</h3>
                <DocumentList documents={request.documents} />
              </Card>
            </TabPanel>

            <TabPanel isActive={activeTab === 'audit'}>
              <Card className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Audit Trail</h3>
                <AuditTrail auditTrail={auditTrail} />
              </Card>
            </TabPanel>
          </div>
        </>
      )}

      {/* Compact view */}
      {compact && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-500">Member</label>
            <p className="text-gray-900">{request.memberName}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Provider</label>
            <p className="text-gray-900">{request.providerName}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Amount</label>
            <p className="text-gray-900">
              {new Intl.NumberFormat('en-AE', {
                style: 'currency',
                currency: request.currency,
              }).format(request.requestedAmount)}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Service</label>
            <p className="text-gray-900">{request.serviceDescription}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Diagnosis</label>
            <p className="text-gray-900">{request.diagnosis}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-500">Processing Time</label>
            <p className="text-gray-900">
              {request.processingTime ? `${request.processingTime}s` : 'N/A'}
            </p>
          </div>
        </div>
      )}
    </div>
  );

  // Render as modal or inline content
  if (onClose && !compact) {
    return (
      <Modal isOpen={true} onClose={onClose} title="" size="xl">
        <div className="max-h-[80vh] overflow-y-auto">
          {content}
        </div>
      </Modal>
    );
  }

  return content;
}

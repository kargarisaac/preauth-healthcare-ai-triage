import React, { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  UserCheck,
  Tag,
  Download,
  Trash2,
  AlertTriangle,
  Users,
  X,
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useRequestHistory } from '@/hooks/dashboard/useRequestHistory';
import { useToast } from '@/contexts/ToastContext';
import type { BulkAction, BulkActionType, RequestExportFormat } from '@/types/requests';

const BULK_ACTIONS: BulkAction[] = [
  {
    type: 'approve',
    label: 'Approve Selected',
    icon: 'check-circle',
    requiresConfirmation: true,
  },
  {
    type: 'deny',
    label: 'Deny Selected',
    icon: 'x-circle',
    requiresConfirmation: true,
    isDestructive: true,
  },
  {
    type: 'assign',
    label: 'Assign To',
    icon: 'user-check',
    requiresConfirmation: false,
  },
  {
    type: 'tag',
    label: 'Add Tags',
    icon: 'tag',
    requiresConfirmation: false,
  },
  {
    type: 'export',
    label: 'Export Selected',
    icon: 'download',
    requiresConfirmation: false,
  },
  {
    type: 'delete',
    label: 'Delete Selected',
    icon: 'trash-2',
    requiresConfirmation: true,
    isDestructive: true,
  },
];

interface BulkActionsProps {
  selectedCount: number;
  selectedIds: string[];
  onClearSelection: () => void;
}

interface BulkActionModalProps {
  isOpen: boolean;
  action: BulkAction | null;
  selectedCount: number;
  selectedIds: string[];
  onClose: () => void;
  onConfirm: (actionType: BulkActionType, data?: Record<string, any>) => void;
}

const BulkActionModal: React.FC<BulkActionModalProps> = ({
  isOpen,
  action,
  selectedCount,
  selectedIds: _selectedIds,
  onClose,
  onConfirm,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});

  if (!action) return null;

  const handleConfirm = async () => {
    setIsProcessing(true);
    try {
      await onConfirm(action.type, formData);
      onClose();
    } catch (error) {
      // Error handling is done in the parent component
    } finally {
      setIsProcessing(false);
    }
  };

  const getModalContent = () => {
    switch (action.type) {
      case 'approve':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Approve Requests</h3>
                <p className="text-gray-500">
                  You are about to approve {selectedCount} request{selectedCount > 1 ? 's' : ''}.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Approval Notes (optional)
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="Add any notes about this approval..."
              />
            </div>
          </div>
        );

      case 'deny':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <XCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Deny Requests</h3>
                <p className="text-gray-500">
                  You are about to deny {selectedCount} request{selectedCount > 1 ? 's' : ''}.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Denial Reason *
              </label>
              <select
                value={formData.reason || ''}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                required
              >
                <option value="">Select a reason</option>
                <option value="insufficient_documentation">Insufficient Documentation</option>
                <option value="not_covered">Service Not Covered</option>
                <option value="duplicate_request">Duplicate Request</option>
                <option value="medical_necessity">Medical Necessity Not Met</option>
                <option value="expired_eligibility">Expired Eligibility</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Add any additional notes..."
              />
            </div>
          </div>
        );

      case 'assign':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <UserCheck className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Assign Requests</h3>
                <p className="text-gray-500">
                  Assign {selectedCount} request{selectedCount > 1 ? 's' : ''} to a team member.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assign To *
              </label>
              <select
                value={formData.assignTo || ''}
                onChange={(e) => setFormData({ ...formData, assignTo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select team member</option>
                <option value="sarah.ahmed">Dr. Sarah Ahmed</option>
                <option value="mohammed.hassan">Dr. Mohammed Hassan</option>
                <option value="fatima.ali">Fatima Ali (Senior Reviewer)</option>
                <option value="omar.khalil">Omar Khalil (Claims Specialist)</option>
                <option value="aisha.ibrahim">Aisha Ibrahim (Medical Review)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority Level
              </label>
              <select
                value={formData.priority || 'medium'}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Assignment Notes
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Add any notes for the assignee..."
              />
            </div>
          </div>
        );

      case 'tag':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <Tag className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Add Tags</h3>
                <p className="text-gray-500">
                  Add tags to {selectedCount} request{selectedCount > 1 ? 's' : ''}.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={formData.tags || ''}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="urgent, follow-up, complex-case"
              />
              <p className="text-xs text-gray-500 mt-1">
                Separate multiple tags with commas
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Common Tags
              </label>
              <div className="flex flex-wrap gap-2">
                {['urgent', 'follow-up', 'complex-case', 'high-value', 'review-required', 'expedite'].map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => {
                      const currentTags = formData.tags || '';
                      const tagsArray = currentTags.split(',').map((t: string) => t.trim()).filter(Boolean);
                      if (!tagsArray.includes(tag)) {
                        tagsArray.push(tag);
                        setFormData({ ...formData, tags: tagsArray.join(', ') });
                      }
                    }}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 'export':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <Download className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Export Requests</h3>
                <p className="text-gray-500">
                  Export {selectedCount} request{selectedCount > 1 ? 's' : ''} to file.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Export Format
              </label>
              <select
                value={formData.format || 'csv'}
                onChange={(e) => setFormData({ ...formData, format: e.target.value as RequestExportFormat })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="csv">CSV (Comma Separated Values)</option>
                <option value="excel">Excel Spreadsheet</option>
                <option value="pdf">PDF Report</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Include Columns
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {[
                  'requestNumber',
                  'memberName',
                  'providerName',
                  'status',
                  'amount',
                  'submissionDate',
                  'diagnosis',
                  'procedure',
                  'notes'
                ].map((column) => (
                  <label key={column} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={(formData.columns || []).includes(column)}
                      onChange={(e) => {
                        const columns = formData.columns || [];
                        if (e.target.checked) {
                          setFormData({ ...formData, columns: [...columns, column] });
                        } else {
                          setFormData({ ...formData, columns: columns.filter((c: any) => c !== column) });
                        }
                      }}
                      className="mr-2 h-4 w-4 text-green-600 rounded border-gray-300 focus:ring-green-500"
                    />
                    <span className="text-sm text-gray-700 capitalize">
                      {column.replace(/([A-Z])/g, ' $1').toLowerCase()}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 'delete':
        return (
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Delete Requests</h3>
                <p className="text-gray-500">
                  You are about to permanently delete {selectedCount} request{selectedCount > 1 ? 's' : ''}.
                </p>
              </div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                <p className="text-sm text-red-800">
                  <strong>This action cannot be undone.</strong> All request data, documents, and history will be permanently removed.
                </p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Deletion Reason *
              </label>
              <select
                value={formData.reason || ''}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                required
              >
                <option value="">Select a reason</option>
                <option value="duplicate">Duplicate Request</option>
                <option value="test_data">Test Data</option>
                <option value="data_correction">Data Correction</option>
                <option value="compliance">Compliance Requirements</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title=""
      size="md"
    >
      <div className="space-y-6">
        {getModalContent()}

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isProcessing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isProcessing}
            className={action.isDestructive ? 'bg-red-600 hover:bg-red-700' : ''}
          >
            {isProcessing ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Processing...
              </>
            ) : (
              action.label
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export function BulkActions({ selectedCount, selectedIds, onClearSelection }: BulkActionsProps) {
  const [activeAction, setActiveAction] = useState<BulkAction | null>(null);
  const { performBulkOperation, exportRequests } = useRequestHistory();
  const { showToast: _showToast } = useToast();

  const handleActionClick = (action: BulkAction) => {
    setActiveAction(action);
  };

  const handleActionConfirm = async (actionType: BulkActionType, data?: Record<string, any>) => {
    try {
      if (actionType === 'export') {
        await exportRequests({
          format: data?.format || 'csv',
          includeColumns: data?.columns || [],
          includeFilters: false,
        });
      } else {
        await performBulkOperation({
          requestIds: selectedIds,
          action: actionType,
          data,
        });
      }

      onClearSelection();
      setActiveAction(null);

    } catch (error) {
      // Error is handled by the hook
    }
  };

  const getActionIcon = (iconName: string) => {
    switch (iconName) {
      case 'check-circle':
        return CheckCircle;
      case 'x-circle':
        return XCircle;
      case 'user-check':
        return UserCheck;
      case 'tag':
        return Tag;
      case 'download':
        return Download;
      case 'trash-2':
        return Trash2;
      default:
        return CheckCircle;
    }
  };

  return (
    <>
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-blue-900">
                {selectedCount} request{selectedCount > 1 ? 's' : ''} selected
              </span>
            </div>

            <div className="flex items-center space-x-2">
              {BULK_ACTIONS.map((action) => {
                const Icon = getActionIcon(action.icon);
                return (
                  <Button
                    key={action.type}
                    variant="secondary"
                    size="sm"
                    onClick={() => handleActionClick(action)}
                    className={`${
                      action.isDestructive
                        ? 'text-red-600 border-red-200 hover:bg-red-50'
                        : 'text-blue-600 border-blue-200 hover:bg-blue-50'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {action.label}
                  </Button>
                );
              })}
            </div>
          </div>

          <Button
            variant="tertiary"
            size="sm"
            onClick={onClearSelection}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="w-4 h-4 mr-2" />
            Clear Selection
          </Button>
        </div>
      </Card>

      <BulkActionModal
        isOpen={activeAction !== null}
        action={activeAction}
        selectedCount={selectedCount}
        selectedIds={selectedIds}
        onClose={() => setActiveAction(null)}
        onConfirm={handleActionConfirm}
      />
    </>
  );
}

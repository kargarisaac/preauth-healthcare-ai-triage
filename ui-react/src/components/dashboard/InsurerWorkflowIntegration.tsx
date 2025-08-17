import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Clock,
  CheckCircle,
  AlertTriangle,
  ExternalLink,
  X,
  Bell,
  ArrowRight
} from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { useInsurer } from '@/contexts/InsurerContext';
import { useProcessing } from '@/contexts/ProcessingContext';

interface InsurerWorkflowIntegrationProps {
  className?: string;
}

const InsurerWorkflowIntegration: React.FC<InsurerWorkflowIntegrationProps> = ({
  className = ''
}) => {
  const { metrics, notifications } = useInsurer();
  const { pipelineResult } = useProcessing();
  const [showRecentActivity, setShowRecentActivity] = useState(false);
  const [dismissedNotifications, setDismissedNotifications] = useState<Set<string>>(new Set());

  // Show recent activity when pipeline result includes request creation
  useEffect(() => {
    if (pipelineResult?.data?.request_id && !dismissedNotifications.has(pipelineResult.data.request_id)) {
      setShowRecentActivity(true);
    }
  }, [pipelineResult, dismissedNotifications]);

  const dismissNotification = (id: string) => {
    setDismissedNotifications(prev => new Set(prev).add(id));
    if (pipelineResult?.data?.request_id === id) {
      setShowRecentActivity(false);
    }
  };

  // Don't render if no insurer metrics available
  if (!metrics) {
    return null;
  }

  const hasUrgentItems = metrics?.workload?.overdueReviews > 0 || 
                         (Array.isArray(notifications) ? notifications.filter(n => !n.read && n.priority === 'high').length > 0 : false);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Recent Pipeline Activity */}
      {showRecentActivity && pipelineResult?.data?.request_id && (
        <Card className="bg-green-50 border-green-200 relative">
          <button
            onClick={() => dismissNotification(pipelineResult.data.request_id)}
            className="absolute top-2 right-2 text-green-500 hover:text-green-700"
          >
            <X className="h-4 w-4" />
          </button>
          
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-green-900 mb-1">
                Request Sent to Insurer
              </h3>
              <p className="text-sm text-green-800 mb-2">
                Your file has been processed and submitted to the insurer dashboard for medical director review.
              </p>
              <div className="flex items-center space-x-4 text-xs text-green-700">
                <span>Request ID: {pipelineResult.data.request_id}</span>
                <span>Decision: {pipelineResult.decision?.outcome || 'Pending'}</span>
                {pipelineResult.metadata?.processing_time_seconds && (
                  <span>Processed in {pipelineResult.metadata.processing_time_seconds.toFixed(1)}s</span>
                )}
              </div>
              <div className="mt-2">
                <Link to="/dashboard/insurer">
                  <Button variant="tertiary" size="sm" className="text-green-700 hover:text-green-800">
                    <ExternalLink className="w-3 h-3 mr-1" />
                    View in Insurer Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Insurer Workflow Status */}
      <Card title="Insurer Workflow Status">
        <div className="space-y-4">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {metrics?.workload?.totalPending || 0}
              </div>
              <div className="text-xs text-gray-600">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {metrics?.workload?.underReview || 0}
              </div>
              <div className="text-xs text-gray-600">Under Review</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {metrics?.performance?.approvalRate || 0}%
              </div>
              <div className="text-xs text-gray-600">Approval Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {metrics?.workload?.avgReviewTime || 0}m
              </div>
              <div className="text-xs text-gray-600">Avg Review</div>
            </div>
          </div>

          {/* Urgency Indicators */}
          {hasUrgentItems && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-orange-600" />
                <span className="text-sm font-medium text-orange-800">
                  Attention Required
                </span>
              </div>
              <div className="mt-1 text-sm text-orange-700">
                {metrics?.workload?.overdueReviews > 0 && (
                  <span>{metrics?.workload?.overdueReviews} overdue reviews • </span>
                )}
                {Array.isArray(notifications) ? notifications.filter(n => !n.read && n.priority === 'high').length : 0} urgent notifications
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-200">
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>Updates every 30s</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {Array.isArray(notifications) && notifications.filter(n => !n.read).length > 0 && (
                <div className="flex items-center space-x-1 text-xs text-blue-600">
                  <Bell className="h-3 w-3" />
                  <span>{Array.isArray(notifications) ? notifications.filter(n => !n.read).length : 0} unread</span>
                </div>
              )}
              
              <Link to="/dashboard/insurer">
                <Button variant="secondary" size="sm" className="text-xs">
                  View Dashboard
                  <ArrowRight className="w-3 h-3 ml-1" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default InsurerWorkflowIntegration;
import React from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  Clock,
  AlertTriangle,
  ExternalLink,
  FileText,
  User
} from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface RequestStatus {
  id: string;
  status: 'submitted' | 'under_review' | 'decided' | 'communicated';
  submittedAt: string;
  assignedReviewer?: string;
  urgency: 'routine' | 'urgent' | 'emergency' | 'critical';
  estimatedDecisionTime?: string;
  aiRecommendation?: {
    decision: 'approve' | 'deny' | 'request_more_info';
    confidence: number;
  };
}

interface RequestStatusBannerProps {
  patientId: string;
  requestStatus?: RequestStatus;
  className?: string;
}

const RequestStatusBanner: React.FC<RequestStatusBannerProps> = ({
  patientId,
  requestStatus,
  className = ''
}) => {
  if (!requestStatus) {
    return null;
  }

  const getStatusInfo = () => {
    switch (requestStatus.status) {
      case 'submitted':
        return {
          icon: Clock,
          iconColor: 'text-blue-500',
          bgColor: 'bg-blue-50 border-blue-200',
          title: 'Request Submitted to Insurer',
          message: 'Your file has been processed and submitted for medical director review.',
          showProgress: true
        };
      case 'under_review':
        return {
          icon: User,
          iconColor: 'text-orange-500',
          bgColor: 'bg-orange-50 border-orange-200',
          title: 'Under Medical Review',
          message: `Currently being reviewed by ${requestStatus.assignedReviewer || 'medical director'}.`,
          showProgress: true
        };
      case 'decided':
        return {
          icon: CheckCircle,
          iconColor: 'text-green-500',
          bgColor: 'bg-green-50 border-green-200',
          title: 'Decision Made',
          message: 'Medical director has made a decision. Communication is being prepared.',
          showProgress: false
        };
      case 'communicated':
        return {
          icon: CheckCircle,
          iconColor: 'text-green-500',
          bgColor: 'bg-green-50 border-green-200',
          title: 'Decision Communicated',
          message: 'The authorization decision has been sent to your provider.',
          showProgress: false
        };
      default:
        return {
          icon: AlertTriangle,
          iconColor: 'text-gray-500',
          bgColor: 'bg-gray-50 border-gray-200',
          title: 'Status Unknown',
          message: 'Request status is being updated.',
          showProgress: false
        };
    }
  };

  const getUrgencyColor = () => {
    switch (requestStatus.urgency) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'emergency':
        return 'text-red-500 bg-red-50';
      case 'urgent':
        return 'text-orange-500 bg-orange-50';
      default:
        return 'text-blue-500 bg-blue-50';
    }
  };

  const statusInfo = getStatusInfo();
  const StatusIcon = statusInfo.icon;

  const progressSteps = [
    { label: 'Submitted', completed: true },
    { 
      label: 'Under Review', 
      completed: ['under_review', 'decided', 'communicated'].includes(requestStatus.status),
      active: requestStatus.status === 'under_review'
    },
    { 
      label: 'Decision Made', 
      completed: ['decided', 'communicated'].includes(requestStatus.status),
      active: requestStatus.status === 'decided'
    },
    { 
      label: 'Communicated', 
      completed: requestStatus.status === 'communicated',
      active: requestStatus.status === 'communicated'
    }
  ];

  return (
    <Card className={`${statusInfo.bgColor} border ${className}`}>
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <StatusIcon className={`h-6 w-6 ${statusInfo.iconColor}`} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-900">
              {statusInfo.title}
            </h3>
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getUrgencyColor()}`}>
                {requestStatus.urgency.charAt(0).toUpperCase() + requestStatus.urgency.slice(1)}
              </span>
              <span className="text-xs text-gray-500">
                ID: {requestStatus.id}
              </span>
            </div>
          </div>
          
          <p className="text-sm text-gray-700 mb-3">
            {statusInfo.message}
          </p>

          {/* AI Recommendation Display */}
          {requestStatus.aiRecommendation && (
            <div className="mb-3 p-2 bg-white rounded border border-gray-200">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">AI Recommendation:</span>
                <span className="font-medium text-gray-900">
                  {requestStatus.aiRecommendation.decision.replace('_', ' ').toUpperCase()}
                  <span className="ml-1 text-gray-500">
                    ({Math.round(requestStatus.aiRecommendation.confidence)}% confidence)
                  </span>
                </span>
              </div>
            </div>
          )}

          {/* Progress Steps */}
          {statusInfo.showProgress && (
            <div className="mb-3">
              <div className="flex items-center space-x-2">
                {progressSteps.map((step, index) => (
                  <React.Fragment key={step.label}>
                    <div className="flex items-center">
                      <div className={`
                        w-3 h-3 rounded-full border-2 
                        ${step.completed 
                          ? 'bg-green-500 border-green-500' 
                          : step.active 
                            ? 'bg-blue-500 border-blue-500' 
                            : 'bg-gray-200 border-gray-300'
                        }
                      `} />
                      <span className={`
                        ml-1 text-xs 
                        ${step.completed || step.active ? 'text-gray-900 font-medium' : 'text-gray-500'}
                      `}>
                        {step.label}
                      </span>
                    </div>
                    {index < progressSteps.length - 1 && (
                      <div className={`
                        flex-1 h-0.5 mx-2 
                        ${step.completed ? 'bg-green-500' : 'bg-gray-200'}
                      `} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Additional Info */}
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center space-x-4">
              <span>
                Submitted: {new Date(requestStatus.submittedAt).toLocaleDateString()} at{' '}
                {new Date(requestStatus.submittedAt).toLocaleTimeString()}
              </span>
              {requestStatus.estimatedDecisionTime && (
                <span>
                  Est. Decision: {requestStatus.estimatedDecisionTime}
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <Link to={`/dashboard/insurer`}>
                <Button variant="tertiary" size="sm" className="text-xs">
                  <ExternalLink className="w-3 h-3 mr-1" />
                  View in Insurer Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RequestStatusBanner;
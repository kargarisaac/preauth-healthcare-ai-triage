import React from 'react';
import { 
  User, 
  Phone, 
  Mail, 
  MapPin, 
  CreditCard, 
  AlertTriangle, 
  Activity,
  Clock,
  DollarSign,
  Shield,
  Calendar,
  Heart,
  Pill
} from 'lucide-react';
import { Member } from '../../types/healthcare';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface MemberCardProps {
  member: Member;
  onClick?: () => void;
  onViewProfile?: () => void;
  onViewHistory?: () => void;
  onViewCareGaps?: () => void;
  showActions?: boolean;
  compact?: boolean;
  className?: string;
}

export const MemberCard: React.FC<MemberCardProps> = ({
  member,
  onClick,
  onViewProfile,
  onViewHistory,
  onViewCareGaps,
  showActions = true,
  compact = false,
  className = ''
}) => {
  // Calculate age
  const calculateAge = (dateOfBirth: string): number => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  };

  // Get risk level color and label
  const getRiskInfo = (score: number) => {
    if (score >= 70) {
      return { level: 'High', color: 'text-red-600', bgColor: 'bg-red-100', dotColor: 'bg-red-500' };
    } else if (score >= 40) {
      return { level: 'Medium', color: 'text-yellow-600', bgColor: 'bg-yellow-100', dotColor: 'bg-yellow-500' };
    } else {
      return { level: 'Low', color: 'text-green-600', bgColor: 'bg-green-100', dotColor: 'bg-green-500' };
    }
  };

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Calculate days since last activity
  const getDaysSinceActivity = (lastActivity: string): number => {
    const today = new Date();
    const activityDate = new Date(lastActivity);
    return Math.floor((today.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24));
  };

  const age = calculateAge(member.demographics.dateOfBirth);
  const riskInfo = getRiskInfo(member.riskScore);
  const daysSinceActivity = getDaysSinceActivity(member.lastActivity);
  const activeConditions = member.medicalHistory.chronicConditions.filter(
    c => c.status === 'active' || c.status === 'chronic'
  );

  return (
    <Card 
      className={`p-4 hover:shadow-lg transition-shadow duration-200 cursor-pointer ${className}`}
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {member.demographics.fullName}
              </h3>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>{age} years old</span>
                <span>•</span>
                <span className="capitalize">{member.demographics.gender}</span>
                <span>•</span>
                <span>{member.demographics.nationality}</span>
              </div>
            </div>
          </div>
          
          {/* Risk Badge */}
          <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${riskInfo.bgColor} ${riskInfo.color}`}>
            <div className={`w-2 h-2 rounded-full ${riskInfo.dotColor}`} />
            <span>{riskInfo.level} Risk</span>
          </div>
        </div>

        {/* Key Information Grid */}
        <div className={`grid ${compact ? 'grid-cols-1' : 'grid-cols-2'} gap-3`}>
          {/* Contact Information */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm">
              <CreditCard className="h-4 w-4 text-gray-400" />
              <span className="text-gray-900 font-medium">
                {member.emiratesId}
              </span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm">
              <Phone className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">{member.contact.phone}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm">
              <Mail className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600 truncate">{member.contact.email}</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm">
              <MapPin className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">
                {member.contact.address.city}, {member.contact.address.emirate}
              </span>
            </div>
          </div>

          {/* Insurance & Medical Information */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm">
              <Shield className="h-4 w-4 text-gray-400" />
              <div>
                <span className="text-gray-900 font-medium">
                  {member.insurance.provider}
                </span>
                <span className="text-gray-600 ml-1">
                  ({member.insurance.planType})
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 text-sm">
              <CreditCard className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">{member.insurance.policyNumber}</span>
            </div>
            
            {activeConditions.length > 0 && (
              <div className="flex items-center space-x-2 text-sm">
                <Heart className="h-4 w-4 text-gray-400" />
                <span className="text-gray-600">
                  {activeConditions.length} chronic condition{activeConditions.length > 1 ? 's' : ''}
                </span>
              </div>
            )}
            
            <div className="flex items-center space-x-2 text-sm">
              <Clock className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">
                Last activity: {daysSinceActivity === 0 ? 'Today' : `${daysSinceActivity} days ago`}
              </span>
            </div>
          </div>
        </div>

        {/* Cost Utilization Summary */}
        {!compact && (
          <div className="border-t pt-3">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {formatCurrency(member.costUtilization.yearToDate.totalCosts)}
                </div>
                <div className="text-xs text-gray-600">YTD Costs</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {formatCurrency(member.costUtilization.yearToDate.deductibleMet)}
                </div>
                <div className="text-xs text-gray-600">Deductible Met</div>
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {member.recentRequests.length}
                </div>
                <div className="text-xs text-gray-600">Recent Requests</div>
              </div>
            </div>
          </div>
        )}

        {/* Chronic Conditions */}
        {!compact && activeConditions.length > 0 && (
          <div className="border-t pt-3">
            <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
              <Pill className="h-4 w-4 mr-1" />
              Active Conditions
            </h4>
            <div className="flex flex-wrap gap-2">
              {activeConditions.slice(0, 3).map((condition, index) => (
                <span
                  key={index}
                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                    condition.severity === 'severe' ? 'bg-red-100 text-red-700' :
                    condition.severity === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-blue-100 text-blue-700'
                  }`}
                >
                  {condition.condition}
                </span>
              ))}
              {activeConditions.length > 3 && (
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                  +{activeConditions.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Insurance Status */}
        <div className="border-t pt-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                member.insurance.status === 'active' ? 'bg-green-500' :
                member.insurance.status === 'suspended' ? 'bg-yellow-500' :
                'bg-red-500'
              }`} />
              <span className="text-sm text-gray-600">
                Insurance {member.insurance.status}
              </span>
              <span className="text-sm text-gray-400">
                • Expires {formatDate(member.insurance.expirationDate)}
              </span>
            </div>
            
            {/* Alerts */}
            {(member.riskScore >= 70 || activeConditions.some(c => c.severity === 'severe')) && (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {showActions && (
          <div className="border-t pt-3">
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewProfile?.();
                }}
                className="flex-1"
              >
                View Profile
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewHistory?.();
                }}
                className="flex-1"
              >
                History
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewCareGaps?.();
                }}
                className="flex-1"
              >
                Care Gaps
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default MemberCard;
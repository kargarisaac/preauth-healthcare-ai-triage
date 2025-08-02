import React, { useState, useEffect } from 'react';
import {
  User,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  Shield,
  Heart,
  Activity,
  DollarSign,
  Calendar,
  AlertTriangle,
  Edit,
  Download,
  Share,
  RefreshCw,
  Pill,
  Stethoscope,
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { Member } from '../../types/healthcare';
import { useMemberProfile } from '../../hooks/data/useMemberProfile';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface MemberProfileProps {
  memberId: string;
  onEdit?: (member: Member) => void;
  onClose?: () => void;
  className?: string;
}

interface TabConfig {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const TABS: TabConfig[] = [
  { id: 'overview', label: 'Overview', icon: <User className="h-4 w-4" /> },
  { id: 'demographics', label: 'Demographics', icon: <Users className="h-4 w-4" /> },
  { id: 'insurance', label: 'Insurance', icon: <Shield className="h-4 w-4" /> },
  { id: 'medical', label: 'Medical History', icon: <Heart className="h-4 w-4" /> },
  { id: 'costs', label: 'Cost Analysis', icon: <DollarSign className="h-4 w-4" /> },
  { id: 'utilization', label: 'Utilization', icon: <Activity className="h-4 w-4" /> }
];

export const MemberProfile: React.FC<MemberProfileProps> = ({
  memberId,
  onEdit,
  onClose,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);

  const {
    member,
    activities,
    authorizationHistory,
    isLoading,
    error,
    lastUpdated,
    loadMemberProfile,
    updateMemberInfo,
    refreshMemberData,
    getMemberInsights,
    getCostTrends
  } = useMemberProfile(memberId);

  // Load member profile on component mount
  useEffect(() => {
    if (memberId) {
      loadMemberProfile(memberId);
    }
  }, [memberId, loadMemberProfile]);

  // Calculate member insights
  const insights = member ? getMemberInsights() : null;
  const costTrends = member ? getCostTrends() : null;

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
      month: 'long',
      day: 'numeric'
    });
  };

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

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'severe': return 'text-red-600 bg-red-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'mild': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get risk color
  const getRiskColor = (riskScore: number) => {
    if (riskScore >= 70) return 'text-red-600 bg-red-100';
    if (riskScore >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  if (isLoading && !member) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error && !member) {
    return (
      <div className="p-6 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Profile</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <Button onClick={() => loadMemberProfile(memberId)}>
          Retry
        </Button>
      </div>
    );
  }

  if (!member) {
    return (
      <div className="p-6 text-center">
        <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Member Not Found</h3>
        <p className="text-gray-600">No member found with ID: {memberId}</p>
      </div>
    );
  }

  const age = calculateAge(member.demographics.dateOfBirth);

  // Render different tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Risk Score</p>
                    <p className="text-2xl font-bold text-gray-900">{member.riskScore}</p>
                  </div>
                  <div className={`p-2 rounded-full ${getRiskColor(member.riskScore)}`}>
                    <Activity className="h-6 w-6" />
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">YTD Costs</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(member.costUtilization.yearToDate.totalCosts)}
                    </p>
                  </div>
                  <div className="p-2 rounded-full bg-blue-100 text-blue-600">
                    <DollarSign className="h-6 w-6" />
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Chronic Conditions</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {member.medicalHistory.chronicConditions.length}
                    </p>
                  </div>
                  <div className="p-2 rounded-full bg-red-100 text-red-600">
                    <Heart className="h-6 w-6" />
                  </div>
                </div>
              </Card>
              
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Days Since Activity</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {insights?.lastActivityDays || 0}
                    </p>
                  </div>
                  <div className="p-2 rounded-full bg-purple-100 text-purple-600">
                    <Clock className="h-6 w-6" />
                  </div>
                </div>
              </Card>
            </div>

            {/* Member Insights */}
            {insights && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Member Insights</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Risk Level</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(member.riskScore)}`}>
                        {insights.riskLevel.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Remaining Deductible</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(insights.remainingDeductible)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Remaining Out-of-Pocket</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(insights.remainingOutOfPocket)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Active Conditions</span>
                      <span className="text-sm font-medium text-gray-900">
                        {insights.activeConditions.length}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Severity Score</span>
                      <span className="text-sm font-medium text-gray-900">
                        {insights.severityScore}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Last Activity</span>
                      <span className="text-sm font-medium text-gray-900">
                        {insights.lastActivityDays === 0 ? 'Today' : `${insights.lastActivityDays} days ago`}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {/* Cost Trends */}
            {costTrends && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Trends</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Current Month</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(costTrends.currentMonthCosts)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Previous Month</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(costTrends.previousMonthCosts)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Monthly Change</span>
                      <div className="flex items-center space-x-1">
                        {costTrends.costChange > 0 ? (
                          <TrendingUp className="h-4 w-4 text-red-500" />
                        ) : costTrends.costChange < 0 ? (
                          <TrendingDown className="h-4 w-4 text-green-500" />
                        ) : (
                          <Minus className="h-4 w-4 text-gray-500" />
                        )}
                        <span className={`text-sm font-medium ${
                          costTrends.costChange > 0 ? 'text-red-600' :
                          costTrends.costChange < 0 ? 'text-green-600' :
                          'text-gray-600'
                        }`}>
                          {Math.abs(costTrends.costChange).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Average Monthly</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(costTrends.averageMonthlyCosts)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Highest Month</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(costTrends.highestMonth.totalCosts)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Lowest Month</span>
                      <span className="text-sm font-medium text-gray-900">
                        {formatCurrency(costTrends.lowestMonth.totalCosts)}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        );

      case 'demographics':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Demographics Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Full Name</label>
                  <p className="mt-1 text-sm text-gray-900">{member.demographics.fullName}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatDate(member.demographics.dateOfBirth)} ({age} years old)
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Gender</label>
                  <p className="mt-1 text-sm text-gray-900 capitalize">{member.demographics.gender}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nationality</label>
                  <p className="mt-1 text-sm text-gray-900">{member.demographics.nationality}</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Emirates ID</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">{member.emiratesId}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Preferred Language</label>
                  <p className="mt-1 text-sm text-gray-900">{member.demographics.preferredLanguage}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Marital Status</label>
                  <p className="mt-1 text-sm text-gray-900 capitalize">{member.demographics.maritalStatus}</p>
                </div>
              </div>
            </div>
            
            {/* Contact Information */}
            <div className="mt-8">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Contact Information</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Primary Phone</label>
                    <p className="mt-1 text-sm text-gray-900">{member.contact.phone}</p>
                  </div>
                  
                  {member.contact.alternativePhone && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Alternative Phone</label>
                      <p className="mt-1 text-sm text-gray-900">{member.contact.alternativePhone}</p>
                    </div>
                  )}
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <p className="mt-1 text-sm text-gray-900">{member.contact.email}</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Address</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {member.contact.address.street}<br />
                      {member.contact.address.city}, {member.contact.address.emirate}<br />
                      {member.contact.address.country} {member.contact.address.postalCode}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Emergency Contact</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {member.contact.emergencyContact.name}<br />
                      <span className="text-gray-600">{member.contact.emergencyContact.relationship}</span><br />
                      {member.contact.emergencyContact.phone}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        );

      case 'insurance':
        return (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Insurance Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Provider</label>
                  <p className="mt-1 text-sm text-gray-900">{member.insurance.provider}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Policy Number</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">{member.insurance.policyNumber}</p>
                </div>
                
                {member.insurance.groupNumber && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Group Number</label>
                    <p className="mt-1 text-sm text-gray-900 font-mono">{member.insurance.groupNumber}</p>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Plan Type</label>
                  <p className="mt-1 text-sm text-gray-900">{member.insurance.planType}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <div className="flex items-center space-x-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${
                      member.insurance.status === 'active' ? 'bg-green-500' :
                      member.insurance.status === 'suspended' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`} />
                    <span className="text-sm text-gray-900 capitalize">{member.insurance.status}</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Effective Date</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(member.insurance.effectiveDate)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Expiration Date</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(member.insurance.expirationDate)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Benefit Year</label>
                  <p className="mt-1 text-sm text-gray-900">{member.insurance.benefitYear}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Deductible</label>
                  <p className="mt-1 text-sm text-gray-900">{formatCurrency(member.insurance.deductible)}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Co-payment</label>
                  <p className="mt-1 text-sm text-gray-900">{member.insurance.coPayment}%</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Out-of-Pocket Maximum</label>
                  <p className="mt-1 text-sm text-gray-900">{formatCurrency(member.insurance.outOfPocketMax)}</p>
                </div>
              </div>
            </div>
          </Card>
        );

      case 'medical':
        return (
          <div className="space-y-6">
            {/* Allergies */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Allergies</h3>
              {member.medicalHistory.allergies.length > 0 ? (
                <div className="space-y-3">
                  {member.medicalHistory.allergies.map((allergy, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{allergy.allergen}</p>
                        <p className="text-sm text-gray-600">{allergy.reaction}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(allergy.severity)}`}>
                        {allergy.severity}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No known allergies</p>
              )}
            </Card>

            {/* Chronic Conditions */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Chronic Conditions</h3>
              {member.medicalHistory.chronicConditions.length > 0 ? (
                <div className="space-y-4">
                  {member.medicalHistory.chronicConditions.map((condition) => (
                    <div key={condition.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{condition.condition}</h4>
                          <p className="text-sm text-gray-600">ICD Code: {condition.icdCode}</p>
                          <p className="text-sm text-gray-600">Diagnosed: {formatDate(condition.diagnosisDate)}</p>
                          <p className="text-sm text-gray-600">Managing Provider: {condition.managingProvider}</p>
                          <p className="text-sm text-gray-600">Last Review: {formatDate(condition.lastReview)}</p>
                        </div>
                        <div className="flex flex-col items-end space-y-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(condition.severity)}`}>
                            {condition.severity}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            condition.status === 'active' ? 'bg-green-100 text-green-700' :
                            condition.status === 'chronic' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {condition.status}
                          </span>
                        </div>
                      </div>
                      
                      {condition.medications.length > 0 && (
                        <div className="mt-3">
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Current Medications:</h5>
                          <div className="flex flex-wrap gap-2">
                            {condition.medications.map((medication, index) => (
                              <span key={index} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                                {medication}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No chronic conditions recorded</p>
              )}
            </Card>

            {/* Surgical History */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Surgical History</h3>
              {member.medicalHistory.surgicalHistory.length > 0 ? (
                <div className="space-y-3">
                  {member.medicalHistory.surgicalHistory.map((surgery, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{surgery.procedure}</p>
                        <p className="text-sm text-gray-600">{formatDate(surgery.date)} • {surgery.hospital}</p>
                        {surgery.complications && (
                          <p className="text-sm text-red-600">Complications: {surgery.complications}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No surgical history recorded</p>
              )}
            </Card>

            {/* Family History */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Family History</h3>
              {member.medicalHistory.familyHistory.length > 0 ? (
                <div className="space-y-3">
                  {member.medicalHistory.familyHistory.map((history, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{history.condition}</p>
                        <p className="text-sm text-gray-600">
                          {history.relationship}
                          {history.ageOfOnset && ` • Age of onset: ${history.ageOfOnset}`}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No family history recorded</p>
              )}
            </Card>
          </div>
        );

      case 'costs':
        return (
          <div className="space-y-6">
            {/* Year-to-Date Summary */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Year-to-Date Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(member.costUtilization.yearToDate.totalCosts)}
                  </p>
                  <p className="text-sm text-gray-600">Total Costs</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {formatCurrency(member.costUtilization.yearToDate.planPaid)}
                  </p>
                  <p className="text-sm text-gray-600">Plan Paid</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">
                    {formatCurrency(member.costUtilization.yearToDate.memberPaid)}
                  </p>
                  <p className="text-sm text-gray-600">Member Paid</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(member.costUtilization.yearToDate.deductibleMet)}
                  </p>
                  <p className="text-sm text-gray-600">Deductible Met</p>
                </div>
              </div>
            </Card>

            {/* Top Categories */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost by Category</h3>
              <div className="space-y-4">
                {member.costUtilization.topCategories.map((category, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      <span className="text-sm font-medium text-gray-900">{category.category}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{formatCurrency(category.amount)}</p>
                      <p className="text-xs text-gray-600">{category.percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Monthly Trends */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Trends</h3>
              <div className="space-y-3">
                {member.costUtilization.monthlyTrends.map((month, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">
                        {new Date(month.month + '-01').toLocaleDateString('en-AE', { month: 'long', year: 'numeric' })}
                      </p>
                      <p className="text-sm text-gray-600">
                        {month.visits} visits • {month.prescriptions} prescriptions
                      </p>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(month.totalCosts)}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        );

      case 'utilization':
        return (
          <div className="space-y-6">
            {/* Recent Activities */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h3>
              {activities.length > 0 ? (
                <div className="space-y-4">
                  {activities.slice(0, 10).map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        activity.type === 'authorization' ? 'bg-blue-100 text-blue-600' :
                        activity.type === 'claim' ? 'bg-green-100 text-green-600' :
                        activity.type === 'care_gap' ? 'bg-yellow-100 text-yellow-600' :
                        'bg-purple-100 text-purple-600'
                      }`}>
                        {activity.type === 'authorization' ? <FileText className="h-4 w-4" /> :
                         activity.type === 'claim' ? <DollarSign className="h-4 w-4" /> :
                         activity.type === 'care_gap' ? <AlertCircle className="h-4 w-4" /> :
                         <Calendar className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{activity.title}</h4>
                        <p className="text-sm text-gray-600">{activity.description}</p>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            activity.status === 'approved' ? 'bg-green-100 text-green-700' :
                            activity.status === 'denied' ? 'bg-red-100 text-red-700' :
                            activity.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {activity.status}
                          </span>
                          {activity.amount && (
                            <span className="text-sm text-gray-600">
                              {formatCurrency(activity.amount)}
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {formatDate(activity.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No recent activities</p>
              )}
            </Card>

            {/* Authorization History */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Authorization History</h3>
              {authorizationHistory.length > 0 ? (
                <div className="space-y-4">
                  {authorizationHistory.map((auth) => (
                    <div key={auth.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{auth.serviceType}</h4>
                          <p className="text-sm text-gray-600">{auth.provider}</p>
                          <p className="text-sm text-gray-600">Requested: {formatDate(auth.requestDate)}</p>
                          {auth.reviewDate && (
                            <p className="text-sm text-gray-600">Reviewed: {formatDate(auth.reviewDate)}</p>
                          )}
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            auth.status === 'approved' ? 'bg-green-100 text-green-700' :
                            auth.status === 'denied' ? 'bg-red-100 text-red-700' :
                            auth.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {auth.status}
                          </span>
                          <p className="text-sm font-medium text-gray-900 mt-1">
                            {formatCurrency(auth.requestedAmount)}
                          </p>
                          {auth.approvedAmount && auth.approvedAmount !== auth.requestedAmount && (
                            <p className="text-sm text-green-600">
                              Approved: {formatCurrency(auth.approvedAmount)}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      {auth.decisionReason && (
                        <div className="mt-3">
                          <p className="text-sm text-gray-700">
                            <span className="font-medium">Reason:</span> {auth.decisionReason}
                          </p>
                        </div>
                      )}
                      
                      {auth.reviewNotes && (
                        <div className="mt-2">
                          <p className="text-sm text-gray-600">{auth.reviewNotes}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No authorization history</p>
              )}
            </Card>
          </div>
        );

      default:
        return <div>Tab content not found</div>;
    }
  };

  return (
    <div className={`bg-white ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{member.demographics.fullName}</h1>
              <p className="text-sm text-gray-600">
                {member.emiratesId} • {age} years old • {member.insurance.provider}
              </p>
            </div>
          </div>
          
          {/* Header Actions */}
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={refreshMemberData}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit?.(member)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
            
            <Button
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            
            <Button
              variant="outline"
              size="sm"
            >
              <Share className="h-4 w-4 mr-2" />
              Share
            </Button>
            
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        
        {/* Last Updated */}
        {lastUpdated && (
          <p className="text-xs text-gray-500 mt-2">
            Last updated: {new Date(lastUpdated).toLocaleString('en-AE')}
          </p>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default MemberProfile;
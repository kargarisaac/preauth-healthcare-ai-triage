import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Eye, EyeOff, Lock, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { Member } from '../../types/healthcare';
import {
  usePDPLCompliance,
  PDPLProcessingPurpose,
  PDPLLegalBasis,
  PDPLDataCategory,
  ConsentRecord
} from '../../utils/pdplCompliance';
import { MemberSearch } from './MemberSearch';
import { MemberProfile } from './MemberProfile';
import { MemberCard } from './MemberCard';
import { AlertsPanel } from './AlertsPanel';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';

interface PrivacyAwareMemberSearchProps {
  onMemberSelect?: (member: Member) => void;
  userRole: string;
  userId: string;
  purpose: PDPLProcessingPurpose;
  className?: string;
}

interface PrivacyNotice {
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  actions?: Array<{
    label: string;
    action: () => void;
    variant?: 'primary' | 'secondary' | 'danger';
  }>;
}

export const PrivacyAwareMemberSearch: React.FC<PrivacyAwareMemberSearchProps> = ({
  onMemberSelect,
  userRole,
  userId,
  purpose,
  className = ''
}) => {
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [maskedMember, setMaskedMember] = useState<Partial<Member> | null>(null);
  const [showProfile, setShowProfile] = useState(false);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [privacyNotices, setPrivacyNotices] = useState<PrivacyNotice[]>([]);
  const [dataVisible, setDataVisible] = useState<{ [key: string]: boolean }>({});
  const [userConsents, setUserConsents] = useState<{ [key: string]: boolean }>({});

  const {
    classifyField,
    checkProcessing,
    maskData,
    logAccess,
    recordConsent,
    checkRetention
  } = usePDPLCompliance();

  // Check user permissions for the current purpose
  const checkUserPermissions = useCallback((member: Member) => {
    const notices: PrivacyNotice[] = [];

    // Check if user role has access to this data
    const rolePermissions = {
      admin: [PDPLProcessingPurpose.HEALTHCARE_TREATMENT, PDPLProcessingPurpose.INSURANCE_CLAIMS, PDPLProcessingPurpose.QUALITY_IMPROVEMENT],
      doctor: [PDPLProcessingPurpose.HEALTHCARE_TREATMENT, PDPLProcessingPurpose.PREVENTIVE_CARE, PDPLProcessingPurpose.EMERGENCY_CARE],
      nurse: [PDPLProcessingPurpose.HEALTHCARE_TREATMENT, PDPLProcessingPurpose.PREVENTIVE_CARE],
      financial: [PDPLProcessingPurpose.INSURANCE_CLAIMS],
      researcher: [PDPLProcessingPurpose.RESEARCH_ANONYMIZED]
    };

    const allowedPurposes = rolePermissions[userRole as keyof typeof rolePermissions] || [];

    if (!allowedPurposes.includes(purpose)) {
      notices.push({
        title: 'Access Restricted',
        message: `Your role (${userRole}) does not have permission to access data for ${purpose}`,
        type: 'error'
      });
      return notices;
    }

    // Check data retention compliance
    const retentionCheck = checkRetention(member);
    if (!retentionCheck.shouldRetain) {
      notices.push({
        title: 'Data Retention Notice',
        message: `This member's data is scheduled for deletion: ${retentionCheck.reason}`,
        type: 'warning',
        actions: [{
          label: 'Contact Data Protection Officer',
          action: () => window.open('mailto:dpo@nazmito.com?subject=Data Retention Query')
        }]
      });
    }

    // Check for sensitive data categories
    const healthDataCategories = [PDPLDataCategory.HEALTH_DATA, PDPLDataCategory.SENSITIVE_PERSONAL];
    const hasHealthData = member.medicalHistory.chronicConditions.length > 0 ||
                         member.medicalHistory.allergies.length > 0;

    if (hasHealthData && !checkProcessing(member.id, purpose, healthDataCategories)) {
      notices.push({
        title: 'Consent Required',
        message: 'This member\'s health data requires explicit consent for the intended purpose',
        type: 'warning',
        actions: [{
          label: 'Request Consent',
          action: () => setShowConsentModal(true),
          variant: 'primary'
        }]
      });
    }

    // Check for high-risk members
    if (member.riskScore >= 70) {
      notices.push({
        title: 'High-Risk Member',
        message: 'This member has a high risk score. Additional care coordination may be required.',
        type: 'info'
      });
    }

    return notices;
  }, [userRole, purpose, checkProcessing, checkRetention]);

  // Handle member selection with privacy checks
  const handleMemberSelect = useCallback((member: Member) => {
    // Log the access attempt
    logAccess(
      userId,
      userRole,
      'VIEW_MEMBER',
      'Member',
      member.id,
      purpose,
      PDPLLegalBasis.LEGITIMATE_INTERESTS,
      [PDPLDataCategory.PERSONAL_IDENTIFIABLE, PDPLDataCategory.HEALTH_DATA],
      true
    );

    const notices = checkUserPermissions(member);
    setPrivacyNotices(notices);

    // Mask sensitive data based on role and purpose
    const maskedData = maskData(member, userRole, purpose);

    setSelectedMember(member);
    setMaskedMember(maskedData);

    // Initialize visibility settings based on data sensitivity
    const initialVisibility: { [key: string]: boolean } = {};
    Object.keys(maskedData).forEach(key => {
      const categories = classifyField(key);
      const isSensitive = categories.some(cat =>
        [PDPLDataCategory.HEALTH_DATA, PDPLDataCategory.SENSITIVE_PERSONAL].includes(cat)
      );
      initialVisibility[key] = !isSensitive; // Hide sensitive data by default
    });
    setDataVisible(initialVisibility);

    if (onMemberSelect) {
      onMemberSelect(member);
    }
  }, [userId, userRole, purpose, checkUserPermissions, maskData, classifyField, logAccess, onMemberSelect]);

  // Toggle data field visibility
  const toggleDataVisibility = useCallback((field: string) => {
    setDataVisible(prev => ({ ...prev, [field]: !prev[field] }));

    // Log sensitive data access
    const categories = classifyField(field);
    if (categories.some(cat => [PDPLDataCategory.HEALTH_DATA, PDPLDataCategory.SENSITIVE_PERSONAL].includes(cat))) {
      logAccess(
        userId,
        userRole,
        'VIEW_SENSITIVE_FIELD',
        'Member',
        selectedMember?.id || '',
        purpose,
        PDPLLegalBasis.LEGITIMATE_INTERESTS,
        categories,
        true,
        { field }
      );
    }
  }, [classifyField, logAccess, userId, userRole, purpose, selectedMember]);

  // Handle consent recording
  const handleConsentRecording = useCallback((consentData: any) => {
    if (!selectedMember) return;

    const consentRecord: ConsentRecord = {
      id: `consent-${Date.now()}`,
      memberId: selectedMember.id,
      purpose,
      legalBasis: PDPLLegalBasis.CONSENT,
      consentDate: new Date().toISOString(),
      withdrawn: false,
      version: '1.0',
      specificConsents: {
        dataProcessing: consentData.dataProcessing || false,
        dataSharing: consentData.dataSharing || false,
        marketingCommunications: consentData.marketingCommunications || false,
        dataRetention: consentData.dataRetention || false,
        internationalTransfer: consentData.internationalTransfer || false
      },
      metadata: {
        consentMethod: 'explicit',
        witnessedBy: userId
      }
    };

    recordConsent(consentRecord);
    setShowConsentModal(false);

    // Update privacy notices
    const updatedNotices = privacyNotices.filter(notice => notice.title !== 'Consent Required');
    setPrivacyNotices(updatedNotices);

    // Show success notice
    setPrivacyNotices(prev => [...prev, {
      title: 'Consent Recorded',
      message: 'Member consent has been successfully recorded for this processing purpose',
      type: 'success'
    }]);
  }, [selectedMember, purpose, userId, recordConsent, privacyNotices]);

  // Privacy-aware member card component
  const PrivacyAwareMemberCard: React.FC<{ member: Member }> = ({ member }) => {
    const [showSensitiveData, setShowSensitiveData] = useState(false);

    return (
      <div className="relative">
        {/* Privacy overlay for sensitive data */}
        {!showSensitiveData && (
          <div className="absolute inset-0 bg-gray-50 bg-opacity-90 flex items-center justify-center z-10 rounded-lg">
            <div className="text-center">
              <Shield className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-900 mb-2">Protected Health Information</p>
              <p className="text-xs text-gray-600 mb-3">This data is protected under UAE PDPL</p>
              <Button
                size="sm"
                onClick={() => {
                  setShowSensitiveData(true);
                  // Log the sensitive data access
                  logAccess(
                    userId,
                    userRole,
                    'VIEW_PROTECTED_DATA',
                    'Member',
                    member.id,
                    purpose,
                    PDPLLegalBasis.LEGITIMATE_INTERESTS,
                    [PDPLDataCategory.HEALTH_DATA],
                    true
                  );
                }}
              >
                <Eye className="h-4 w-4 mr-1" />
                Show Data
              </Button>
            </div>
          </div>
        )}

        <MemberCard
          member={member}
          onClick={() => handleMemberSelect(member)}
          showActions={showSensitiveData}
        />
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Privacy Notices */}
      {privacyNotices.length > 0 && (
        <div className="space-y-3">
          {privacyNotices.map((notice, index) => (
            <Card key={index} className={`p-4 border-l-4 ${
              notice.type === 'error' ? 'border-red-500 bg-red-50' :
              notice.type === 'warning' ? 'border-yellow-500 bg-yellow-50' :
              notice.type === 'success' ? 'border-green-500 bg-green-50' :
              'border-blue-500 bg-blue-50'
            }`}>
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  {notice.type === 'error' ? <AlertTriangle className="h-5 w-5 text-red-500" /> :
                   notice.type === 'warning' ? <AlertTriangle className="h-5 w-5 text-yellow-500" /> :
                   notice.type === 'success' ? <CheckCircle className="h-5 w-5 text-green-500" /> :
                   <Info className="h-5 w-5 text-blue-500" />}
                </div>
                <div className="ml-3 flex-1">
                  <h3 className={`text-sm font-medium ${
                    notice.type === 'error' ? 'text-red-800' :
                    notice.type === 'warning' ? 'text-yellow-800' :
                    notice.type === 'success' ? 'text-green-800' :
                    'text-blue-800'
                  }`}>
                    {notice.title}
                  </h3>
                  <p className={`mt-1 text-sm ${
                    notice.type === 'error' ? 'text-red-700' :
                    notice.type === 'warning' ? 'text-yellow-700' :
                    notice.type === 'success' ? 'text-green-700' :
                    'text-blue-700'
                  }`}>
                    {notice.message}
                  </p>
                  {notice.actions && (
                    <div className="mt-3 space-x-2">
                      {notice.actions.map((action, actionIndex) => (
                        <Button
                          key={actionIndex}
                          size="sm"
                          variant={action.variant || 'outline'}
                          onClick={action.action}
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Member Search */}
      <MemberSearch
        onMemberSelect={handleMemberSelect}
        onSearchResults={(results) => {
          // Log search activity
          logAccess(
            userId,
            userRole,
            'SEARCH_MEMBERS',
            'MemberDatabase',
            'search-results',
            purpose,
            PDPLLegalBasis.LEGITIMATE_INTERESTS,
            [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
            true,
            { resultCount: results.length }
          );
        }}
      />

      {/* Selected Member Display */}
      {selectedMember && maskedMember && (
        <div className="space-y-6">
          {/* Member Profile with Privacy Controls */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Shield className="h-6 w-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Privacy-Protected Member Profile
                </h2>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600">
                  Viewing as: {userRole} | Purpose: {purpose}
                </span>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowProfile(!showProfile)}
                >
                  {showProfile ? <EyeOff className="h-4 w-4 mr-1" /> : <Eye className="h-4 w-4 mr-1" />}
                  {showProfile ? 'Hide' : 'Show'} Full Profile
                </Button>
              </div>
            </div>

            {/* Privacy-aware member card */}
            <PrivacyAwareMemberCard member={selectedMember} />

            {/* Full profile view */}
            {showProfile && (
              <div className="mt-6 border-t pt-6">
                <MemberProfile
                  memberId={selectedMember.id}
                  className="privacy-protected"
                />
              </div>
            )}
          </Card>

          {/* Care Alerts with Privacy Context */}
          <AlertsPanel
            memberId={selectedMember.id}
            member={selectedMember}
            onAlertClick={(alert) => {
              logAccess(
                userId,
                userRole,
                'VIEW_CARE_ALERT',
                'CareGap',
                alert.id,
                purpose,
                PDPLLegalBasis.LEGITIMATE_INTERESTS,
                [PDPLDataCategory.HEALTH_DATA],
                true
              );
            }}
          />
        </div>
      )}

      {/* Consent Modal */}
      {showConsentModal && (
        <Modal
          isOpen={showConsentModal}
          onClose={() => setShowConsentModal(false)}
          title="Record Member Consent"
          size="lg"
        >
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-start">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
                <div>
                  <h3 className="text-sm font-medium text-blue-800">UAE PDPL Compliance</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    Processing of health data requires explicit consent under UAE Personal Data Protection Law.
                    Please record the member's consent for the intended processing purpose.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Consent Details</h3>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="dataProcessing"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      onChange={(e) => setUserConsents(prev => ({ ...prev, dataProcessing: e.target.checked }))}
                    />
                    <label htmlFor="dataProcessing" className="ml-2 text-sm text-gray-700">
                      I consent to the processing of my personal health data for {purpose}
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="dataSharing"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      onChange={(e) => setUserConsents(prev => ({ ...prev, dataSharing: e.target.checked }))}
                    />
                    <label htmlFor="dataSharing" className="ml-2 text-sm text-gray-700">
                      I consent to sharing my data with authorized healthcare providers
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="dataRetention"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      onChange={(e) => setUserConsents(prev => ({ ...prev, dataRetention: e.target.checked }))}
                    />
                    <label htmlFor="dataRetention" className="ml-2 text-sm text-gray-700">
                      I understand my data will be retained as per the privacy policy
                    </label>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Your Rights</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Right to access your personal data</li>
                  <li>• Right to rectify incorrect data</li>
                  <li>• Right to erase your data</li>
                  <li>• Right to restrict processing</li>
                  <li>• Right to data portability</li>
                  <li>• Right to object to processing</li>
                  <li>• Right to withdraw consent at any time</li>
                </ul>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowConsentModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={() => handleConsentRecording(userConsents)}
                disabled={!userConsents.dataProcessing}
              >
                <Lock className="h-4 w-4 mr-1" />
                Record Consent
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default PrivacyAwareMemberSearch;

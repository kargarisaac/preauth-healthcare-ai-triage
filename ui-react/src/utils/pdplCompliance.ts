/**
 * UAE Personal Data Protection Law (PDPL) Compliance Utilities
 *
 * This module provides utilities for ensuring compliance with UAE Federal Decree Law No. 45 of 2021
 * on the Protection of Personal Data (PDPL) for healthcare applications.
 */

import { Member } from '../types/healthcare';

// PDPL Data Categories
export enum PDPLDataCategory {
  PERSONAL_IDENTIFIABLE = 'personal_identifiable',
  SENSITIVE_PERSONAL = 'sensitive_personal',
  HEALTH_DATA = 'health_data',
  FINANCIAL_DATA = 'financial_data',
  LOCATION_DATA = 'location_data',
  BIOMETRIC_DATA = 'biometric_data'
}

// PDPL Processing Purposes
export enum PDPLProcessingPurpose {
  HEALTHCARE_TREATMENT = 'healthcare_treatment',
  INSURANCE_CLAIMS = 'insurance_claims',
  PREVENTIVE_CARE = 'preventive_care',
  QUALITY_IMPROVEMENT = 'quality_improvement',
  RESEARCH_ANONYMIZED = 'research_anonymized',
  REGULATORY_COMPLIANCE = 'regulatory_compliance',
  EMERGENCY_CARE = 'emergency_care'
}

// PDPL Legal Basis
export enum PDPLLegalBasis {
  CONSENT = 'consent',
  CONTRACT = 'contract',
  LEGAL_OBLIGATION = 'legal_obligation',
  VITAL_INTERESTS = 'vital_interests',
  PUBLIC_TASK = 'public_task',
  LEGITIMATE_INTERESTS = 'legitimate_interests'
}

// Data Subject Rights
export enum DataSubjectRight {
  ACCESS = 'access',
  RECTIFICATION = 'rectification',
  ERASURE = 'erasure',
  RESTRICTION = 'restriction',
  PORTABILITY = 'portability',
  OBJECTION = 'objection',
  WITHDRAW_CONSENT = 'withdraw_consent'
}

// Consent Record
export interface ConsentRecord {
  id: string;
  memberId: string;
  purpose: PDPLProcessingPurpose;
  legalBasis: PDPLLegalBasis;
  consentDate: string;
  expiryDate?: string;
  withdrawn: boolean;
  withdrawnDate?: string;
  version: string;
  specificConsents: {
    dataProcessing: boolean;
    dataSharing: boolean;
    marketingCommunications: boolean;
    dataRetention: boolean;
    internationalTransfer: boolean;
  };
  metadata: {
    ipAddress?: string;
    userAgent?: string;
    consentMethod: 'explicit' | 'implied' | 'opt_in' | 'opt_out';
    witnessedBy?: string;
  };
}

// Privacy Settings
export interface PrivacySettings {
  memberId: string;
  dataMinimization: boolean;
  pseudonymization: boolean;
  dataRetentionPeriod: number; // in days
  automaticDeletion: boolean;
  accessRestrictions: {
    roles: string[];
    departments: string[];
    purposes: PDPLProcessingPurpose[];
  };
  auditLogging: boolean;
  dataExportFormat: 'json' | 'xml' | 'csv' | 'pdf';
  notificationPreferences: {
    dataProcessing: boolean;
    policyUpdates: boolean;
    securityIncidents: boolean;
    dataRetention: boolean;
  };
}

// Audit Log Entry
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  userRole: string;
  action: string;
  resource: string;
  resourceId: string;
  purpose: PDPLProcessingPurpose;
  legalBasis: PDPLLegalBasis;
  dataCategories: PDPLDataCategory[];
  success: boolean;
  ipAddress: string;
  userAgent: string;
  details?: Record<string, any>;
}

// Data Classification Map
const DATA_CLASSIFICATION_MAP: Record<string, PDPLDataCategory[]> = {
  'demographics.firstName': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'demographics.lastName': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'demographics.fullName': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'demographics.dateOfBirth': [PDPLDataCategory.PERSONAL_IDENTIFIABLE, PDPLDataCategory.SENSITIVE_PERSONAL],
  'demographics.gender': [PDPLDataCategory.SENSITIVE_PERSONAL],
  'demographics.nationality': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'emirates': [PDPLDataCategory.PERSONAL_IDENTIFIABLE, PDPLDataCategory.SENSITIVE_PERSONAL],
  'contact.phone': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'contact.email': [PDPLDataCategory.PERSONAL_IDENTIFIABLE],
  'contact.address': [PDPLDataCategory.PERSONAL_IDENTIFIABLE, PDPLDataCategory.LOCATION_DATA],
  'insurance': [PDPLDataCategory.FINANCIAL_DATA, PDPLDataCategory.SENSITIVE_PERSONAL],
  'medicalHistory': [PDPLDataCategory.HEALTH_DATA, PDPLDataCategory.SENSITIVE_PERSONAL],
  'costUtilization': [PDPLDataCategory.FINANCIAL_DATA, PDPLDataCategory.HEALTH_DATA],
  'riskScore': [PDPLDataCategory.HEALTH_DATA, PDPLDataCategory.SENSITIVE_PERSONAL]
};

// Sensitive field patterns
const SENSITIVE_FIELD_PATTERNS = [
  /emirates?[_-]?id/i,
  /ssn|social[_-]?security/i,
  /password|pwd|secret/i,
  /credit[_-]?card|payment/i,
  /medical[_-]?record/i,
  /diagnosis|condition|disease/i,
  /medication|prescription/i,
  /biometric|fingerprint|iris/i
];

/**
 * PDPL Compliance Manager
 */
export class PDPLComplianceManager {
  private static instance: PDPLComplianceManager;
  private auditLogs: AuditLogEntry[] = [];
  private consentRecords: Map<string, ConsentRecord[]> = new Map();
  private privacySettings: Map<string, PrivacySettings> = new Map();

  static getInstance(): PDPLComplianceManager {
    if (!PDPLComplianceManager.instance) {
      PDPLComplianceManager.instance = new PDPLComplianceManager();
    }
    return PDPLComplianceManager.instance;
  }

  /**
   * Classify data fields based on PDPL categories
   */
  classifyDataField(fieldPath: string): PDPLDataCategory[] {
    // Check exact matches first
    if (DATA_CLASSIFICATION_MAP[fieldPath]) {
      return DATA_CLASSIFICATION_MAP[fieldPath];
    }

    // Check pattern matches
    const categories: PDPLDataCategory[] = [];

    if (SENSITIVE_FIELD_PATTERNS.some(pattern => pattern.test(fieldPath))) {
      categories.push(PDPLDataCategory.SENSITIVE_PERSONAL);
    }

    if (fieldPath.includes('medical') || fieldPath.includes('health')) {
      categories.push(PDPLDataCategory.HEALTH_DATA);
    }

    if (fieldPath.includes('location') || fieldPath.includes('address')) {
      categories.push(PDPLDataCategory.LOCATION_DATA);
    }

    if (fieldPath.includes('financial') || fieldPath.includes('cost') || fieldPath.includes('payment')) {
      categories.push(PDPLDataCategory.FINANCIAL_DATA);
    }

    // Default to personal identifiable if no specific category found
    if (categories.length === 0) {
      categories.push(PDPLDataCategory.PERSONAL_IDENTIFIABLE);
    }

    return categories;
  }

  /**
   * Check if processing is allowed based on consent and legal basis
   */
  isProcessingAllowed(
    memberId: string,
    purpose: PDPLProcessingPurpose,
    dataCategories: PDPLDataCategory[]
  ): boolean {
    const consents = this.consentRecords.get(memberId) || [];
    const relevantConsent = consents.find(c =>
      c.purpose === purpose &&
      !c.withdrawn &&
      (!c.expiryDate || new Date(c.expiryDate) > new Date())
    );

    if (!relevantConsent) {
      return false;
    }

    // Special handling for sensitive data
    if (dataCategories.includes(PDPLDataCategory.HEALTH_DATA) ||
        dataCategories.includes(PDPLDataCategory.SENSITIVE_PERSONAL)) {
      return relevantConsent.legalBasis === PDPLLegalBasis.CONSENT ||
             relevantConsent.legalBasis === PDPLLegalBasis.VITAL_INTERESTS;
    }

    return true;
  }

  /**
   * Pseudonymize sensitive data
   */
  pseudonymizeData<T>(data: T, memberId: string): T {
    const settings = this.privacySettings.get(memberId);
    if (!settings?.pseudonymization) {
      return data;
    }

    const pseudonymized = JSON.parse(JSON.stringify(data));

    // Replace sensitive identifiers with hashed versions
    if (typeof pseudonymized === 'object' && pseudonymized !== null) {
      this.recursivePseudonymize(pseudonymized, memberId);
    }

    return pseudonymized;
  }

  private recursivePseudonymize(obj: any, memberId: string, path = ''): void {
    Object.keys(obj).forEach(key => {
      const currentPath = path ? `${path}.${key}` : key;
      const value = obj[key];

      if (typeof value === 'object' && value !== null) {
        this.recursivePseudonymize(value, memberId, currentPath);
      } else if (typeof value === 'string') {
        const categories = this.classifyDataField(currentPath);

        if (categories.includes(PDPLDataCategory.SENSITIVE_PERSONAL) ||
            categories.includes(PDPLDataCategory.PERSONAL_IDENTIFIABLE)) {
          obj[key] = this.hashValue(value, memberId);
        }
      }
    });
  }

  private hashValue(value: string, salt: string): string {
    // Simple hash function - in production, use a proper cryptographic hash
    let hash = 0;
    const input = value + salt;

    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return `***${Math.abs(hash).toString(36).substring(0, 6)}***`;
  }

  /**
   * Mask sensitive member data for display
   */
  maskMemberData(member: Member, userRole: string, purpose: PDPLProcessingPurpose): Partial<Member> {
    const maskedMember = JSON.parse(JSON.stringify(member));

    // Role-based access control
    switch (userRole) {
      case 'admin':
        // Admins get full access
        break;
      case 'doctor':
        // Doctors get medical data but limited financial info
        if (maskedMember.costUtilization) {
          delete maskedMember.costUtilization.topCategories;
          delete maskedMember.costUtilization.monthlyTrends;
        }
        break;
      case 'nurse':
        // Nurses get limited medical data
        if (maskedMember.medicalHistory) {
          delete maskedMember.medicalHistory.familyHistory;
        }
        if (maskedMember.costUtilization) {
          delete maskedMember.costUtilization;
        }
        break;
      case 'financial':
        // Financial staff get limited access to medical data
        if (maskedMember.medicalHistory) {
          maskedMember.medicalHistory = {
            allergies: maskedMember.medicalHistory.allergies,
            chronicConditions: maskedMember.medicalHistory.chronicConditions.map((c: any) => ({
              id: c.id,
              condition: c.condition,
              status: c.status
            })),
            surgicalHistory: [],
            familyHistory: []
          };
        }
        break;
      default:
        // Default role gets minimal access
        this.applyMinimalAccess(maskedMember);
    }

    // Purpose-based restrictions
    if (purpose === PDPLProcessingPurpose.RESEARCH_ANONYMIZED) {
      delete maskedMember.demographics.firstName;
      delete maskedMember.demographics.lastName;
      delete maskedMember.demographics.fullName;
      delete maskedMember.emiratesId;
      delete maskedMember.contact;
      delete maskedMember.insurance.policyNumber;
    }

    return maskedMember;
  }

  private applyMinimalAccess(member: any): void {
    // Remove sensitive personal identifiable information
    delete member.emiratesId;
    delete member.contact.phone;
    delete member.contact.email;
    delete member.contact.address;
    delete member.insurance.policyNumber;
    delete member.insurance.groupNumber;
    delete member.medicalHistory;
    delete member.costUtilization;
  }

  /**
   * Log data access for audit purposes
   */
  logDataAccess(
    userId: string,
    userRole: string,
    action: string,
    resource: string,
    resourceId: string,
    purpose: PDPLProcessingPurpose,
    legalBasis: PDPLLegalBasis,
    dataCategories: PDPLDataCategory[],
    success: boolean,
    request: any = {}
  ): void {
    const auditEntry: AuditLogEntry = {
      id: `audit-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      userId,
      userRole,
      action,
      resource,
      resourceId,
      purpose,
      legalBasis,
      dataCategories,
      success,
      ipAddress: request.ip || 'unknown',
      userAgent: request.headers?.['user-agent'] || 'unknown',
      details: {
        fieldsAccessed: request.fieldsAccessed || [],
        searchQuery: request.searchQuery || null,
        filters: request.filters || {}
      }
    };

    this.auditLogs.push(auditEntry);

    // In production, this should be sent to a secure audit logging service
    console.log('[PDPL Audit]', auditEntry);

    // Cleanup old logs (keep last 10000 entries)
    if (this.auditLogs.length > 10000) {
      this.auditLogs = this.auditLogs.slice(-10000);
    }
  }

  /**
   * Record consent
   */
  recordConsent(consentRecord: ConsentRecord): void {
    const memberConsents = this.consentRecords.get(consentRecord.memberId) || [];
    memberConsents.push(consentRecord);
    this.consentRecords.set(consentRecord.memberId, memberConsents);
  }

  /**
   * Withdraw consent
   */
  withdrawConsent(memberId: string, purpose: PDPLProcessingPurpose): void {
    const consents = this.consentRecords.get(memberId) || [];
    const consent = consents.find(c => c.purpose === purpose && !c.withdrawn);

    if (consent) {
      consent.withdrawn = true;
      consent.withdrawnDate = new Date().toISOString();
    }
  }

  /**
   * Set privacy settings for a member
   */
  setPrivacySettings(settings: PrivacySettings): void {
    this.privacySettings.set(settings.memberId, settings);
  }

  /**
   * Get privacy settings for a member
   */
  getPrivacySettings(memberId: string): PrivacySettings | null {
    return this.privacySettings.get(memberId) || null;
  }

  /**
   * Check data retention compliance
   */
  checkDataRetention(member: Member): {
    shouldRetain: boolean;
    deleteAfter?: string;
    reason: string;
  } {
    const settings = this.privacySettings.get(member.id);
    const createdDate = new Date(member.createdAt);
    const retentionPeriod = settings?.dataRetentionPeriod || 2555; // Default 7 years in days
    const deleteAfter = new Date(createdDate.getTime() + retentionPeriod * 24 * 60 * 60 * 1000);

    if (new Date() > deleteAfter) {
      return {
        shouldRetain: false,
        deleteAfter: deleteAfter.toISOString(),
        reason: 'Data retention period exceeded'
      };
    }

    // Check if member has active insurance or ongoing treatment
    if (member.insurance.status === 'active') {
      return {
        shouldRetain: true,
        reason: 'Active insurance policy'
      };
    }

    // Check for active chronic conditions requiring ongoing care
    const activeConditions = member.medicalHistory.chronicConditions.filter(
      c => c.status === 'active' || c.status === 'chronic'
    );

    if (activeConditions.length > 0) {
      return {
        shouldRetain: true,
        reason: 'Active chronic conditions requiring ongoing care'
      };
    }

    return {
      shouldRetain: true,
      deleteAfter: deleteAfter.toISOString(),
      reason: 'Within retention period'
    };
  }

  /**
   * Export member data in compliance with data portability rights
   */
  exportMemberData(memberId: string, format: 'json' | 'xml' | 'csv' | 'pdf' = 'json'): any {
    // This would integrate with the actual data source
    // For now, returning a placeholder structure

    const exportData = {
      exportDate: new Date().toISOString(),
      exportedBy: 'system',
      memberId,
      format,
      dataCategories: [
        PDPLDataCategory.PERSONAL_IDENTIFIABLE,
        PDPLDataCategory.HEALTH_DATA,
        PDPLDataCategory.FINANCIAL_DATA
      ],
      notice: 'This export contains all personal data we hold about you as per UAE PDPL Article 13',
      contactInfo: {
        dataProtectionOfficer: 'dpo@healthcare-preauth.com',
        phone: '+971-4-XXX-XXXX'
      },
      data: {
        // Member data would be included here
        // Structure depends on format requested
      }
    };

    return exportData;
  }

  /**
   * Get audit logs for a member
   */
  getAuditLogs(memberId: string): AuditLogEntry[] {
    return this.auditLogs.filter(log => log.resourceId === memberId);
  }
}

// Utility functions for React components
export const usePDPLCompliance = () => {
  const compliance = PDPLComplianceManager.getInstance();

  return {
    classifyField: (field: string) => compliance.classifyDataField(field),
    checkProcessing: (memberId: string, purpose: PDPLProcessingPurpose, categories: PDPLDataCategory[]) =>
      compliance.isProcessingAllowed(memberId, purpose, categories),
    maskData: (member: Member, role: string, purpose: PDPLProcessingPurpose) =>
      compliance.maskMemberData(member, role, purpose),
    logAccess: (userId: string, userRole: string, action: string, resource: string, resourceId: string, purpose: PDPLProcessingPurpose, legalBasis: PDPLLegalBasis, categories: PDPLDataCategory[], success: boolean, request?: any) =>
      compliance.logDataAccess(userId, userRole, action, resource, resourceId, purpose, legalBasis, categories, success, request),
    recordConsent: (consent: ConsentRecord) => compliance.recordConsent(consent),
    withdrawConsent: (memberId: string, purpose: PDPLProcessingPurpose) => compliance.withdrawConsent(memberId, purpose),
    exportData: (memberId: string, format?: 'json' | 'xml' | 'csv' | 'pdf') => compliance.exportMemberData(memberId, format),
    checkRetention: (member: Member) => compliance.checkDataRetention(member)
  };
};

// Default privacy settings
export const DEFAULT_PRIVACY_SETTINGS: Omit<PrivacySettings, 'memberId'> = {
  dataMinimization: true,
  pseudonymization: false,
  dataRetentionPeriod: 2555, // 7 years in days
  automaticDeletion: false,
  accessRestrictions: {
    roles: ['admin', 'doctor', 'nurse'],
    departments: ['clinical', 'administration'],
    purposes: [
      PDPLProcessingPurpose.HEALTHCARE_TREATMENT,
      PDPLProcessingPurpose.INSURANCE_CLAIMS,
      PDPLProcessingPurpose.PREVENTIVE_CARE
    ]
  },
  auditLogging: true,
  dataExportFormat: 'json',
  notificationPreferences: {
    dataProcessing: true,
    policyUpdates: true,
    securityIncidents: true,
    dataRetention: false
  }
};

export default PDPLComplianceManager;

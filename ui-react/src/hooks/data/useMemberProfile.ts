import { useState, useEffect, useCallback } from 'react';
import {
  Member,
  MemberActivity,
  AuthorizationHistory,
  CostUtilization
} from '../../types/healthcare';

interface MemberProfileState {
  member: Member | null;
  activities: MemberActivity[];
  authorizationHistory: AuthorizationHistory[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

export const useMemberProfile = (memberId?: string) => {
  const [state, setState] = useState<MemberProfileState>({
    member: null,
    activities: [],
    authorizationHistory: [],
    isLoading: false,
    error: null,
    lastUpdated: null
  });

  // Mock API calls - replace with actual API integration
  const fetchMemberAPI = async (id: string): Promise<Member> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    // Mock member data
    return {
      id,
      emiratesId: '784-1234-5678901-0',
      demographics: {
        firstName: 'Ahmed',
        lastName: 'Al Mansouri',
        fullName: 'Ahmed Al Mansouri',
        dateOfBirth: '1985-03-15',
        gender: 'male',
        nationality: 'UAE',
        preferredLanguage: 'Arabic',
        maritalStatus: 'married'
      },
      contact: {
        phone: '+971501234567',
        alternativePhone: '+971508765432',
        email: 'ahmed.almansouri@email.com',
        address: {
          street: 'Al Wasl Road, Villa 123',
          city: 'Dubai',
          emirate: 'Dubai',
          country: 'UAE',
          postalCode: '12345'
        },
        emergencyContact: {
          name: 'Fatima Al Mansouri',
          relationship: 'Spouse',
          phone: '+971507654321'
        }
      },
      insurance: {
        provider: 'Dubai Health Insurance',
        policyNumber: 'DHI-789456123',
        groupNumber: 'GRP-001',
        planType: 'Gold Plus',
        effectiveDate: '2024-01-01',
        expirationDate: '2024-12-31',
        deductible: 1000,
        coPayment: 20,
        outOfPocketMax: 5000,
        benefitYear: '2024',
        status: 'active'
      },
      medicalHistory: {
        allergies: [
          { allergen: 'Penicillin', severity: 'severe', reaction: 'Anaphylaxis' },
          { allergen: 'Shellfish', severity: 'moderate', reaction: 'Hives' }
        ],
        chronicConditions: [
          {
            id: '1',
            condition: 'Type 2 Diabetes',
            icdCode: 'E11.9',
            diagnosisDate: '2020-05-10',
            severity: 'moderate',
            status: 'chronic',
            managingProvider: 'Dr. Sarah Johnson',
            medications: ['Metformin 500mg', 'Insulin Glargine'],
            lastReview: '2024-06-15'
          },
          {
            id: '2',
            condition: 'Hypertension',
            icdCode: 'I10',
            diagnosisDate: '2021-08-22',
            severity: 'mild',
            status: 'chronic',
            managingProvider: 'Dr. Sarah Johnson',
            medications: ['Lisinopril 10mg'],
            lastReview: '2024-07-10'
          }
        ],
        surgicalHistory: [
          {
            procedure: 'Appendectomy',
            date: '2010-03-15',
            hospital: 'Dubai Hospital',
            complications: 'None'
          }
        ],
        familyHistory: [
          { relationship: 'Father', condition: 'Diabetes', ageOfOnset: 55 },
          { relationship: 'Mother', condition: 'Hypertension', ageOfOnset: 60 }
        ]
      },
      costUtilization: {
        yearToDate: {
          totalCosts: 18500,
          memberPaid: 3700,
          planPaid: 14800,
          deductibleMet: 1000,
          outOfPocketMet: 2700
        },
        monthlyTrends: [
          { month: '2024-01', totalCosts: 2200, visits: 3, prescriptions: 4 },
          { month: '2024-02', totalCosts: 1800, visits: 2, prescriptions: 3 },
          { month: '2024-03', totalCosts: 2500, visits: 4, prescriptions: 5 },
          { month: '2024-04', totalCosts: 1900, visits: 2, prescriptions: 3 },
          { month: '2024-05', totalCosts: 3200, visits: 5, prescriptions: 6 },
          { month: '2024-06', totalCosts: 2100, visits: 3, prescriptions: 4 },
          { month: '2024-07', totalCosts: 4800, visits: 6, prescriptions: 7 }
        ],
        topCategories: [
          { category: 'Medications', amount: 9500, percentage: 51.4 },
          { category: 'Outpatient Visits', amount: 6000, percentage: 32.4 },
          { category: 'Laboratory Tests', amount: 2000, percentage: 10.8 },
          { category: 'Imaging', amount: 1000, percentage: 5.4 }
        ]
      },
      recentRequests: [],
      riskScore: 75,
      lastActivity: '2024-07-28T10:30:00Z',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-07-28T10:30:00Z'
    };
  };

  const fetchMemberActivitiesAPI = async (id: string): Promise<MemberActivity[]> => {
    await new Promise(resolve => setTimeout(resolve, 200));

    return [
      {
        id: '1',
        memberId: id,
        type: 'authorization',
        title: 'Pre-authorization Request',
        description: 'MRI scan for lower back pain evaluation',
        status: 'approved',
        amount: 2500,
        provider: 'Dubai Imaging Center',
        outcome: 'Approved within 24 hours',
        timestamp: '2024-07-28T10:30:00Z',
        metadata: {
          serviceCode: 'MRI-001',
          approvalNumber: 'AUTH-789123',
          validUntil: '2024-08-28'
        }
      },
      {
        id: '2',
        memberId: id,
        type: 'claim',
        title: 'Claim Processed',
        description: 'Endocrinologist consultation for diabetes management',
        status: 'paid',
        amount: 450,
        provider: 'Dr. Sarah Johnson Clinic',
        outcome: 'Paid in full',
        timestamp: '2024-07-25T14:15:00Z',
        metadata: {
          claimNumber: 'CLM-456789',
          serviceDate: '2024-07-20',
          copayAmount: 90
        }
      },
      {
        id: '3',
        memberId: id,
        type: 'care_gap',
        title: 'Care Gap Identified',
        description: 'Due for annual diabetic eye exam',
        status: 'open',
        provider: 'Care Management Team',
        outcome: 'Notification sent to member',
        timestamp: '2024-07-22T09:00:00Z',
        metadata: {
          gapType: 'preventive',
          dueDate: '2024-08-15',
          priority: 'medium'
        }
      },
      {
        id: '4',
        memberId: id,
        type: 'appointment',
        title: 'Appointment Scheduled',
        description: 'Follow-up with cardiologist for hypertension',
        status: 'scheduled',
        provider: 'Dr. Ahmed Hassan',
        timestamp: '2024-07-20T11:20:00Z',
        metadata: {
          appointmentDate: '2024-08-05T10:00:00Z',
          location: 'Dubai Heart Center',
          type: 'follow-up'
        }
      }
    ];
  };

  const fetchAuthorizationHistoryAPI = async (id: string): Promise<AuthorizationHistory[]> => {
    await new Promise(resolve => setTimeout(resolve, 200));

    return [
      {
        id: '1',
        requestDate: '2024-07-28',
        serviceType: 'Diagnostic Imaging - MRI',
        provider: 'Dubai Imaging Center',
        requestedAmount: 2500,
        approvedAmount: 2500,
        status: 'approved',
        decisionReason: 'Medical necessity established',
        reviewNotes: 'Patient has chronic lower back pain with new neurological symptoms',
        reviewedBy: 'Dr. Medical Director',
        reviewDate: '2024-07-28',
        appealStatus: 'none'
      },
      {
        id: '2',
        requestDate: '2024-06-15',
        serviceType: 'Specialist Consultation - Orthopedic',
        provider: 'Dr. Omar Al Rashid',
        requestedAmount: 600,
        approvedAmount: 600,
        status: 'approved',
        decisionReason: 'Referral from primary care physician',
        reviewedBy: 'Automated System',
        reviewDate: '2024-06-15',
        appealStatus: 'none'
      },
      {
        id: '3',
        requestDate: '2024-05-20',
        serviceType: 'Physical Therapy - 12 sessions',
        provider: 'Dubai Rehabilitation Center',
        requestedAmount: 1800,
        approvedAmount: 1200,
        status: 'approved',
        decisionReason: 'Approved for 8 sessions initially',
        reviewNotes: 'Member can request additional sessions after progress review',
        reviewedBy: 'Dr. Clinical Reviewer',
        reviewDate: '2024-05-21',
        appealStatus: 'none'
      },
      {
        id: '4',
        requestDate: '2024-04-10',
        serviceType: 'Prescription - Specialty Medication',
        provider: 'Al Noor Pharmacy',
        requestedAmount: 2800,
        status: 'denied',
        decisionReason: 'Alternative, equally effective medication available',
        reviewNotes: 'Generic equivalent available at 60% cost savings',
        reviewedBy: 'PharmD Clinical Reviewer',
        reviewDate: '2024-04-12',
        appealStatus: 'filed'
      }
    ];
  };

  // Load member profile
  const loadMemberProfile = useCallback(async (id: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [member, activities, authHistory] = await Promise.all([
        fetchMemberAPI(id),
        fetchMemberActivitiesAPI(id),
        fetchAuthorizationHistoryAPI(id)
      ]);

      setState({
        member,
        activities,
        authorizationHistory: authHistory,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString()
      });
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load member profile'
      }));
    }
  }, []);

  // Update member information
  const updateMemberInfo = useCallback(async (
    memberId: string,
    updates: Partial<Member>
  ) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 500));

      setState(prev => ({
        ...prev,
        member: prev.member ? { ...prev.member, ...updates } : null,
        isLoading: false,
        lastUpdated: new Date().toISOString()
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to update member'
      }));
    }
  }, []);

  // Refresh member data
  const refreshMemberData = useCallback(async () => {
    if (state.member?.id) {
      await loadMemberProfile(state.member.id);
    }
  }, [state.member?.id, loadMemberProfile]);

  // Calculate member insights
  const getMemberInsights = useCallback(() => {
    if (!state.member) return null;

    const { costUtilization, medicalHistory, riskScore } = state.member;

    return {
      riskLevel: riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : 'low',
      totalYearToDateCosts: costUtilization.yearToDate.totalCosts,
      remainingDeductible: Math.max(0, state.member.insurance.deductible - costUtilization.yearToDate.deductibleMet),
      remainingOutOfPocket: Math.max(0, state.member.insurance.outOfPocketMax - costUtilization.yearToDate.outOfPocketMet),
      chronicConditionsCount: medicalHistory.chronicConditions.length,
      activeConditions: medicalHistory.chronicConditions.filter(c => c.status === 'chronic' || c.status === 'active'),
      severityScore: medicalHistory.chronicConditions.reduce((acc, condition) => {
        const severityWeights = { mild: 1, moderate: 2, severe: 3 };
        return acc + (severityWeights[condition.severity] || 0);
      }, 0),
      lastActivityDays: state.member.lastActivity ?
        Math.floor((new Date().getTime() - new Date(state.member.lastActivity).getTime()) / (1000 * 60 * 60 * 24)) : 0
    };
  }, [state.member]);

  // Get cost trends analysis
  const getCostTrends = useCallback(() => {
    if (!state.member?.costUtilization.monthlyTrends) return null;

    const trends = state.member.costUtilization.monthlyTrends;
    const currentMonth = trends[trends.length - 1];
    const previousMonth = trends[trends.length - 2];

    return {
      currentMonthCosts: currentMonth?.totalCosts || 0,
      previousMonthCosts: previousMonth?.totalCosts || 0,
      costChange: currentMonth && previousMonth ?
        ((currentMonth.totalCosts - previousMonth.totalCosts) / previousMonth.totalCosts) * 100 : 0,
      averageMonthlyCosts: trends.reduce((sum, month) => sum + month.totalCosts, 0) / trends.length,
      highestMonth: trends.reduce((max, month) =>
        month.totalCosts > max.totalCosts ? month : max, trends[0]),
      lowestMonth: trends.reduce((min, month) =>
        month.totalCosts < min.totalCosts ? month : min, trends[0])
    };
  }, [state.member?.costUtilization.monthlyTrends]);

  // Auto-load member if ID provided
  useEffect(() => {
    if (memberId && memberId !== state.member?.id) {
      loadMemberProfile(memberId);
    }
  }, [memberId, state.member?.id, loadMemberProfile]);

  return {
    // State
    member: state.member,
    activities: state.activities,
    authorizationHistory: state.authorizationHistory,
    isLoading: state.isLoading,
    error: state.error,
    lastUpdated: state.lastUpdated,

    // Actions
    loadMemberProfile,
    updateMemberInfo,
    refreshMemberData,

    // Analytics
    getMemberInsights,
    getCostTrends
  };
};

export default useMemberProfile;

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CareGap,
  InterventionRecommendation,
  QualityMetric,
  Member,
  ChronicCondition
} from '../../types/healthcare';

interface CareGapAnalysis {
  totalGaps: number;
  urgentGaps: number;
  highPriorityGaps: number;
  potentialSavings: number;
  completionRate: number;
  averageDaysOverdue: number;
}

interface CareGapState {
  careGaps: CareGap[];
  recommendations: InterventionRecommendation[];
  qualityMetrics: QualityMetric[];
  analysis: CareGapAnalysis;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

export const useCareGaps = (memberId?: string) => {
  const [state, setState] = useState<CareGapState>({
    careGaps: [],
    recommendations: [],
    qualityMetrics: [],
    analysis: {
      totalGaps: 0,
      urgentGaps: 0,
      highPriorityGaps: 0,
      potentialSavings: 0,
      completionRate: 0,
      averageDaysOverdue: 0
    },
    isLoading: false,
    error: null,
    lastUpdated: null
  });

  // Mock API calls - replace with actual clinical decision support system
  const fetchCareGapsAPI = async (id: string): Promise<CareGap[]> => {
    await new Promise(resolve => setTimeout(resolve, 400));

    return [
      {
        id: '1',
        memberId: id,
        type: 'preventive',
        category: 'Diabetic Eye Exam',
        description: 'Annual comprehensive eye examination for diabetic retinopathy screening',
        recommendation: 'Schedule ophthalmology appointment within 30 days',
        priority: 'high',
        dueDate: '2024-08-15',
        status: 'open',
        evidenceBase: 'ADA Clinical Practice Guidelines - Annual eye exams recommended for all diabetic patients',
        potentialCostSaving: 15000, // Cost of treating advanced retinopathy
        assignedProvider: 'Dubai Eye Institute',
        createdAt: '2024-07-22T09:00:00Z',
        updatedAt: '2024-07-22T09:00:00Z'
      },
      {
        id: '2',
        memberId: id,
        type: 'chronic_care',
        category: 'HbA1c Testing',
        description: 'Quarterly HbA1c testing for diabetes management',
        recommendation: 'Schedule laboratory test - last HbA1c was 4 months ago',
        priority: 'medium',
        dueDate: '2024-08-01',
        status: 'open',
        evidenceBase: 'ADA Standards of Medical Care - HbA1c every 3 months for uncontrolled diabetes',
        potentialCostSaving: 8000, // Cost of diabetes complications
        createdAt: '2024-07-20T14:30:00Z',
        updatedAt: '2024-07-20T14:30:00Z'
      },
      {
        id: '3',
        memberId: id,
        type: 'medication_adherence',
        category: 'Medication Refill Gap',
        description: 'Member has not refilled Metformin prescription in 45 days',
        recommendation: 'Contact member to address potential medication adherence issues',
        priority: 'urgent',
        dueDate: '2024-07-30',
        status: 'open',
        evidenceBase: 'Medication adherence critical for diabetes control and complication prevention',
        potentialCostSaving: 12000, // Cost of uncontrolled diabetes
        createdAt: '2024-07-28T08:15:00Z',
        updatedAt: '2024-07-28T08:15:00Z'
      },
      {
        id: '4',
        memberId: id,
        type: 'follow_up',
        category: 'Cardiology Follow-up',
        description: 'Overdue follow-up appointment for hypertension management',
        recommendation: 'Schedule cardiology appointment within 2 weeks',
        priority: 'high',
        dueDate: '2024-07-25',
        status: 'scheduled',
        evidenceBase: 'AHA/ACC Hypertension Guidelines - Regular follow-up for medication adjustment',
        potentialCostSaving: 25000, // Cost of cardiovascular events
        assignedProvider: 'Dr. Ahmed Hassan - Dubai Heart Center',
        createdAt: '2024-07-15T11:00:00Z',
        updatedAt: '2024-07-29T16:20:00Z'
      },
      {
        id: '5',
        memberId: id,
        type: 'preventive',
        category: 'Nephrology Screening',
        description: 'Annual kidney function assessment for diabetic nephropathy screening',
        recommendation: 'Order microalbuminuria and serum creatinine tests',
        priority: 'medium',
        dueDate: '2024-09-01',
        status: 'open',
        evidenceBase: 'KDOQI Guidelines - Annual screening for diabetic kidney disease',
        potentialCostSaving: 45000, // Cost of dialysis and kidney disease management
        createdAt: '2024-07-25T13:45:00Z',
        updatedAt: '2024-07-25T13:45:00Z'
      }
    ];
  };

  const fetchRecommendationsAPI = async (id: string): Promise<InterventionRecommendation[]> => {
    await new Promise(resolve => setTimeout(resolve, 300));

    return [
      {
        id: '1',
        memberId: id,
        type: 'lifestyle',
        title: 'Diabetes Self-Management Education',
        description: 'Enroll in structured diabetes education program to improve self-care behaviors',
        expectedOutcome: '15-20% improvement in HbA1c levels and better medication adherence',
        timeframe: '3-6 months',
        priority: 'high',
        costEstimate: 800,
        qualityMeasure: 'HbA1c <7%',
        status: 'recommended'
      },
      {
        id: '2',
        memberId: id,
        type: 'medication',
        title: 'Medication Therapy Management',
        description: 'Comprehensive medication review with clinical pharmacist',
        expectedOutcome: 'Reduced medication errors, improved adherence, potential cost savings',
        timeframe: '1-2 sessions over 3 months',
        priority: 'medium',
        costEstimate: 300,
        qualityMeasure: 'Medication adherence >80%',
        status: 'approved'
      },
      {
        id: '3',
        memberId: id,
        type: 'screening',
        title: 'Cardiovascular Risk Assessment',
        description: 'Comprehensive cardiovascular risk stratification and prevention planning',
        expectedOutcome: 'Early identification and prevention of cardiovascular events',
        timeframe: '1 month',
        priority: 'high',
        costEstimate: 1500,
        qualityMeasure: 'ASCVD risk <7.5%',
        status: 'scheduled'
      },
      {
        id: '4',
        memberId: id,
        type: 'referral',
        title: 'Endocrinologist Consultation',
        description: 'Specialist consultation for complex diabetes management',
        expectedOutcome: 'Optimized medication regimen and improved glycemic control',
        timeframe: '2-4 weeks',
        priority: 'medium',
        costEstimate: 600,
        qualityMeasure: 'HbA1c improvement',
        status: 'recommended'
      }
    ];
  };

  const fetchQualityMetricsAPI = async (id: string): Promise<QualityMetric[]> => {
    await new Promise(resolve => setTimeout(resolve, 200));

    return [
      {
        measure: 'HbA1c Control',
        description: 'Percentage of diabetic patients with HbA1c <7%',
        target: 70,
        current: 65,
        trend: 'improving',
        lastUpdated: '2024-07-28',
        benchmark: 72
      },
      {
        measure: 'Blood Pressure Control',
        description: 'Percentage of hypertensive patients with BP <140/90',
        target: 80,
        current: 75,
        trend: 'stable',
        lastUpdated: '2024-07-28',
        benchmark: 78
      },
      {
        measure: 'Medication Adherence',
        description: 'Percentage of patients with >80% medication adherence',
        target: 85,
        current: 68,
        trend: 'declining',
        lastUpdated: '2024-07-28',
        benchmark: 82
      },
      {
        measure: 'Preventive Care Completion',
        description: 'Percentage of due preventive care measures completed',
        target: 90,
        current: 73,
        trend: 'improving',
        lastUpdated: '2024-07-28',
        benchmark: 88
      }
    ];
  };

  // Analyze care gaps based on member data
  const analyzeCareGapsForMember = useCallback((member: Member): CareGap[] => {
    const gaps: CareGap[] = [];
    const today = new Date();

    // Check chronic conditions for care gaps
    member.medicalHistory.chronicConditions.forEach(condition => {
      const lastReview = new Date(condition.lastReview);
      const daysSinceReview = Math.floor((today.getTime() - lastReview.getTime()) / (1000 * 60 * 60 * 24));

      // Diabetes-specific gaps
      if (condition.condition.toLowerCase().includes('diabetes')) {
        if (daysSinceReview > 90) {
          gaps.push({
            id: `hba1c-${condition.id}`,
            memberId: member.id,
            type: 'chronic_care',
            category: 'HbA1c Testing',
            description: 'Overdue HbA1c testing for diabetes monitoring',
            recommendation: 'Schedule HbA1c test within 2 weeks',
            priority: daysSinceReview > 120 ? 'high' : 'medium',
            dueDate: new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString(),
            status: 'open',
            evidenceBase: 'ADA Clinical Practice Guidelines',
            potentialCostSaving: 8000,
            createdAt: today.toISOString(),
            updatedAt: today.toISOString()
          });
        }

        // Annual eye exam
        if (daysSinceReview > 365) {
          gaps.push({
            id: `eye-exam-${condition.id}`,
            memberId: member.id,
            type: 'preventive',
            category: 'Diabetic Eye Exam',
            description: 'Overdue annual diabetic eye examination',
            recommendation: 'Schedule ophthalmology appointment',
            priority: 'high',
            dueDate: new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString(),
            status: 'open',
            evidenceBase: 'ADA Clinical Practice Guidelines',
            potentialCostSaving: 15000,
            createdAt: today.toISOString(),
            updatedAt: today.toISOString()
          });
        }
      }

      // Hypertension-specific gaps
      if (condition.condition.toLowerCase().includes('hypertension')) {
        if (daysSinceReview > 180) {
          gaps.push({
            id: `bp-check-${condition.id}`,
            memberId: member.id,
            type: 'chronic_care',
            category: 'Blood Pressure Monitoring',
            description: 'Overdue blood pressure monitoring appointment',
            recommendation: 'Schedule follow-up for blood pressure check',
            priority: daysSinceReview > 240 ? 'high' : 'medium',
            dueDate: new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString(),
            status: 'open',
            evidenceBase: 'AHA/ACC Hypertension Guidelines',
            potentialCostSaving: 25000,
            createdAt: today.toISOString(),
            updatedAt: today.toISOString()
          });
        }
      }
    });

    // Age-based preventive care gaps
    const age = Math.floor((today.getTime() - new Date(member.demographics.dateOfBirth).getTime()) / (1000 * 60 * 60 * 24 * 365.25));

    if (age >= 50) {
      gaps.push({
        id: `colonoscopy-${member.id}`,
        memberId: member.id,
        type: 'preventive',
        category: 'Colorectal Cancer Screening',
        description: 'Due for colorectal cancer screening',
        recommendation: 'Schedule colonoscopy or alternative screening',
        priority: age >= 60 ? 'high' : 'medium',
        dueDate: new Date(today.getTime() + 60 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'open',
        evidenceBase: 'USPSTF Guidelines',
        potentialCostSaving: 50000,
        createdAt: today.toISOString(),
        updatedAt: today.toISOString()
      });
    }

    return gaps;
  }, []);

  // Calculate care gap analysis
  const calculateAnalysis = useCallback((gaps: CareGap[]): CareGapAnalysis => {
    const today = new Date();
    const overduegaps = gaps.filter(gap => new Date(gap.dueDate) < today);

    return {
      totalGaps: gaps.length,
      urgentGaps: gaps.filter(gap => gap.priority === 'urgent').length,
      highPriorityGaps: gaps.filter(gap => gap.priority === 'high').length,
      potentialSavings: gaps.reduce((sum, gap) => sum + gap.potentialCostSaving, 0),
      completionRate: gaps.length > 0 ?
        (gaps.filter(gap => gap.status === 'completed').length / gaps.length) * 100 : 100,
      averageDaysOverdue: overduegaps.length > 0 ?
        overduegaps.reduce((sum, gap) => {
          const daysDiff = Math.floor((today.getTime() - new Date(gap.dueDate).getTime()) / (1000 * 60 * 60 * 24));
          return sum + daysDiff;
        }, 0) / overduegaps.length : 0
    };
  }, []);

  // Load care gaps for member
  const loadCareGaps = useCallback(async (id: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const [careGaps, recommendations, qualityMetrics] = await Promise.all([
        fetchCareGapsAPI(id),
        fetchRecommendationsAPI(id),
        fetchQualityMetricsAPI(id)
      ]);

      const analysis = calculateAnalysis(careGaps);

      setState({
        careGaps,
        recommendations,
        qualityMetrics,
        analysis,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString()
      });
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load care gaps'
      }));
    }
  }, [calculateAnalysis]);

  // Generate care gaps from member profile
  const generateCareGaps = useCallback(async (member: Member) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const generatedGaps = analyzeCareGapsForMember(member);
      const existingGaps = await fetchCareGapsAPI(member.id);
      const allGaps = [...existingGaps, ...generatedGaps];

      // Remove duplicates based on category and member
      const uniqueGaps = allGaps.filter((gap, index, self) =>
        index === self.findIndex(g => g.category === gap.category && g.memberId === gap.memberId)
      );

      const analysis = calculateAnalysis(uniqueGaps);

      setState(prev => ({
        ...prev,
        careGaps: uniqueGaps,
        analysis,
        isLoading: false,
        lastUpdated: new Date().toISOString()
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to generate care gaps'
      }));
    }
  }, [analyzeCareGapsForMember, calculateAnalysis]);

  // Update care gap status
  const updateCareGapStatus = useCallback(async (
    gapId: string,
    status: CareGap['status'],
    notes?: string
  ) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 300));

      setState(prev => ({
        ...prev,
        careGaps: prev.careGaps.map(gap =>
          gap.id === gapId
            ? { ...gap, status, updatedAt: new Date().toISOString() }
            : gap
        ),
        analysis: calculateAnalysis(prev.careGaps.map(gap =>
          gap.id === gapId ? { ...gap, status } : gap
        )),
        isLoading: false,
        lastUpdated: new Date().toISOString()
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to update care gap'
      }));
    }
  }, [calculateAnalysis]);

  // Get priority care gaps
  const getPriorityCareGaps = useCallback((priority: CareGap['priority']) => {
    return state.careGaps.filter(gap => gap.priority === priority);
  }, [state.careGaps]);

  // Get overdue care gaps
  const getOverdueCareGaps = useCallback(() => {
    const today = new Date();
    return state.careGaps.filter(gap => new Date(gap.dueDate) < today);
  }, [state.careGaps]);

  // Auto-load if member ID provided
  useEffect(() => {
    if (memberId) {
      loadCareGaps(memberId);
    }
  }, [memberId, loadCareGaps]);

  // Memoized computations
  const careGapsByType = useMemo(() => {
    return state.careGaps.reduce((acc, gap) => {
      acc[gap.type] = (acc[gap.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [state.careGaps]);

  const recommendationsByType = useMemo(() => {
    return state.recommendations.reduce((acc, rec) => {
      acc[rec.type] = (acc[rec.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [state.recommendations]);

  return {
    // State
    careGaps: state.careGaps,
    recommendations: state.recommendations,
    qualityMetrics: state.qualityMetrics,
    analysis: state.analysis,
    isLoading: state.isLoading,
    error: state.error,
    lastUpdated: state.lastUpdated,

    // Computed values
    careGapsByType,
    recommendationsByType,

    // Actions
    loadCareGaps,
    generateCareGaps,
    updateCareGapStatus,
    getPriorityCareGaps,
    getOverdueCareGaps
  };
};

export default useCareGaps;

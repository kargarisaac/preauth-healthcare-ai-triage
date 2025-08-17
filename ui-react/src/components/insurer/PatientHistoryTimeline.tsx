import React, { useState, useEffect } from 'react';
import {
  Calendar,
  FileText,
  Activity,
  Heart,
  Pill,
  Building,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import type {
  PatientHistoryEntry,
  InsurerRequest,
} from '@/types/insurer';
import type { Member } from '@/types/healthcare';

// Timeline entry type configuration
const ENTRY_TYPE_CONFIGS = {
  authorization: {
    icon: FileText,
    color: 'blue',
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
    label: 'Authorization',
  },
  claim: {
    icon: DollarSign,
    color: 'green',
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    label: 'Claim',
  },
  treatment: {
    icon: Activity,
    color: 'purple',
    bgColor: 'bg-purple-100',
    textColor: 'text-purple-800',
    label: 'Treatment',
  },
  prescription: {
    icon: Pill,
    color: 'orange',
    bgColor: 'bg-orange-100',
    textColor: 'text-orange-800',
    label: 'Prescription',
  },
  hospitalization: {
    icon: Building,
    color: 'red',
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
    label: 'Hospitalization',
  },
} as const;

// Mock patient data - replace with actual API
const mockPatientData: Member = {
  id: 'MEM-789',
  emiratesId: '784-1985-1234567-8',
  demographics: {
    firstName: 'Ahmed',
    lastName: 'Al-Mansouri',
    fullName: 'Ahmed Al-Mansouri',
    dateOfBirth: '1985-03-15',
    gender: 'male',
    nationality: 'UAE',
    preferredLanguage: 'Arabic',
    maritalStatus: 'married',
  },
  contact: {
    phone: '+971-50-123-4567',
    email: 'ahmed.almansouri@email.com',
    address: {
      street: '123 Sheikh Zayed Road',
      city: 'Dubai',
      emirate: 'Dubai',
      country: 'UAE',
      postalCode: '12345',
    },
    emergencyContact: {
      name: 'Fatima Al-Mansouri',
      relationship: 'Wife',
      phone: '+971-50-987-6543',
    },
  },
  insurance: {
    provider: 'Emirates Insurance',
    policyNumber: 'EI-2025-789',
    planType: 'Premium Health',
    effectiveDate: '2025-01-01',
    expirationDate: '2025-12-31',
    deductible: 1000,
    coPayment: 20,
    outOfPocketMax: 15000,
    benefitYear: '2025',
    status: 'active',
  },
  medicalHistory: {
    allergies: [
      {
        allergen: 'Penicillin',
        severity: 'moderate',
        reaction: 'Skin rash',
      },
    ],
    chronicConditions: [
      {
        id: 'CC-001',
        condition: 'Hypertension',
        icdCode: 'I10',
        diagnosisDate: '2020-03-15',
        severity: 'mild',
        status: 'active',
        managingProvider: 'Dr. Sarah Ahmed',
        medications: ['Lisinopril 10mg'],
        lastReview: '2025-06-15',
      },
    ],
    surgicalHistory: [
      {
        procedure: 'Appendectomy',
        date: '2018-08-22',
        hospital: 'Dubai Hospital',
      },
    ],
    familyHistory: [
      {
        relationship: 'Father',
        condition: 'Diabetes Type 2',
        ageOfOnset: 55,
      },
    ],
  },
  costUtilization: {
    yearToDate: {
      totalCosts: 12500,
      memberPaid: 2800,
      planPaid: 9700,
      deductibleMet: 800,
      outOfPocketMet: 2800,
    },
    monthlyTrends: [],
    topCategories: [],
  },
  recentRequests: [],
  riskScore: 35,
  lastActivity: '2025-08-17T10:30:00Z',
  createdAt: '2020-01-01T00:00:00Z',
  updatedAt: '2025-08-17T10:30:00Z',
};

const mockHistoryEntries: PatientHistoryEntry[] = [
  {
    id: 'PH-001',
    type: 'authorization',
    date: '2025-08-17T10:30:00Z',
    provider: 'Dubai Healthcare City',
    service: 'Coronary Angioplasty',
    diagnosis: 'Coronary Artery Disease',
    outcome: 'Approved',
    cost: 45000,
    status: 'approved',
    relevanceScore: 100,
  },
  {
    id: 'PH-002',
    type: 'treatment',
    date: '2025-07-20T14:15:00Z',
    provider: 'Emirates Hospital',
    service: 'Cardiac Catheterization',
    diagnosis: 'Chest Pain Investigation',
    outcome: 'Significant stenosis found',
    cost: 8500,
    status: 'completed',
    relevanceScore: 95,
  },
  {
    id: 'PH-003',
    type: 'prescription',
    date: '2025-07-15T09:00:00Z',
    provider: 'Dr. Sarah Ahmed',
    service: 'Cardiac Medication',
    diagnosis: 'Hypertension',
    outcome: 'Medication adjusted',
    cost: 320,
    status: 'active',
    relevanceScore: 70,
  },
  {
    id: 'PH-004',
    type: 'claim',
    date: '2025-06-30T11:20:00Z',
    provider: 'Mediclinic Dubai',
    service: 'Cardiology Consultation',
    diagnosis: 'Hypertension Follow-up',
    outcome: 'Routine monitoring',
    cost: 750,
    status: 'paid',
    relevanceScore: 60,
  },
  {
    id: 'PH-005',
    type: 'authorization',
    date: '2025-05-12T16:45:00Z',
    provider: 'Dubai Hospital',
    service: 'MRI Heart',
    diagnosis: 'Cardiac Assessment',
    outcome: 'Approved',
    cost: 2800,
    status: 'approved',
    relevanceScore: 85,
  },
  {
    id: 'PH-006',
    type: 'hospitalization',
    date: '2024-11-08T08:30:00Z',
    provider: 'American Hospital Dubai',
    service: 'Emergency Care',
    diagnosis: 'Chest Pain',
    outcome: 'Discharged stable',
    cost: 5200,
    status: 'completed',
    relevanceScore: 90,
  },
];

interface PatientHistoryTimelineProps {
  patientId: string;
  currentRequestId?: string;
  onEntryClick?: (entry: PatientHistoryEntry) => void;
}

export const PatientHistoryTimeline: React.FC<PatientHistoryTimelineProps> = ({
  patientId,
  currentRequestId,
  onEntryClick,
}) => {
  const [patient, setPatient] = useState<Member | null>(null);
  const [historyEntries, setHistoryEntries] = useState<PatientHistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedEntries, setExpandedEntries] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [showOnlyRelevant, setShowOnlyRelevant] = useState(true);

  useEffect(() => {
    // Simulate API loading
    const loadPatientData = async () => {
      setIsLoading(true);
      try {
        // Mock delay
        await new Promise(resolve => setTimeout(resolve, 500));
        setPatient(mockPatientData);
        setHistoryEntries(mockHistoryEntries);
      } catch (error) {
        console.error('Failed to load patient data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadPatientData();
  }, [patientId]);

  const filteredEntries = React.useMemo(() => {
    let filtered = historyEntries;

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter(entry => entry.type === filterType);
    }

    // Filter by relevance
    if (showOnlyRelevant) {
      filtered = filtered.filter(entry => entry.relevanceScore >= 60);
    }

    // Sort by date (most recent first)
    return filtered.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [historyEntries, filterType, showOnlyRelevant]);

  const toggleEntryExpansion = (entryId: string) => {
    setExpandedEntries(prev => 
      prev.includes(entryId)
        ? prev.filter(id => id !== entryId)
        : [...prev, entryId]
    );
  };

  const getRelevanceColor = (score: number): string => {
    if (score >= 90) return 'text-red-600';
    if (score >= 80) return 'text-orange-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const calculateTotalCosts = () => {
    return filteredEntries.reduce((total, entry) => total + entry.cost, 0);
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </Card>
    );
  }

  if (!patient) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <User className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
            Patient Not Found
          </h3>
          <p className="text-gray-600 dark:text-dark-text-secondary">
            Unable to load patient history.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Patient Summary Card */}
      <Card className="p-4">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
            <User className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              {patient.demographics.fullName}
            </h3>
            <div className="mt-1 text-sm text-gray-600 dark:text-dark-text-secondary space-y-1">
              <p>ID: {patient.id} • Emirates ID: {patient.emiratesId}</p>
              <p>DOB: {new Date(patient.demographics.dateOfBirth).toLocaleDateString()}</p>
              <p>Plan: {patient.insurance.planType} • Status: {patient.insurance.status}</p>
            </div>
            
            {/* Risk Score */}
            <div className="mt-2 flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700 dark:text-dark-text-primary">
                  Risk Score:
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  patient.riskScore >= 70 ? 'bg-red-100 text-red-800' :
                  patient.riskScore >= 40 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {patient.riskScore}/100
                </span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Cost Summary */}
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border-primary">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-dark-text-secondary">YTD Total:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-dark-text-primary">
                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED' })
                  .format(patient.costUtilization.yearToDate.totalCosts)}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-dark-text-secondary">Deductible Met:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-dark-text-primary">
                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED' })
                  .format(patient.costUtilization.yearToDate.deductibleMet)}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Timeline Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div>
            <h4 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
              Patient History Timeline
            </h4>
            <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
              {filteredEntries.length} entries • Total: {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED' }).format(calculateTotalCosts())}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="text-sm border border-gray-300 dark:border-dark-border-primary rounded-md px-3 py-1 bg-white dark:bg-dark-bg-secondary text-gray-900 dark:text-dark-text-primary"
            >
              <option value="all">All Types</option>
              <option value="authorization">Authorizations</option>
              <option value="claim">Claims</option>
              <option value="treatment">Treatments</option>
              <option value="prescription">Prescriptions</option>
              <option value="hospitalization">Hospitalizations</option>
            </select>
            
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={showOnlyRelevant}
                onChange={(e) => setShowOnlyRelevant(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              <span className="text-gray-700 dark:text-dark-text-primary">Relevant only</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Timeline */}
      <Card className="p-4">
        <div className="flow-root">
          <ul className="-mb-8">
            {filteredEntries.map((entry, entryIdx) => {
              const config = ENTRY_TYPE_CONFIGS[entry.type];
              const Icon = config.icon;
              const isExpanded = expandedEntries.includes(entry.id);
              const isHighRelevance = entry.relevanceScore >= 80;
              
              return (
                <li key={entry.id}>
                  <div className="relative pb-8">
                    {entryIdx !== filteredEntries.length - 1 ? (
                      <span
                        className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-dark-border-primary"
                        aria-hidden="true"
                      />
                    ) : null}
                    
                    <div className="relative flex space-x-3">
                      {/* Timeline Icon */}
                      <div>
                        <span className={`h-8 w-8 rounded-full ${config.bgColor} flex items-center justify-center ring-8 ring-white dark:ring-dark-bg-secondary`}>
                          <Icon className={`h-5 w-5 ${config.textColor}`} aria-hidden="true" />
                        </span>
                      </div>
                      
                      {/* Timeline Content */}
                      <div className="flex-1 w-full">
                        <div className="cursor-pointer p-3 bg-white dark:bg-dark-bg-secondary rounded-lg border border-gray-200 dark:border-dark-border-primary hover:shadow-sm transition-shadow" onClick={() => toggleEntryExpansion(entry.id)}>
                          <div className="space-y-2">
                            <div className="flex items-start justify-between">
                              <div className="flex-1 space-y-1">
                                <div className="flex items-center space-x-2 flex-wrap">
                                  <h4 className="text-sm font-semibold text-gray-900 dark:text-dark-text-primary">
                                    {entry.service}
                                  </h4>
                                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} whitespace-nowrap`}>
                                    {config.label}
                                  </span>
                                  {isHighRelevance && (
                                    <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs font-medium whitespace-nowrap">
                                      High Relevance
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                                  {entry.diagnosis} • {entry.provider}
                                </p>
                              </div>
                              <div className="flex items-center space-x-2 ml-2">
                                <span className={`text-xs font-medium ${getRelevanceColor(entry.relevanceScore)} whitespace-nowrap`}>
                                  {entry.relevanceScore}% relevant
                                </span>
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
                                )}
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between text-sm text-gray-500 dark:text-dark-text-secondary">
                              <span className="flex items-center space-x-1">
                                <Calendar className="h-3 w-3" />
                                <span>{new Date(entry.date).toLocaleDateString()}</span>
                              </span>
                              <span className="font-medium">
                                {new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED' })
                                  .format(entry.cost)}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Expanded Details */}
                        {isExpanded && (
                          <div className="mt-3 p-4 bg-gray-50 dark:bg-dark-bg-tertiary rounded-lg border border-gray-100 dark:border-dark-border-secondary">
                            <div className="space-y-3">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <div className="space-y-1">
                                  <span className="block font-medium text-gray-700 dark:text-dark-text-primary">Outcome:</span>
                                  <p className="text-gray-600 dark:text-dark-text-secondary">{entry.outcome}</p>
                                </div>
                                <div className="space-y-1">
                                  <span className="block font-medium text-gray-700 dark:text-dark-text-primary">Status:</span>
                                  <p className="text-gray-600 dark:text-dark-text-secondary capitalize">{entry.status}</p>
                                </div>
                              </div>
                              
                              {onEntryClick && (
                                <div className="pt-2 border-t border-gray-200 dark:border-dark-border-primary">
                                  <Button
                                    variant="tertiary"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onEntryClick(entry);
                                    }}
                                    className="text-blue-600 hover:text-blue-700"
                                  >
                                    View Full Details
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
        
        {filteredEntries.length === 0 && (
          <div className="text-center py-8">
            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
              No History Found
            </h3>
            <p className="text-gray-600 dark:text-dark-text-secondary">
              No medical history entries match your current filters.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

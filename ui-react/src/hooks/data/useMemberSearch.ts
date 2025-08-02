import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Member, 
  SearchCriteria, 
  SearchResult, 
  SearchSuggestion,
  OfflineSearchCache 
} from '../../types/healthcare';

// Fuzzy search utility
const fuzzyScore = (term: string, target: string): number => {
  if (!term || !target) return 0;
  
  term = term.toLowerCase();
  target = target.toLowerCase();
  
  if (target.includes(term)) return 100;
  
  let score = 0;
  let termIndex = 0;
  
  for (let i = 0; i < target.length && termIndex < term.length; i++) {
    if (target[i] === term[termIndex]) {
      score++;
      termIndex++;
    }
  }
  
  return (score / term.length) * 100;
};

export const useMemberSearch = () => {
  const [searchResults, setSearchResults] = useState<SearchResult>({
    members: [],
    total: 0,
    page: 1,
    pageSize: 20,
    hasMore: false,
    filters: {
      providers: [],
      planTypes: [],
      emirates: [],
      riskLevels: []
    }
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  
  // Local cache for offline capability
  const [offlineCache, setOfflineCache] = useState<OfflineSearchCache>({
    members: [],
    lastSync: new Date().toISOString(),
    searchHistory: [],
    recentMembers: []
  });
  
  // Search history management
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<SearchCriteria[]>([]);

  // Mock API call - replace with actual API integration
  const searchMembersAPI = async (criteria: SearchCriteria, page = 1): Promise<SearchResult> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock data - replace with actual API call
    const mockMembers: Member[] = [
      {
        id: '1',
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
          email: 'ahmed.almansouri@email.com',
          address: {
            street: 'Al Wasl Road',
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
            { allergen: 'Penicillin', severity: 'severe', reaction: 'Anaphylaxis' }
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
              medications: ['Metformin', 'Insulin'],
              lastReview: '2024-06-15'
            }
          ],
          surgicalHistory: [],
          familyHistory: [
            { relationship: 'Father', condition: 'Diabetes', ageOfOnset: 55 }
          ]
        },
        costUtilization: {
          yearToDate: {
            totalCosts: 15000,
            memberPaid: 3000,
            planPaid: 12000,
            deductibleMet: 1000,
            outOfPocketMet: 2000
          },
          monthlyTrends: [
            { month: '2024-01', totalCosts: 2000, visits: 2, prescriptions: 3 },
            { month: '2024-02', totalCosts: 1500, visits: 1, prescriptions: 2 }
          ],
          topCategories: [
            { category: 'Medications', amount: 8000, percentage: 53.3 },
            { category: 'Outpatient', amount: 5000, percentage: 33.3 },
            { category: 'Lab Tests', amount: 2000, percentage: 13.3 }
          ]
        },
        recentRequests: [],
        riskScore: 75,
        lastActivity: '2024-07-28',
        createdAt: '2024-01-01',
        updatedAt: '2024-07-28'
      }
    ];

    // Apply fuzzy search
    let filteredMembers = mockMembers;
    
    if (criteria.query) {
      filteredMembers = mockMembers.filter(member => {
        const searchTerms = [
          member.demographics.fullName,
          member.emiratesId,
          member.contact.phone,
          member.contact.email,
          member.insurance.policyNumber
        ];
        
        return searchTerms.some(term => 
          fuzzyScore(criteria.query!, term) > 50
        );
      });
    }
    
    // Apply other filters
    if (criteria.emiratesId) {
      filteredMembers = filteredMembers.filter(m => 
        m.emiratesId.includes(criteria.emiratesId!)
      );
    }
    
    if (criteria.provider) {
      filteredMembers = filteredMembers.filter(m => 
        m.insurance.provider.toLowerCase().includes(criteria.provider!.toLowerCase())
      );
    }
    
    if (criteria.riskLevel) {
      const riskRanges = {
        low: [0, 40],
        medium: [41, 70],
        high: [71, 100]
      };
      const [min, max] = riskRanges[criteria.riskLevel];
      filteredMembers = filteredMembers.filter(m => 
        m.riskScore >= min && m.riskScore <= max
      );
    }

    return {
      members: filteredMembers,
      total: filteredMembers.length,
      page,
      pageSize: 20,
      hasMore: false,
      filters: {
        providers: ['Dubai Health Insurance', 'Abu Dhabi Health Services'],
        planTypes: ['Gold Plus', 'Silver', 'Bronze'],
        emirates: ['Dubai', 'Abu Dhabi', 'Sharjah'],
        riskLevels: ['low', 'medium', 'high']
      }
    };
  };

  // Main search function
  const searchMembers = useCallback(async (
    criteria: SearchCriteria, 
    page = 1,
    useCache = false
  ) => {
    setIsLoading(true);
    setError(null);
    
    try {
      let result: SearchResult;
      
      if (useCache && offlineCache.members.length > 0) {
        // Use offline cache
        const filteredMembers = offlineCache.members.filter(member => {
          if (!criteria.query) return true;
          
          const searchTerms = [
            member.demographics.fullName,
            member.emiratesId,
            member.contact.phone,
            member.contact.email,
            member.insurance.policyNumber
          ];
          
          return searchTerms.some(term => 
            fuzzyScore(criteria.query!, term) > 50
          );
        });
        
        result = {
          members: filteredMembers,
          total: filteredMembers.length,
          page,
          pageSize: 20,
          hasMore: false,
          filters: {
            providers: [],
            planTypes: [],
            emirates: [],
            riskLevels: []
          }
        };
      } else {
        result = await searchMembersAPI(criteria, page);
        
        // Update offline cache
        setOfflineCache(prev => ({
          ...prev,
          members: [...prev.members, ...result.members].slice(0, 1000), // Keep latest 1000
          lastSync: new Date().toISOString()
        }));
      }
      
      setSearchResults(result);
      
      // Update search history
      if (criteria.query && criteria.query.trim()) {
        setSearchHistory(prev => {
          const newHistory = [criteria.query!, ...prev.filter(h => h !== criteria.query)];
          return newHistory.slice(0, 10); // Keep latest 10
        });
      }
      
      setRecentSearches(prev => {
        const newSearches = [criteria, ...prev.filter(s => 
          JSON.stringify(s) !== JSON.stringify(criteria)
        )];
        return newSearches.slice(0, 5); // Keep latest 5
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsLoading(false);
    }
  }, [offlineCache.members]);

  // Generate search suggestions
  const generateSuggestions = useCallback(async (query: string): Promise<SearchSuggestion[]> => {
    if (!query || query.length < 2) return [];
    
    // Mock suggestions - replace with actual API
    const mockSuggestions: SearchSuggestion[] = [
      {
        id: '1',
        type: 'member',
        value: 'Ahmed Al Mansouri',
        label: 'Ahmed Al Mansouri (784-1234-5678901-0)',
        memberCount: 1
      },
      {
        id: '2',
        type: 'provider',
        value: 'Dubai Health Insurance',
        label: 'Dubai Health Insurance',
        memberCount: 245
      },
      {
        id: '3',
        type: 'condition',
        value: 'Diabetes',
        label: 'Type 2 Diabetes',
        memberCount: 156
      }
    ];
    
    return mockSuggestions.filter(s => 
      s.label.toLowerCase().includes(query.toLowerCase())
    );
  }, []);

  // Auto-complete functionality
  const getSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    
    const newSuggestions = await generateSuggestions(query);
    setSuggestions(newSuggestions);
  }, [generateSuggestions]);

  // Quick search by specific field
  const quickSearch = useCallback(async (
    field: keyof SearchCriteria, 
    value: string
  ) => {
    const criteria: SearchCriteria = { [field]: value };
    await searchMembers(criteria);
  }, [searchMembers]);

  // Advanced search with multiple criteria
  const advancedSearch = useCallback(async (criteria: SearchCriteria) => {
    await searchMembers(criteria);
  }, [searchMembers]);

  // Clear search results
  const clearSearch = useCallback(() => {
    setSearchResults({
      members: [],
      total: 0,
      page: 1,
      pageSize: 20,
      hasMore: false,
      filters: {
        providers: [],
        planTypes: [],
        emirates: [],
        riskLevels: []
      }
    });
    setSuggestions([]);
    setError(null);
  }, []);

  // Load more results (pagination)
  const loadMore = useCallback(async (criteria: SearchCriteria) => {
    if (isLoading || !searchResults.hasMore) return;
    
    const nextPage = searchResults.page + 1;
    setIsLoading(true);
    
    try {
      const result = await searchMembersAPI(criteria, nextPage);
      setSearchResults(prev => ({
        ...result,
        members: [...prev.members, ...result.members]
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more results');
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, searchResults.hasMore, searchResults.page]);

  // Memoized values for performance
  const searchStats = useMemo(() => ({
    totalMembers: searchResults.total,
    currentPage: searchResults.page,
    hasResults: searchResults.members.length > 0,
    canLoadMore: searchResults.hasMore
  }), [searchResults]);

  return {
    // State
    searchResults,
    isLoading,
    error,
    suggestions,
    searchHistory,
    recentSearches,
    offlineCache,
    searchStats,
    
    // Actions
    searchMembers,
    quickSearch,
    advancedSearch,
    getSuggestions,
    clearSearch,
    loadMore,
    
    // Utilities
    fuzzyScore
  };
};

export default useMemberSearch;
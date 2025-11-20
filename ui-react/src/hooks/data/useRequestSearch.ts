import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useDebounce } from 'use-debounce';
import type {
  RequestSearchCriteria,
  SavedSearch,
  QuickFilter,
  RequestHistoryItem,
} from '@/types/requests';

// Quick filter presets
const DEFAULT_QUICK_FILTERS: QuickFilter[] = [
  {
    id: 'pending',
    label: 'Pending Review',
    icon: 'clock',
    criteria: { status: ['pending', 'under_review'] },
    color: 'yellow',
  },
  {
    id: 'urgent',
    label: 'Urgent',
    icon: 'alert-triangle',
    criteria: { priority: ['urgent'] },
    color: 'red',
  },
  {
    id: 'high_value',
    label: 'High Value',
    icon: 'dollar-sign',
    criteria: { amountRange: { min: 10000, max: Number.MAX_VALUE } },
    color: 'green',
  },
  {
    id: 'today',
    label: 'Today',
    icon: 'calendar',
    criteria: {
      dateRange: {
        from: new Date().toISOString().split('T')[0],
        to: new Date().toISOString().split('T')[0],
      },
    },
    color: 'blue',
  },
  {
    id: 'no_documents',
    label: 'Missing Documents',
    icon: 'file-x',
    criteria: { hasDocuments: false },
    color: 'orange',
  },
];

// Search history storage
const SEARCH_HISTORY_KEY = 'healthcare-preauth_search_history';
const SAVED_SEARCHES_KEY = 'healthcare-preauth_saved_searches';
const MAX_SEARCH_HISTORY = 10;

export function useRequestSearch() {
  const [searchCriteria, setSearchCriteria] = useState<RequestSearchCriteria>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [activeQuickFilters, setActiveQuickFilters] = useState<string[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<RequestHistoryItem[]>([]);
  const [highlightTerm, setHighlightTerm] = useState('');

  // Refs for managing search state
  const searchInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounced search query
  const [debouncedQuery] = useDebounce(searchQuery, 300);

  // Load saved data from localStorage
  useEffect(() => {
    try {
      const savedSearchesData = localStorage.getItem(SAVED_SEARCHES_KEY);
      if (savedSearchesData) {
        setSavedSearches(JSON.parse(savedSearchesData));
      }

      const searchHistoryData = localStorage.getItem(SEARCH_HISTORY_KEY);
      if (searchHistoryData) {
        setSearchHistory(JSON.parse(searchHistoryData));
      }
    } catch (error) {
      console.warn('Failed to load search data from localStorage:', error);
    }
  }, []);

  // Update search criteria when query changes
  useEffect(() => {
    if (debouncedQuery !== searchCriteria.query) {
      updateSearchCriteria({ query: debouncedQuery || undefined });
      setHighlightTerm(debouncedQuery);
    }
  }, [debouncedQuery]);

  // Update search criteria
  const updateSearchCriteria = useCallback((newCriteria: Partial<RequestSearchCriteria>) => {
    setSearchCriteria(prev => {
      const updated = { ...prev, ...newCriteria };

      // Remove undefined values
      Object.keys(updated).forEach(key => {
        if (updated[key as keyof RequestSearchCriteria] === undefined) {
          delete updated[key as keyof RequestSearchCriteria];
        }
      });

      return updated;
    });
  }, []);

  // Update search query
  const updateSearchQuery = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setSearchCriteria({});
    setActiveQuickFilters([]);
    setHighlightTerm('');
    setSearchResults([]);

    if (searchInputRef.current) {
      searchInputRef.current.value = '';
    }
  }, []);

  // Quick filter management
  const toggleQuickFilter = useCallback((filterId: string) => {
    const filter = DEFAULT_QUICK_FILTERS.find(f => f.id === filterId);
    if (!filter) return;

    setActiveQuickFilters(prev => {
      const isActive = prev.includes(filterId);
      const newActiveFilters = isActive
        ? prev.filter(id => id !== filterId)
        : [...prev, filterId];

      // Update search criteria based on active quick filters
      const newCriteria: RequestSearchCriteria = { ...searchCriteria };

      if (isActive) {
        // Remove filter criteria
        Object.keys(filter.criteria).forEach(key => {
          delete newCriteria[key as keyof RequestSearchCriteria];
        });
      } else {
        // Add filter criteria
        Object.assign(newCriteria, filter.criteria);
      }

      // Apply remaining active filters
      const remainingFilters = newActiveFilters.filter(id => id !== filterId);
      remainingFilters.forEach(id => {
        const remainingFilter = DEFAULT_QUICK_FILTERS.find(f => f.id === id);
        if (remainingFilter) {
          Object.assign(newCriteria, remainingFilter.criteria);
        }
      });

      setSearchCriteria(newCriteria);
      return newActiveFilters;
    });
  }, [searchCriteria]);

  // Clear all quick filters
  const clearQuickFilters = useCallback(() => {
    setActiveQuickFilters([]);

    // Remove quick filter criteria from search
    const newCriteria = { ...searchCriteria };
    DEFAULT_QUICK_FILTERS.forEach(filter => {
      Object.keys(filter.criteria).forEach(key => {
        delete newCriteria[key as keyof RequestSearchCriteria];
      });
    });

    setSearchCriteria(newCriteria);
  }, [searchCriteria]);

  // Save search
  const saveSearch = useCallback((name: string, description?: string) => {
    const newSearch: SavedSearch = {
      id: `search_${Date.now()}`,
      name,
      description,
      criteria: searchCriteria,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setSavedSearches(prev => {
      const updated = [...prev, newSearch];
      try {
        localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to save search to localStorage:', error);
      }
      return updated;
    });

    return newSearch;
  }, [searchCriteria]);

  // Load saved search
  const loadSavedSearch = useCallback((searchId: string) => {
    const search = savedSearches.find(s => s.id === searchId);
    if (search) {
      setSearchCriteria(search.criteria);
      setSearchQuery(search.criteria.query || '');

      // Update active quick filters
      const activeFilters: string[] = [];
      DEFAULT_QUICK_FILTERS.forEach(filter => {
        const isMatch = Object.keys(filter.criteria).every(key => {
          const filterValue = filter.criteria[key as keyof RequestSearchCriteria];
          const searchValue = search.criteria[key as keyof RequestSearchCriteria];
          return JSON.stringify(filterValue) === JSON.stringify(searchValue);
        });
        if (isMatch) {
          activeFilters.push(filter.id);
        }
      });
      setActiveQuickFilters(activeFilters);
    }
  }, [savedSearches]);

  // Delete saved search
  const deleteSavedSearch = useCallback((searchId: string) => {
    setSavedSearches(prev => {
      const updated = prev.filter(s => s.id !== searchId);
      try {
        localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to update saved searches in localStorage:', error);
      }
      return updated;
    });
  }, []);

  // Add to search history
  const addToSearchHistory = useCallback((query: string) => {
    if (!query.trim() || searchHistory.includes(query)) return;

    setSearchHistory(prev => {
      const updated = [query, ...prev.filter(q => q !== query)].slice(0, MAX_SEARCH_HISTORY);
      try {
        localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
      } catch (error) {
        console.warn('Failed to save search history to localStorage:', error);
      }
      return updated;
    });
  }, [searchHistory]);

  // Clear search history
  const clearSearchHistory = useCallback(() => {
    setSearchHistory([]);
    try {
      localStorage.removeItem(SEARCH_HISTORY_KEY);
    } catch (error) {
      console.warn('Failed to clear search history from localStorage:', error);
    }
  }, []);

  // Perform search with highlighting
  const performSearch = useCallback(async (requests: RequestHistoryItem[]) => {
    if (!searchQuery.trim()) {
      setSearchResults(requests);
      setHighlightTerm('');
      return requests;
    }

    setIsSearching(true);

    // Cancel previous search
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      // Add to search history
      addToSearchHistory(searchQuery);

      // Perform client-side filtering for highlighting
      const query = searchQuery.toLowerCase();
      const filtered = requests.filter(request => {
        return (
          request.requestNumber.toLowerCase().includes(query) ||
          request.memberName.toLowerCase().includes(query) ||
          request.providerName.toLowerCase().includes(query) ||
          request.serviceDescription.toLowerCase().includes(query) ||
          request.diagnosis.toLowerCase().includes(query) ||
          request.notes.toLowerCase().includes(query) ||
          request.tags.some(tag => tag.toLowerCase().includes(query))
        );
      });

      setSearchResults(filtered);
      setHighlightTerm(searchQuery);

      return filtered;

    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Search failed:', error);
      }
      return requests;
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, addToSearchHistory]);

  // Quick filter options with counts
  const quickFiltersWithCounts = useMemo(() => {
    return DEFAULT_QUICK_FILTERS.map(filter => ({
      ...filter,
      count: searchResults.length, // This would be calculated based on actual data
    }));
  }, [searchResults.length]);

  // Check if search has active filters
  const hasActiveFilters = useMemo(() => {
    return Object.keys(searchCriteria).length > 0 || activeQuickFilters.length > 0;
  }, [searchCriteria, activeQuickFilters]);

  // Build search summary text
  const searchSummary = useMemo(() => {
    const parts: string[] = [];

    if (searchQuery) {
      parts.push(`"${searchQuery}"`);
    }

    if (activeQuickFilters.length > 0) {
      const filterNames = activeQuickFilters.map(id => {
        const filter = DEFAULT_QUICK_FILTERS.find(f => f.id === id);
        return filter?.label || id;
      });
      parts.push(`Filters: ${filterNames.join(', ')}`);
    }

    if (searchCriteria.dateRange?.from || searchCriteria.dateRange?.to) {
      const from = searchCriteria.dateRange.from;
      const to = searchCriteria.dateRange.to;
      if (from && to) {
        parts.push(`Date: ${from} to ${to}`);
      } else if (from) {
        parts.push(`From: ${from}`);
      } else if (to) {
        parts.push(`Until: ${to}`);
      }
    }

    return parts.join(' • ');
  }, [searchQuery, activeQuickFilters, searchCriteria]);

  return {
    // State
    searchCriteria,
    searchQuery,
    activeQuickFilters,
    savedSearches,
    searchHistory,
    isSearching,
    searchResults,
    highlightTerm,
    hasActiveFilters,
    searchSummary,

    // Quick filters
    quickFilters: DEFAULT_QUICK_FILTERS,
    quickFiltersWithCounts,

    // Actions
    updateSearchCriteria,
    updateSearchQuery,
    clearSearch,
    toggleQuickFilter,
    clearQuickFilters,
    saveSearch,
    loadSavedSearch,
    deleteSavedSearch,
    addToSearchHistory,
    clearSearchHistory,
    performSearch,

    // Refs
    searchInputRef,

    // Utilities
    getHighlightedText: (text: string) => {
      if (!highlightTerm) return text;

      const regex = new RegExp(`(${highlightTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      return text.replace(regex, '<mark>$1</mark>');
    },
  };
}
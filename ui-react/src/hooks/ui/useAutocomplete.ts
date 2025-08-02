import { useState, useEffect, useCallback, useMemo } from 'react';

export interface AutocompleteOption {
  id: string;
  value: string;
  label: string;
  category?: string;
  metadata?: Record<string, any>;
  priority?: number;
}

export interface AutocompleteConfig {
  minLength?: number;
  maxResults?: number;
  debounceMs?: number;
  caseSensitive?: boolean;
  fuzzyMatch?: boolean;
  fuzzyThreshold?: number;
  groupByCategory?: boolean;
  showNoResults?: boolean;
  highlightMatches?: boolean;
}

interface AutocompleteState {
  query: string;
  suggestions: AutocompleteOption[];
  selectedIndex: number;
  isLoading: boolean;
  isOpen: boolean;
  error: string | null;
}

export const useAutocomplete = (
  options: AutocompleteOption[] | ((query: string) => Promise<AutocompleteOption[]>),
  config: AutocompleteConfig = {}
) => {
  const {
    minLength = 1,
    maxResults = 10,
    debounceMs = 300,
    caseSensitive = false,
    fuzzyMatch = true,
    fuzzyThreshold = 60,
    groupByCategory = false,
    showNoResults = true,
    highlightMatches = true
  } = config;

  const [state, setState] = useState<AutocompleteState>({
    query: '',
    suggestions: [],
    selectedIndex: -1,
    isLoading: false,
    isOpen: false,
    error: null
  });

  // Debounced query state
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(state.query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [state.query, debounceMs]);

  // Fuzzy matching algorithm
  const fuzzyScore = useCallback((term: string, target: string): number => {
    if (!term || !target) return 0;

    if (!caseSensitive) {
      term = term.toLowerCase();
      target = target.toLowerCase();
    }

    // Exact match gets highest score
    if (target === term) return 100;

    // Substring match gets high score
    if (target.includes(term)) return 90;

    // Fuzzy character matching
    let score = 0;
    let termIndex = 0;
    let consecutiveMatches = 0;
    let maxConsecutive = 0;

    for (let i = 0; i < target.length && termIndex < term.length; i++) {
      if (target[i] === term[termIndex]) {
        score += 1;
        termIndex++;
        consecutiveMatches++;
        maxConsecutive = Math.max(maxConsecutive, consecutiveMatches);
      } else {
        consecutiveMatches = 0;
      }
    }

    // Bonus for consecutive matches
    score += maxConsecutive * 2;

    // Penalty for unmatched characters
    const unmatchedPenalty = (term.length - termIndex) * 2;
    score = Math.max(0, score - unmatchedPenalty);

    // Calculate percentage
    const maxPossibleScore = term.length + maxConsecutive * 2;
    return maxPossibleScore > 0 ? (score / maxPossibleScore) * 100 : 0;
  }, [caseSensitive]);

  // Filter and sort options
  const filterOptions = useCallback((
    availableOptions: AutocompleteOption[],
    query: string
  ): AutocompleteOption[] => {
    if (!query || query.length < minLength) return [];

    let filtered = availableOptions;

    if (fuzzyMatch) {
      // Fuzzy matching with scoring
      filtered = availableOptions
        .map(option => ({
          ...option,
          _score: Math.max(
            fuzzyScore(query, option.value),
            fuzzyScore(query, option.label),
            option.metadata && option.metadata.searchTerms
              ? Math.max(...option.metadata.searchTerms.map((term: string) => fuzzyScore(query, term)))
              : 0
          )
        }))
        .filter(option => option._score >= fuzzyThreshold)
        .sort((a, b) => {
          // Sort by priority first, then by score
          if (a.priority !== b.priority) {
            return (b.priority || 0) - (a.priority || 0);
          }
          return b._score - a._score;
        });
    } else {
      // Simple substring matching
      const searchTerm = caseSensitive ? query : query.toLowerCase();
      filtered = availableOptions.filter(option => {
        const value = caseSensitive ? option.value : option.value.toLowerCase();
        const label = caseSensitive ? option.label : option.label.toLowerCase();

        return value.includes(searchTerm) ||
               label.includes(searchTerm) ||
               (option.metadata?.searchTerms &&
                option.metadata.searchTerms.some((term: string) =>
                  (caseSensitive ? term : term.toLowerCase()).includes(searchTerm)
                ));
      });
    }

    return filtered.slice(0, maxResults);
  }, [minLength, fuzzyMatch, fuzzyThreshold, fuzzyScore, caseSensitive, maxResults]);

  // Highlight matching text
  const highlightText = useCallback((text: string, query: string): string => {
    if (!highlightMatches || !query) return text;

    const searchTerm = caseSensitive ? query : query.toLowerCase();
    const targetText = caseSensitive ? text : text.toLowerCase();

    const index = targetText.indexOf(searchTerm);
    if (index === -1) return text;

    return text.substring(0, index) +
           `<mark>${text.substring(index, index + query.length)}</mark>` +
           text.substring(index + query.length);
  }, [highlightMatches, caseSensitive]);

  // Group suggestions by category
  const groupedSuggestions = useMemo(() => {
    if (!groupByCategory) return { ungrouped: state.suggestions };

    const groups: { [key: string]: AutocompleteOption[] } = {};

    state.suggestions.forEach(suggestion => {
      const category = suggestion.category || 'Other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(suggestion);
    });

    return groups;
  }, [state.suggestions, groupByCategory]);

  // Fetch suggestions
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query || query.length < minLength) {
      setState(prev => ({
        ...prev,
        suggestions: [],
        isLoading: false,
        isOpen: false,
        error: null
      }));
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      let results: AutocompleteOption[];

      if (typeof options === 'function') {
        // Async function
        results = await options(query);
      } else {
        // Static array
        results = filterOptions(options, query);
      }

      setState(prev => ({
        ...prev,
        suggestions: results,
        isLoading: false,
        isOpen: results.length > 0 || showNoResults,
        selectedIndex: -1
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        suggestions: [],
        isLoading: false,
        isOpen: false,
        error: error instanceof Error ? error.message : 'Failed to fetch suggestions',
        selectedIndex: -1
      }));
    }
  }, [options, minLength, filterOptions, showNoResults]);

  // Update suggestions when debounced query changes
  useEffect(() => {
    fetchSuggestions(debouncedQuery);
  }, [debouncedQuery, fetchSuggestions]);

  // Input handlers
  const setQuery = useCallback((newQuery: string) => {
    setState(prev => ({ ...prev, query: newQuery }));
  }, []);

  const clearQuery = useCallback(() => {
    setState(prev => ({
      ...prev,
      query: '',
      suggestions: [],
      selectedIndex: -1,
      isOpen: false
    }));
  }, []);

  // Navigation handlers
  const selectNext = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedIndex: prev.selectedIndex < prev.suggestions.length - 1
        ? prev.selectedIndex + 1
        : 0
    }));
  }, []);

  const selectPrevious = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedIndex: prev.selectedIndex > 0
        ? prev.selectedIndex - 1
        : prev.suggestions.length - 1
    }));
  }, []);

  const selectSuggestion = useCallback((index: number) => {
    setState(prev => ({ ...prev, selectedIndex: index }));
  }, []);

  const getSelectedSuggestion = useCallback((): AutocompleteOption | null => {
    if (state.selectedIndex >= 0 && state.selectedIndex < state.suggestions.length) {
      return state.suggestions[state.selectedIndex];
    }
    return null;
  }, [state.selectedIndex, state.suggestions]);

  // Keyboard navigation
  const handleKeyDown = useCallback((event: KeyboardEvent | React.KeyboardEvent) => {
    if (!state.isOpen) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        selectNext();
        break;
      case 'ArrowUp':
        event.preventDefault();
        selectPrevious();
        break;
      case 'Enter':
        event.preventDefault();
        const selected = getSelectedSuggestion();
        if (selected) {
          return selected;
        }
        break;
      case 'Escape':
        event.preventDefault();
        setState(prev => ({ ...prev, isOpen: false, selectedIndex: -1 }));
        break;
      case 'Tab':
        // Allow tab to close dropdown
        setState(prev => ({ ...prev, isOpen: false, selectedIndex: -1 }));
        break;
    }
    return null;
  }, [state.isOpen, selectNext, selectPrevious, getSelectedSuggestion]);

  // Close suggestions
  const closeSuggestions = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: false, selectedIndex: -1 }));
  }, []);

  // Open suggestions
  const openSuggestions = useCallback(() => {
    if (state.suggestions.length > 0) {
      setState(prev => ({ ...prev, isOpen: true }));
    }
  }, [state.suggestions.length]);

  return {
    // State
    query: state.query,
    suggestions: state.suggestions,
    groupedSuggestions,
    selectedIndex: state.selectedIndex,
    isLoading: state.isLoading,
    isOpen: state.isOpen,
    error: state.error,

    // Actions
    setQuery,
    clearQuery,
    selectNext,
    selectPrevious,
    selectSuggestion,
    getSelectedSuggestion,
    closeSuggestions,
    openSuggestions,

    // Utilities
    handleKeyDown,
    highlightText,

    // Config
    minLength,
    maxResults
  };
};

export default useAutocomplete;

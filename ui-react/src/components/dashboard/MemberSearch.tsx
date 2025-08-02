import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Search,
  Mic,
  MicOff,
  Filter,
  X,
  Clock,
  Users,
  ScanLine,
  ChevronDown,
  Settings,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { SearchCriteria, SearchSuggestion, Member } from '../../types/healthcare';
import { useMemberSearch } from '../../hooks/data/useMemberSearch';
import { useVoiceSearch } from '../../hooks/ui/useVoiceSearch';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

interface MemberSearchProps {
  onMemberSelect?: (member: Member) => void;
  onSearchResults?: (results: Member[]) => void;
  placeholder?: string;
  className?: string;
  showAdvancedSearch?: boolean;
  showVoiceSearch?: boolean;
  showBarcodeSearch?: boolean;
  autoFocus?: boolean;
}

interface AdvancedSearchFilters {
  provider?: string;
  planType?: string;
  emirate?: string;
  riskLevel?: 'low' | 'medium' | 'high';
  hasChronicConditions?: boolean;
  ageRange?: { min: number; max: number };
  dateRange?: { start: string; end: string };
}

export const MemberSearch: React.FC<MemberSearchProps> = ({
  onMemberSelect,
  onSearchResults,
  placeholder = 'Search by name, Emirates ID, phone, email, or policy number...',
  className = '',
  showAdvancedSearch = true,
  showVoiceSearch = true,
  showBarcodeSearch = false,
  autoFocus = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedSearchFilters>({});

  const searchInputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Custom hooks
  const {
    searchResults,
    isLoading,
    error,
    suggestions,
    searchHistory,
    recentSearches,
    searchStats,
    searchMembers,
    getSuggestions,
    clearSearch,
    loadMore
  } = useMemberSearch();

  const {
    isSupported: voiceSupported,
    isListening,
    transcript,
    interimTranscript,
    confidence,
    error: voiceError,
    startListening,
    stopListening,
    clearTranscript,
    processVoiceCommand
  } = useVoiceSearch({
    language: 'en-US',
    continuous: false,
    interimResults: true,
    autoStop: true,
    timeout: 10000
  });

  // Handle search input changes
  const handleSearchChange = useCallback(async (value: string) => {
    setSearchQuery(value);
    setSelectedSuggestionIndex(-1);

    if (value.length >= 2) {
      await getSuggestions(value);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  }, [getSuggestions]);

  // Handle search submission
  const handleSearch = useCallback(async (query?: string) => {
    const searchTerm = query || searchQuery;
    if (!searchTerm.trim()) return;

    const criteria: SearchCriteria = {
      query: searchTerm,
      ...advancedFilters
    };

    await searchMembers(criteria);
    setShowSuggestions(false);

    if (onSearchResults) {
      onSearchResults(searchResults.members);
    }
  }, [searchQuery, advancedFilters, searchMembers, onSearchResults, searchResults.members]);

  // Handle suggestion selection
  const handleSuggestionSelect = useCallback((suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.label);
    setShowSuggestions(false);

    if (suggestion.type === 'member') {
      handleSearch(suggestion.value);
    } else {
      // Set appropriate filter based on suggestion type
      const newFilters = { ...advancedFilters };
      if (suggestion.type === 'provider') {
        newFilters.provider = suggestion.value;
      }
      setAdvancedFilters(newFilters);
      handleSearch(suggestion.value);
    }
  }, [advancedFilters, handleSearch]);

  // Handle member selection from results
  const handleMemberSelect = useCallback((member: Member) => {
    if (onMemberSelect) {
      onMemberSelect(member);
    }
  }, [onMemberSelect]);

  // Handle voice search results
  useEffect(() => {
    if (transcript) {
      const command = processVoiceCommand();
      if (command) {
        switch (command.action) {
          case 'searchMember':
          case 'search':
            setSearchQuery(command.value);
            handleSearch(command.value);
            break;
          case 'searchById':
            setAdvancedFilters(prev => ({ ...prev, emiratesId: command.value }));
            handleSearch(command.value);
            break;
          case 'searchByPhone':
            setAdvancedFilters(prev => ({ ...prev, phone: command.value }));
            handleSearch(command.value);
            break;
          case 'searchByPolicy':
            setAdvancedFilters(prev => ({ ...prev, policyNumber: command.value }));
            handleSearch(command.value);
            break;
          default:
            setSearchQuery(command.value);
            handleSearch(command.value);
        }
      }
      clearTranscript();
    }
  }, [transcript, processVoiceCommand, handleSearch, clearTranscript]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        handleSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSuggestionSelect(suggestions[selectedSuggestionIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  }, [showSuggestions, suggestions, selectedSuggestionIndex, handleSearch, handleSuggestionSelect]);

  // Handle outside clicks
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Auto-focus
  useEffect(() => {
    if (autoFocus && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [autoFocus]);

  // Handle advanced filter changes
  const handleAdvancedFilterChange = useCallback((
    key: keyof AdvancedSearchFilters,
    value: any
  ) => {
    setAdvancedFilters(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    setAdvancedFilters({});
    setSearchQuery('');
    clearSearch();
  }, [clearSearch]);

  // Handle barcode scan (placeholder - would integrate with camera)
  const handleBarcodeSearch = useCallback(() => {
    // Placeholder for barcode scanning integration
    console.log('Barcode scanning not implemented');
  }, []);

  return (
    <div className={`w-full ${className}`}>
      {/* Main Search Bar */}
      <div className="relative">
        <div className="relative flex items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => {
                if (suggestions.length > 0) {
                  setShowSuggestions(true);
                }
              }}
              placeholder={placeholder}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              disabled={isLoading}
            />

            {/* Voice Search Indicator */}
            {isListening && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-red-500 font-medium">Listening...</span>
                </div>
              </div>
            )}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
              </div>
            )}

            {/* Clear Button */}
            {searchQuery && !isLoading && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  clearSearch();
                }}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 ml-3">
            {/* Voice Search Button */}
            {showVoiceSearch && voiceSupported && (
              <Button
                variant={isListening ? "destructive" : "outline"}
                size="sm"
                onClick={isListening ? stopListening : startListening}
                className="px-3"
              >
                {isListening ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            )}

            {/* Barcode Search Button */}
            {showBarcodeSearch && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleBarcodeSearch}
                className="px-3"
              >
                <ScanLine className="h-4 w-4" />
              </Button>
            )}

            {/* Advanced Search Toggle */}
            {showAdvancedSearch && (
              <Button
                variant={showAdvancedFilters ? "default" : "outline"}
                size="sm"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className="px-3"
              >
                <Filter className="h-4 w-4" />
                <ChevronDown className={`h-3 w-3 ml-1 transition-transform ${
                  showAdvancedFilters ? 'rotate-180' : ''
                }`} />
              </Button>
            )}
          </div>
        </div>

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
          >
            {suggestions.map((suggestion, index) => (
              <button
                key={suggestion.id}
                onClick={() => handleSuggestionSelect(suggestion)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                  index === selectedSuggestionIndex ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      suggestion.type === 'member' ? 'bg-green-500' :
                      suggestion.type === 'provider' ? 'bg-blue-500' :
                      suggestion.type === 'policy' ? 'bg-purple-500' :
                      'bg-orange-500'
                    }`} />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {suggestion.label}
                      </div>
                      <div className="text-xs text-gray-500 capitalize">
                        {suggestion.type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                  {suggestion.memberCount && (
                    <span className="text-xs text-gray-400">
                      {suggestion.memberCount} members
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Recent Searches */}
        {showSuggestions && suggestions.length === 0 && searchHistory.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg"
          >
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
              Recent Searches
            </div>
            {searchHistory.slice(0, 5).map((query, index) => (
              <button
                key={index}
                onClick={() => {
                  setSearchQuery(query);
                  handleSearch(query);
                }}
                className="w-full px-4 py-2 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
              >
                <div className="flex items-center space-x-3">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{query}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Advanced Search Filters */}
      {showAdvancedFilters && (
        <Card className="mt-4 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Advanced Search</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="text-red-600 hover:text-red-700"
            >
              Clear All
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Provider Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Insurance Provider
              </label>
              <select
                value={advancedFilters.provider || ''}
                onChange={(e) => handleAdvancedFilterChange('provider', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Providers</option>
                <option value="Dubai Health Insurance">Dubai Health Insurance</option>
                <option value="Abu Dhabi Health Services">Abu Dhabi Health Services</option>
                <option value="Sharjah Health Authority">Sharjah Health Authority</option>
              </select>
            </div>

            {/* Plan Type Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Plan Type
              </label>
              <select
                value={advancedFilters.planType || ''}
                onChange={(e) => handleAdvancedFilterChange('planType', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Plans</option>
                <option value="Gold Plus">Gold Plus</option>
                <option value="Silver">Silver</option>
                <option value="Bronze">Bronze</option>
                <option value="Essential">Essential</option>
              </select>
            </div>

            {/* Risk Level Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Risk Level
              </label>
              <select
                value={advancedFilters.riskLevel || ''}
                onChange={(e) => handleAdvancedFilterChange('riskLevel', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Risk Levels</option>
                <option value="low">Low Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="high">High Risk</option>
              </select>
            </div>

            {/* Emirate Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Emirate
              </label>
              <select
                value={advancedFilters.emirate || ''}
                onChange={(e) => handleAdvancedFilterChange('emirate', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All Emirates</option>
                <option value="Dubai">Dubai</option>
                <option value="Abu Dhabi">Abu Dhabi</option>
                <option value="Sharjah">Sharjah</option>
                <option value="Ajman">Ajman</option>
                <option value="Umm Al Quwain">Umm Al Quwain</option>
                <option value="Ras Al Khaimah">Ras Al Khaimah</option>
                <option value="Fujairah">Fujairah</option>
              </select>
            </div>

            {/* Age Range Filter */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Age Range
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={advancedFilters.ageRange?.min || ''}
                  onChange={(e) => handleAdvancedFilterChange('ageRange', {
                    ...advancedFilters.ageRange,
                    min: e.target.value ? parseInt(e.target.value) : undefined
                  })}
                  className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={advancedFilters.ageRange?.max || ''}
                  onChange={(e) => handleAdvancedFilterChange('ageRange', {
                    ...advancedFilters.ageRange,
                    max: e.target.value ? parseInt(e.target.value) : undefined
                  })}
                  className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Chronic Conditions Filter */}
            <div className="flex items-center">
              <input
                id="chronic-conditions"
                type="checkbox"
                checked={advancedFilters.hasChronicConditions || false}
                onChange={(e) => handleAdvancedFilterChange('hasChronicConditions', e.target.checked || undefined)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="chronic-conditions" className="ml-2 text-sm text-gray-700">
                Has chronic conditions
              </label>
            </div>
          </div>

          {/* Apply Filters Button */}
          <div className="mt-4 flex justify-end">
            <Button
              onClick={() => handleSearch()}
              disabled={isLoading}
              className="px-6"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                'Apply Filters'
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* Voice Search Status */}
      {voiceError && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-red-500 mr-2" />
            <span className="text-sm text-red-700">{voiceError}</span>
          </div>
        </div>
      )}

      {/* Search Results Summary */}
      {searchStats.hasResults && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <Users className="h-4 w-4 mr-1" />
              {searchStats.totalMembers} members found
            </span>
            {confidence > 0 && (
              <span className="text-blue-600">
                Voice confidence: {Math.round(confidence * 100)}%
              </span>
            )}
          </div>

          {searchStats.canLoadMore && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => loadMore({ query: searchQuery, ...advancedFilters })}
              disabled={isLoading}
            >
              Load more
            </Button>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-red-500 mr-2" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemberSearch;

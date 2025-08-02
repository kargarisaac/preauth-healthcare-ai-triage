import React, { useState, useCallback } from 'react';
import {
  Search,
  X,
  Clock,
  AlertTriangle,
  DollarSign,
  Calendar,
  FileX,
  Bookmark,
  History,
  Plus,
  ChevronDown,
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import { useRequestSearch } from '@/hooks/data/useRequestSearch';
import type { SavedSearch } from '@/types/requests';

interface QuickFilterBadgeProps {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  id: string;
  label: string;
  icon: React.ElementType;
  count?: number;
  color?: string;
  isActive: boolean;
  onClick: () => void;
}

const QuickFilterBadge: React.FC<QuickFilterBadgeProps> = ({
  id,
  label,
  icon: Icon,
  count,
  color = 'gray',
  isActive,
  onClick,
}) => {
  const colorClasses = {
    gray: isActive ? 'bg-gray-200 text-gray-800 border-gray-300' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50',
    blue: isActive ? 'bg-blue-200 text-blue-800 border-blue-300' : 'bg-white text-blue-600 border-blue-200 hover:bg-blue-50',
    red: isActive ? 'bg-red-200 text-red-800 border-red-300' : 'bg-white text-red-600 border-red-200 hover:bg-red-50',
    yellow: isActive ? 'bg-yellow-200 text-yellow-800 border-yellow-300' : 'bg-white text-yellow-600 border-yellow-200 hover:bg-yellow-50',
    green: isActive ? 'bg-green-200 text-green-800 border-green-300' : 'bg-white text-green-600 border-green-200 hover:bg-green-50',
    orange: isActive ? 'bg-orange-200 text-orange-800 border-orange-300' : 'bg-white text-orange-600 border-orange-200 hover:bg-orange-50',
  };

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center px-3 py-2 border rounded-full text-sm font-medium transition-colors ${colorClasses[color as keyof typeof colorClasses]}`}
    >
      <Icon className="w-4 h-4 mr-2" />
      {label}
      {count !== undefined && (
        <span className="ml-2 px-2 py-0.5 bg-current bg-opacity-20 rounded-full text-xs">
          {count}
        </span>
      )}
    </button>
  );
};

interface SaveSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string, description?: string) => void;
}

const SaveSearchModal: React.FC<SaveSearchModalProps> = ({ isOpen, onClose, onSave }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSave = () => {
    if (name.trim()) {
      onSave(name.trim(), description.trim() || undefined);
      setName('');
      setDescription('');
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Save Search">
      <div className="space-y-4">
        <div>
          <label htmlFor="search-name" className="block text-sm font-medium text-gray-700 mb-2">
            Search Name
          </label>
          <input
            id="search-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter search name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div>
          <label htmlFor="search-description" className="block text-sm font-medium text-gray-700 mb-2">
            Description (optional)
          </label>
          <textarea
            id="search-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter description"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="flex justify-end space-x-3">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            Save Search
          </Button>
        </div>
      </div>
    </Modal>
  );
};

interface SavedSearchDropdownProps {
  savedSearches: SavedSearch[];
  onLoad: (searchId: string) => void;
  onDelete: (searchId: string) => void;
}

const SavedSearchDropdown: React.FC<SavedSearchDropdownProps> = ({
  savedSearches,
  onLoad,
  onDelete,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (savedSearches.length === 0) {
    return null;
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm"
      >
        <Bookmark className="w-4 h-4 mr-2" />
        Saved Searches
        <ChevronDown className="w-4 h-4 ml-2" />
      </Button>
      
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-20">
            <div className="py-1 max-h-64 overflow-y-auto">
              {savedSearches.map((search) => (
                <div
                  key={search.id}
                  className="px-4 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => {
                        onLoad(search.id);
                        setIsOpen(false);
                      }}
                      className="flex-1 text-left"
                    >
                      <div className="font-medium text-gray-900">{search.name}</div>
                      {search.description && (
                        <div className="text-sm text-gray-500 truncate">{search.description}</div>
                      )}
                      <div className="text-xs text-gray-400">
                        {new Date(search.createdAt).toLocaleDateString()}
                      </div>
                    </button>
                    <button
                      onClick={() => onDelete(search.id)}
                      className="ml-2 p-1 text-gray-400 hover:text-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

interface RequestSearchProps {
  className?: string;
}

export function RequestSearch({ className = '' }: RequestSearchProps) {
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const {
    searchQuery,
    activeQuickFilters,
    savedSearches,
    searchHistory,
    hasActiveFilters,
    quickFiltersWithCounts,
    updateSearchQuery,
    clearSearch,
    toggleQuickFilter,
    clearQuickFilters,
    saveSearch,
    loadSavedSearch,
    deleteSavedSearch,
    clearSearchHistory,
    searchInputRef,
  } = useRequestSearch();

  const handleSaveSearch = useCallback((name: string, description?: string) => {
    saveSearch(name, description);
  }, [saveSearch]);

  const handleSearchFromHistory = useCallback((query: string) => {
    updateSearchQuery(query);
    setShowHistory(false);
  }, [updateSearchQuery]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => updateSearchQuery(e.target.value)}
            placeholder="Search requests by number, member, provider, service, or diagnosis..."
            className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {searchQuery && (
            <button
              onClick={() => updateSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            </button>
          )}
        </div>

        {/* Search Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {searchHistory.length > 0 && (
              <div className="relative">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-sm"
                >
                  <History className="w-4 h-4 mr-2" />
                  History
                </Button>
                
                {showHistory && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setShowHistory(false)} />
                    <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-md shadow-lg z-20">
                      <div className="py-2">
                        <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">Recent Searches</span>
                          <button
                            onClick={clearSearchHistory}
                            className="text-xs text-gray-500 hover:text-red-600"
                          >
                            Clear All
                          </button>
                        </div>
                        <div className="max-h-48 overflow-y-auto">
                          {searchHistory.map((query, index) => (
                            <button
                              key={index}
                              onClick={() => handleSearchFromHistory(query)}
                              className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                            >
                              {query}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
            
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearSearch}
                className="text-red-600 border-red-200 hover:bg-red-50"
              >
                <X className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <SavedSearchDropdown
              savedSearches={savedSearches}
              onLoad={loadSavedSearch}
              onDelete={deleteSavedSearch}
            />
            
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSaveModal(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                Save Search
              </Button>
            )}
          </div>
        </div>

        {/* Quick Filters */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">Quick Filters</h3>
            {activeQuickFilters.length > 0 && (
              <button
                onClick={clearQuickFilters}
                className="text-sm text-gray-500 hover:text-red-600"
              >
                Clear Filters
              </button>
            )}
          </div>
          
          <div className="flex flex-wrap gap-2">
            {quickFiltersWithCounts.map((filter) => (
              <QuickFilterBadge
                key={filter.id}
                id={filter.id}
                label={filter.label}
                icon={
                  filter.icon === 'clock' ? Clock :
                  filter.icon === 'alert-triangle' ? AlertTriangle :
                  filter.icon === 'dollar-sign' ? DollarSign :
                  filter.icon === 'calendar' ? Calendar :
                  filter.icon === 'file-x' ? FileX :
                  Search
                }
                count={filter.count}
                color={filter.color}
                isActive={activeQuickFilters.includes(filter.id)}
                onClick={() => toggleQuickFilter(filter.id)}
              />
            ))}
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-blue-800">
                <span className="font-medium">Active search:</span> {searchQuery || 'No search query'}
              </div>
              {activeQuickFilters.length > 0 && (
                <div className="text-sm text-blue-600">
                  {activeQuickFilters.length} filter{activeQuickFilters.length > 1 ? 's' : ''} applied
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Save Search Modal */}
      <SaveSearchModal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        onSave={handleSaveSearch}
      />
    </Card>
  );
}
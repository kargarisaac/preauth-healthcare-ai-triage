import React, { useState, useRef, useEffect, useMemo } from 'react';
import { clsx } from 'clsx';
import { Search, X, Check, AlertCircle } from 'lucide-react';

export interface AutocompleteOption {
  /** Unique identifier for the option */
  id: string;
  /** Display label for the option */
  label: string;
  /** Optional secondary text (e.g., code, description) */
  description?: string;
  /** Option value (defaults to id if not provided) */
  value?: string;
  /** Whether the option is disabled */
  disabled?: boolean;
  /** Medical coding information */
  medical?: {
    /** Medical code (ICD-10, CPT, etc.) */
    code?: string;
    /** Code system (e.g., 'ICD-10', 'CPT', 'LOINC') */
    system?: string;
    /** Category or classification */
    category?: string;
    /** Additional medical context */
    context?: string;
  };
}

export interface AutocompleteProps {
  /** Array of available options */
  options: AutocompleteOption[];
  /** Current selected value(s) */
  value?: string | string[];
  /** Default value (for uncontrolled usage) */
  defaultValue?: string | string[];
  /** Callback when selection changes */
  onChange?: (value: string | string[] | undefined) => void;
  /** Input placeholder text */
  placeholder?: string;
  /** Whether multiple selections are allowed */
  multiple?: boolean;
  /** Whether the input is disabled */
  disabled?: boolean;
  /** Whether the input is required */
  required?: boolean;
  /** Error message to display */
  error?: string;
  /** Helper text to display */
  helperText?: string;
  /** Input label */
  label?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Custom class name */
  className?: string;
  /** Custom class name for the input */
  inputClassName?: string;
  /** Loading state */
  loading?: boolean;
  /** Whether to show medical codes in options */
  showMedicalCodes?: boolean;
  /** Function to filter options (overrides default filtering) */
  filterOptions?: (options: AutocompleteOption[], inputValue: string) => AutocompleteOption[];
  /** Custom option renderer */
  renderOption?: (option: AutocompleteOption, isSelected: boolean, isHighlighted: boolean) => React.ReactNode;
  /** Maximum number of options to display */
  maxDisplayedOptions?: number;
  /** Whether to allow custom values (free text) */
  allowCustomValues?: boolean;
  /** Minimum characters before showing suggestions */
  minSearchLength?: number;
  /** Debounce delay for search in milliseconds */
  searchDebounce?: number;
}

/**
 * Autocomplete component optimized for healthcare data entry.
 * 
 * Features medical-specific functionality like:
 * - ICD-10, CPT, and LOINC code search
 * - Diagnosis and procedure lookups
 * - Drug name and dosage suggestions
 * - Provider and facility searches
 * - Multiple selection for complex medical histories
 * 
 * @example
 * ```tsx
 * // ICD-10 diagnosis search
 * const diagnosisOptions = [
 *   {
 *     id: 'E11.9',
 *     label: 'Type 2 diabetes mellitus without complications',
 *     medical: { code: 'E11.9', system: 'ICD-10', category: 'Endocrine' }
 *   },
 *   {
 *     id: 'I10',
 *     label: 'Essential hypertension',
 *     medical: { code: 'I10', system: 'ICD-10', category: 'Circulatory' }
 *   }
 * ];
 * 
 * <Autocomplete
 *   label="Primary Diagnosis"
 *   options={diagnosisOptions}
 *   value={selectedDiagnosis}
 *   onChange={setSelectedDiagnosis}
 *   showMedicalCodes
 *   placeholder="Search for diagnosis..."
 * />
 * ```
 */
const Autocomplete: React.FC<AutocompleteProps> = ({
  options,
  value,
  defaultValue,
  onChange,
  placeholder = 'Search...',
  multiple = false,
  disabled = false,
  required = false,
  error,
  helperText,
  label,
  size = 'md',
  className,
  inputClassName,
  loading = false,
  showMedicalCodes = false,
  filterOptions,
  renderOption,
  maxDisplayedOptions = 10,
  allowCustomValues = false,
  minSearchLength = 1,
  searchDebounce = 300,
}) => {
  const [internalValue, setInternalValue] = useState<string | string[]>(
    defaultValue || (multiple ? [] : '')
  );
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const currentValue = value !== undefined ? value : internalValue;
  const selectedValues = Array.isArray(currentValue) ? currentValue : currentValue ? [currentValue] : [];

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(inputValue);
    }, searchDebounce);

    return () => clearTimeout(timer);
  }, [inputValue, searchDebounce]);

  // Filter options based on search
  const filteredOptions = useMemo(() => {
    if (debouncedSearchTerm.length < minSearchLength) {
      return [];
    }

    let filtered: AutocompleteOption[];

    if (filterOptions) {
      filtered = filterOptions(options, debouncedSearchTerm);
    } else {
      const searchTerm = debouncedSearchTerm.toLowerCase();
      filtered = options.filter(option => {
        const labelMatch = option.label.toLowerCase().includes(searchTerm);
        const descriptionMatch = option.description?.toLowerCase().includes(searchTerm);
        const codeMatch = option.medical?.code?.toLowerCase().includes(searchTerm);
        const categoryMatch = option.medical?.category?.toLowerCase().includes(searchTerm);
        
        return labelMatch || descriptionMatch || codeMatch || categoryMatch;
      });
    }

    // Remove already selected options in multiple mode
    if (multiple) {
      filtered = filtered.filter(option => 
        !selectedValues.includes(option.value || option.id)
      );
    }

    return filtered.slice(0, maxDisplayedOptions);
  }, [options, debouncedSearchTerm, minSearchLength, filterOptions, multiple, selectedValues, maxDisplayedOptions]);

  // Handle clicks outside component
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsOpen(true);
    setHighlightedIndex(-1);
  };

  const handleOptionSelect = (option: AutocompleteOption) => {
    const optionValue = option.value || option.id;

    if (multiple) {
      const newValues = [...selectedValues, optionValue];
      setInternalValue(newValues);
      onChange?.(newValues);
      setInputValue('');
    } else {
      setInternalValue(optionValue);
      onChange?.(optionValue);
      setInputValue(option.label);
      setIsOpen(false);
    }

    setHighlightedIndex(-1);
  };

  const handleOptionRemove = (optionValue: string) => {
    if (multiple) {
      const newValues = selectedValues.filter(v => v !== optionValue);
      setInternalValue(newValues);
      onChange?.(newValues);
    } else {
      setInternalValue('');
      onChange?.(undefined);
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      setIsOpen(true);
      return;
    }

    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredOptions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
          handleOptionSelect(filteredOptions[highlightedIndex]);
        } else if (allowCustomValues && inputValue.trim()) {
          const customOption: AutocompleteOption = {
            id: inputValue.trim(),
            label: inputValue.trim(),
            value: inputValue.trim()
          };
          handleOptionSelect(customOption);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        inputRef.current?.blur();
        break;
      case 'Tab':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  };

  const handleFocus = () => {
    if (!disabled && inputValue.length >= minSearchLength) {
      setIsOpen(true);
    }
  };

  const getSelectedOption = (optionValue: string) => {
    return options.find(option => (option.value || option.id) === optionValue);
  };

  const inputSizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-4 py-3 text-lg',
  };

  const hasError = !!error;

  return (
    <div ref={containerRef} className={clsx('relative', className)}>
      {/* Label */}
      {label && (
        <label
          htmlFor={`autocomplete-${label}`}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}

      {/* Selected Items (Multiple Mode) */}
      {multiple && selectedValues.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedValues.map(selectedValue => {
            const option = getSelectedOption(selectedValue);
            return (
              <div
                key={selectedValue}
                className="inline-flex items-center px-2 py-1 bg-primary-100 text-primary-800 rounded-md text-sm"
              >
                <span className="mr-1">
                  {option?.label || selectedValue}
                  {showMedicalCodes && option?.medical?.code && (
                    <span className="ml-1 text-primary-600 font-mono text-xs">
                      ({option.medical.code})
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  className="ml-1 hover:text-primary-900 focus:outline-none focus:text-primary-900"
                  onClick={() => handleOptionRemove(selectedValue)}
                  aria-label={`Remove ${option?.label || selectedValue}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Input */}
      <div className="relative">
        <input
          ref={inputRef}
          id={`autocomplete-${label}`}
          type="text"
          value={inputValue}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          autoComplete="off"
          className={clsx(
            'input pr-10',
            inputSizeClasses[size],
            hasError && 'input-error',
            disabled && 'opacity-50 cursor-not-allowed',
            inputClassName
          )}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-autocomplete="list"
          role="combobox"
        />

        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
          {loading ? (
            <div className="w-5 h-5 border-2 border-gray-200 border-t-primary-500 rounded-full animate-spin" />
          ) : (
            <Search className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Options Dropdown */}
      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-large max-h-60 overflow-auto">
          <ul ref={listRef} role="listbox" className="py-1">
            {filteredOptions.map((option, index) => {
              const isHighlighted = index === highlightedIndex;
              const isSelected = selectedValues.includes(option.value || option.id);

              if (renderOption) {
                return (
                  <li key={option.id} role="option" aria-selected={isSelected}>
                    <button
                      type="button"
                      className="w-full text-left focus:outline-none"
                      onClick={() => handleOptionSelect(option)}
                      disabled={option.disabled}
                    >
                      {renderOption(option, isSelected, isHighlighted)}
                    </button>
                  </li>
                );
              }

              return (
                <li key={option.id} role="option" aria-selected={isSelected}>
                  <button
                    type="button"
                    className={clsx(
                      'w-full px-4 py-2 text-left focus:outline-none transition-colors',
                      'hover:bg-gray-50 focus:bg-gray-50',
                      isHighlighted && 'bg-gray-50',
                      isSelected && 'bg-primary-50 text-primary-900',
                      option.disabled && 'opacity-50 cursor-not-allowed'
                    )}
                    onClick={() => !option.disabled && handleOptionSelect(option)}
                    disabled={option.disabled}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center">
                          <span className="font-medium text-gray-900 truncate">
                            {option.label}
                          </span>
                          {showMedicalCodes && option.medical?.code && (
                            <span className="ml-2 text-gray-500 font-mono text-sm">
                              {option.medical.code}
                            </span>
                          )}
                        </div>
                        
                        {option.description && (
                          <p className="text-sm text-gray-600 truncate mt-0.5">
                            {option.description}
                          </p>
                        )}
                        
                        {option.medical?.category && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {option.medical.category}
                            {option.medical.system && ` • ${option.medical.system}`}
                          </p>
                        )}
                      </div>
                      
                      {isSelected && (
                        <Check className="w-5 h-5 text-primary-600 flex-shrink-0 ml-2" />
                      )}
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* No Results */}
      {isOpen && filteredOptions.length === 0 && debouncedSearchTerm.length >= minSearchLength && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-large p-4">
          <div className="flex items-center text-gray-500">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>No results found</span>
          </div>
          {allowCustomValues && inputValue.trim() && (
            <button
              type="button"
              className="mt-2 w-full px-3 py-2 text-left text-primary-600 hover:bg-primary-50 rounded-md"
              onClick={() => {
                const customOption: AutocompleteOption = {
                  id: inputValue.trim(),
                  label: inputValue.trim(),
                  value: inputValue.trim()
                };
                handleOptionSelect(customOption);
              }}
            >
              Add "{inputValue.trim()}"
            </button>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-error-600">
          {error}
        </p>
      )}

      {/* Helper Text */}
      {helperText && !hasError && (
        <p className="mt-1 text-sm text-gray-600">
          {helperText}
        </p>
      )}
    </div>
  );
};

export default Autocomplete;
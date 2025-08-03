import React, { useState, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import { Calendar, ChevronLeft, ChevronRight, Clock } from 'lucide-react';

export interface DatePickerProps {
  /** Current selected date value */
  value?: Date;
  /** Default date value (for uncontrolled usage) */
  defaultValue?: Date;
  /** Callback when date changes */
  onChange?: (date: Date | undefined) => void;
  /** Input placeholder text */
  placeholder?: string;
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
  /** Minimum selectable date */
  minDate?: Date;
  /** Maximum selectable date */
  maxDate?: Date;
  /** Whether to include time selection */
  includeTime?: boolean;
  /** Date format for display */
  dateFormat?: 'short' | 'medium' | 'long';
  /** Healthcare-specific presets */
  showMedicalPresets?: boolean;
  /** Custom class name for the input */
  inputClassName?: string;
  /** Whether to show clear button */
  showClearButton?: boolean;
  /** Custom validation function */
  validate?: (date: Date) => string | undefined;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

/**
 * DatePicker component optimized for healthcare workflows.
 * 
 * Features medical-specific functionality like:
 * - Appointment scheduling presets (today, tomorrow, next week)
 * - Medical date ranges (birth dates, visit dates, etc.)
 * - Time selection for appointments
 * - Keyboard navigation and accessibility
 * - Touch-friendly interface for mobile devices
 * 
 * @example
 * ```tsx
 * // Basic appointment scheduling
 * <DatePicker
 *   label="Appointment Date"
 *   value={appointmentDate}
 *   onChange={setAppointmentDate}
 *   includeTime
 *   showMedicalPresets
 *   minDate={new Date()} // No past dates
 * />
 * 
 * // Birth date selection
 * <DatePicker
 *   label="Date of Birth"
 *   value={birthDate}
 *   onChange={setBirthDate}
 *   maxDate={new Date()} // No future dates
 *   dateFormat="long"
 * />
 * ```
 */
const DatePicker: React.FC<DatePickerProps> = ({
  value,
  defaultValue,
  onChange,
  placeholder = 'Select date',
  disabled = false,
  required = false,
  error,
  helperText,
  label,
  size = 'md',
  className,
  minDate,
  maxDate,
  includeTime = false,
  dateFormat = 'medium',
  showMedicalPresets = false,
  inputClassName,
  showClearButton = true,
  validate,
}) => {
  const [internalValue, setInternalValue] = useState<Date | undefined>(defaultValue);
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState({ hours: 9, minutes: 0 });
  const [validationError, setValidationError] = useState<string | undefined>();

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const currentValue = value || internalValue;

  useEffect(() => {
    if (currentValue) {
      setViewDate(new Date(currentValue));
      setSelectedTime({
        hours: currentValue.getHours(),
        minutes: currentValue.getMinutes()
      });
    }
  }, [currentValue]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatDate = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
      short: { year: 'numeric', month: 'numeric', day: 'numeric' },
      medium: { year: 'numeric', month: 'short', day: 'numeric' },
      long: { year: 'numeric', month: 'long', day: 'numeric' }
    }[dateFormat];

    let formatted = date.toLocaleDateString('en-US', options);

    if (includeTime) {
      const timeOptions: Intl.DateTimeFormatOptions = {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      };
      formatted += ' ' + date.toLocaleTimeString('en-US', timeOptions);
    }

    return formatted;
  };

  const handleDateSelect = (date: Date) => {
    let newDate = new Date(date);
    
    if (includeTime) {
      newDate.setHours(selectedTime.hours, selectedTime.minutes);
    }

    // Validate date
    if (validate) {
      const validationResult = validate(newDate);
      setValidationError(validationResult);
      if (validationResult) return;
    }

    // Check min/max dates
    if (minDate && newDate < minDate) {
      setValidationError('Date cannot be before minimum date');
      return;
    }
    if (maxDate && newDate > maxDate) {
      setValidationError('Date cannot be after maximum date');
      return;
    }

    setValidationError(undefined);
    setInternalValue(newDate);
    onChange?.(newDate);
    
    if (!includeTime) {
      setIsOpen(false);
    }
  };

  const handleTimeChange = (hours: number, minutes: number) => {
    setSelectedTime({ hours, minutes });
    
    if (currentValue) {
      const newDate = new Date(currentValue);
      newDate.setHours(hours, minutes);
      setInternalValue(newDate);
      onChange?.(newDate);
    }
  };

  const handleClear = () => {
    setInternalValue(undefined);
    onChange?.(undefined);
    setValidationError(undefined);
  };

  const handlePresetSelect = (preset: string) => {
    const today = new Date();
    let presetDate: Date;

    switch (preset) {
      case 'today':
        presetDate = new Date(today);
        break;
      case 'tomorrow':
        presetDate = new Date(today);
        presetDate.setDate(today.getDate() + 1);
        break;
      case 'next_week':
        presetDate = new Date(today);
        presetDate.setDate(today.getDate() + 7);
        break;
      case 'next_month':
        presetDate = new Date(today);
        presetDate.setMonth(today.getMonth() + 1);
        break;
      default:
        return;
    }

    if (includeTime) {
      presetDate.setHours(selectedTime.hours, selectedTime.minutes);
    }

    handleDateSelect(presetDate);
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(viewDate);
    if (direction === 'prev') {
      newDate.setMonth(viewDate.getMonth() - 1);
    } else {
      newDate.setMonth(viewDate.getMonth() + 1);
    }
    setViewDate(newDate);
  };

  const isDateDisabled = (date: Date) => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    return false;
  };

  const renderCalendar = () => {
    const firstDay = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
    const lastDay = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    const days = [];
    const currentDate = new Date(startDate);

    for (let i = 0; i < 42; i++) {
      const date = new Date(currentDate);
      const isCurrentMonth = date.getMonth() === viewDate.getMonth();
      const isToday = date.toDateString() === new Date().toDateString();
      const isSelected = currentValue && date.toDateString() === currentValue.toDateString();
      const isDisabled = isDateDisabled(date);

      days.push(
        <button
          key={i}
          type="button"
          className={clsx(
            'w-8 h-8 text-sm rounded-lg transition-colors duration-200',
            'hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500',
            isCurrentMonth ? 'text-gray-900' : 'text-gray-400',
            isToday && !isSelected && 'bg-gray-100 font-semibold',
            isSelected && 'bg-primary-500 text-white font-semibold',
            isDisabled && 'opacity-50 cursor-not-allowed'
          )}
          disabled={isDisabled}
          onClick={() => handleDateSelect(date)}
          aria-label={`Select ${date.toDateString()}`}
        >
          {date.getDate()}
        </button>
      );

      currentDate.setDate(currentDate.getDate() + 1);
    }

    return days;
  };

  const inputSizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-4 py-3 text-lg',
  };

  const displayValue = currentValue ? formatDate(currentValue) : '';
  const hasError = !!(error || validationError);

  return (
    <div ref={containerRef} className={clsx('relative', className)}>
      {/* Label */}
      {label && (
        <label
          htmlFor={`datepicker-${label}`}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}

      {/* Input */}
      <div className="relative">
        <input
          ref={inputRef}
          id={`datepicker-${label}`}
          type="text"
          value={displayValue}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          readOnly
          className={clsx(
            'input pr-10',
            inputSizeClasses[size],
            hasError && 'input-error',
            disabled && 'opacity-50 cursor-not-allowed',
            'cursor-pointer',
            inputClassName
          )}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
              e.preventDefault();
              setIsOpen(!isOpen);
            }
          }}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
          aria-label={`${label || 'Date picker'}, ${displayValue || 'no date selected'}`}
        />

        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <Calendar className="w-5 h-5 text-gray-400" />
        </div>

        {/* Clear Button */}
        {showClearButton && currentValue && !disabled && (
          <button
            type="button"
            className="absolute inset-y-0 right-8 flex items-center pr-1 text-gray-400 hover:text-gray-600"
            onClick={(e) => {
              e.stopPropagation();
              handleClear();
            }}
            aria-label="Clear date"
          >
            ×
          </button>
        )}
      </div>

      {/* Calendar Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 bg-white border border-gray-300 rounded-lg shadow-large p-4 min-w-80">
          {/* Medical Presets */}
          {showMedicalPresets && (
            <div className="mb-4 pb-4 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Select</h4>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'today', label: 'Today' },
                  { key: 'tomorrow', label: 'Tomorrow' },
                  { key: 'next_week', label: 'Next Week' },
                  { key: 'next_month', label: 'Next Month' },
                ].map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    className="px-3 py-1.5 text-sm text-gray-700 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                    onClick={() => handlePresetSelect(preset.key)}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-4">
            <button
              type="button"
              className="p-1 hover:bg-gray-100 rounded focus-ring"
              onClick={() => navigateMonth('prev')}
              aria-label="Previous month"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-semibold text-gray-900">
              {MONTHS[viewDate.getMonth()]} {viewDate.getFullYear()}
            </h3>

            <button
              type="button"
              className="p-1 hover:bg-gray-100 rounded focus-ring"
              onClick={() => navigateMonth('next')}
              aria-label="Next month"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="mb-4">
            {/* Day Headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {DAYS.map((day) => (
                <div key={day} className="text-center text-sm font-medium text-gray-500 py-1">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7 gap-1">
              {renderCalendar()}
            </div>
          </div>

          {/* Time Selection */}
          {includeTime && (
            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Time</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <select
                  value={selectedTime.hours}
                  onChange={(e) => handleTimeChange(Number(e.target.value), selectedTime.minutes)}
                  className="px-2 py-1 border border-gray-300 rounded text-sm focus-ring"
                  aria-label="Hours"
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>
                      {i.toString().padStart(2, '0')}
                    </option>
                  ))}
                </select>
                
                <span className="text-gray-500">:</span>
                
                <select
                  value={selectedTime.minutes}
                  onChange={(e) => handleTimeChange(selectedTime.hours, Number(e.target.value))}
                  className="px-2 py-1 border border-gray-300 rounded text-sm focus-ring"
                  aria-label="Minutes"
                >
                  {Array.from({ length: 60 }, (_, i) => (
                    <option key={i} value={i}>
                      {i.toString().padStart(2, '0')}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {(error || validationError) && (
        <p className="mt-1 text-sm text-error-600">
          {error || validationError}
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

export default DatePicker;
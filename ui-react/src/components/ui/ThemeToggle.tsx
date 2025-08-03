import React, { useState } from 'react';
import { Sun, Moon, Monitor, Palette, Settings, Check } from 'lucide-react';
import { clsx } from 'clsx';
import { useTheme, type ThemeMode } from '@/contexts/ThemeContext';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setHighContrast, setReducedMotion } from '@/store/slices/userPreferencesSlice';

interface ThemeToggleProps {
  variant?: 'icon' | 'button' | 'dropdown' | 'switch';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

// Simple icon toggle
function IconToggle({ size = 'md', className }: Pick<ThemeToggleProps, 'size' | 'className'>) {
  const { actualTheme, toggleTheme } = useTheme();
  
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <button
      onClick={toggleTheme}
      className={clsx(
        'p-2 rounded-lg transition-all duration-200',
        'hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        'dark:focus:ring-offset-dark-bg-primary',
        className
      )}
      aria-label={`Switch to ${actualTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {actualTheme === 'dark' ? (
        <Sun className={clsx(sizeClasses[size], 'text-yellow-500')} />
      ) : (
        <Moon className={clsx(sizeClasses[size], 'text-gray-700 dark:text-dark-text-primary')} />
      )}
    </button>
  );
}

// Button toggle with text
function ButtonToggle({ size = 'md', showLabel = true, className }: Pick<ThemeToggleProps, 'size' | 'showLabel' | 'className'>) {
  const { actualTheme, toggleTheme } = useTheme();
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-3 py-2 text-base',
    lg: 'px-4 py-3 text-lg'
  };

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <button
      onClick={toggleTheme}
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg transition-all duration-200',
        'bg-white dark:bg-dark-bg-secondary',
        'border border-gray-300 dark:border-dark-border-primary',
        'hover:bg-gray-50 dark:hover:bg-dark-bg-tertiary',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        'dark:focus:ring-offset-dark-bg-primary',
        'text-gray-700 dark:text-dark-text-primary',
        sizeClasses[size],
        className
      )}
      aria-label={`Switch to ${actualTheme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {actualTheme === 'dark' ? (
        <Sun className={clsx(iconSizeClasses[size], 'text-yellow-500')} />
      ) : (
        <Moon className={clsx(iconSizeClasses[size])} />
      )}
      {showLabel && (
        <span>{actualTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
      )}
    </button>
  );
}

// Switch toggle (iOS-style)
function SwitchToggle({ size = 'md', className }: Pick<ThemeToggleProps, 'size' | 'className'>) {
  const { actualTheme, toggleTheme } = useTheme();
  const isDark = actualTheme === 'dark';
  
  const sizeClasses = {
    sm: 'w-8 h-4',
    md: 'w-10 h-5',
    lg: 'w-12 h-6'
  };

  const thumbSizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  const thumbTranslateClasses = {
    sm: isDark ? 'translate-x-4' : 'translate-x-0.5',
    md: isDark ? 'translate-x-5' : 'translate-x-0.5',
    lg: isDark ? 'translate-x-6' : 'translate-x-0.5'
  };

  return (
    <button
      onClick={toggleTheme}
      className={clsx(
        'relative rounded-full transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        'dark:focus:ring-offset-dark-bg-primary',
        isDark 
          ? 'bg-primary-500' 
          : 'bg-gray-300 dark:bg-dark-border-primary',
        sizeClasses[size],
        className
      )}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      role="switch"
      aria-checked={isDark}
    >
      <div
        className={clsx(
          'absolute top-0.5 left-0.5 rounded-full transition-transform duration-200',
          'bg-white shadow-sm',
          'flex items-center justify-center',
          thumbSizeClasses[size],
          thumbTranslateClasses[size]
        )}
      >
        {isDark ? (
          <Moon className="w-2 h-2 text-primary-600" />
        ) : (
          <Sun className="w-2 h-2 text-yellow-600" />
        )}
      </div>
    </button>
  );
}

// Advanced dropdown with all options
function DropdownToggle({ size = 'md', className }: Pick<ThemeToggleProps, 'size' | 'className'>) {
  const { theme, setTheme, systemTheme, actualTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useAppDispatch();
  const { highContrast, reducedMotion } = useAppSelector(state => state.userPreferences);

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  const themeOptions: Array<{
    value: ThemeMode;
    label: string;
    icon: React.ReactNode;
    description: string;
  }> = [
    {
      value: 'light',
      label: 'Light',
      icon: <Sun className={iconSizeClasses[size]} />,
      description: 'Classic light interface'
    },
    {
      value: 'dark',
      label: 'Dark',
      icon: <Moon className={iconSizeClasses[size]} />,
      description: 'Easy on the eyes'
    },
    {
      value: 'system',
      label: 'System',
      icon: <Monitor className={iconSizeClasses[size]} />,
      description: `Follows your device (${systemTheme})`
    }
  ];

  const currentIcon = theme === 'system' 
    ? <Monitor className={iconSizeClasses[size]} />
    : actualTheme === 'dark' 
    ? <Moon className={iconSizeClasses[size]} />
    : <Sun className={iconSizeClasses[size]} />;

  return (
    <div className={clsx('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'inline-flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200',
          'bg-white dark:bg-dark-bg-secondary',
          'border border-gray-300 dark:border-dark-border-primary',
          'hover:bg-gray-50 dark:hover:bg-dark-bg-tertiary',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'dark:focus:ring-offset-dark-bg-primary',
          'text-gray-700 dark:text-dark-text-primary'
        )}
        aria-label="Theme options"
        aria-expanded={isOpen}
      >
        {currentIcon}
        <span className="capitalize">{theme}</span>
        <Settings className="w-4 h-4 ml-1" />
      </button>

      {isOpen && (
        <>
          {/* Overlay */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className={clsx(
            'absolute right-0 mt-2 w-64 rounded-lg shadow-large z-20',
            'bg-white dark:bg-dark-bg-secondary',
            'border border-gray-200 dark:border-dark-border-primary',
            'py-2'
          )}>
            {/* Theme Options */}
            <div className="px-3 py-2 border-b border-gray-200 dark:border-dark-border-primary">
              <h3 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                Theme
              </h3>
            </div>
            
            {themeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  setTheme(option.value);
                  setIsOpen(false);
                }}
                className={clsx(
                  'w-full flex items-center gap-3 px-3 py-2 text-left transition-colors',
                  'hover:bg-gray-50 dark:hover:bg-dark-bg-tertiary',
                  theme === option.value && 'bg-primary-50 dark:bg-primary-900/20'
                )}
              >
                <span className={theme === option.value ? 'text-primary-600' : 'text-gray-600 dark:text-dark-text-secondary'}>
                  {option.icon}
                </span>
                <div className="flex-1">
                  <div className={clsx(
                    'font-medium',
                    theme === option.value ? 'text-primary-900 dark:text-primary-100' : 'text-gray-900 dark:text-dark-text-primary'
                  )}>
                    {option.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                    {option.description}
                  </div>
                </div>
                {theme === option.value && (
                  <Check className="w-4 h-4 text-primary-600" />
                )}
              </button>
            ))}

            {/* Accessibility Options */}
            <div className="px-3 py-2 border-t border-gray-200 dark:border-dark-border-primary mt-2">
              <h3 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-2">
                Accessibility
              </h3>
              
              <label className="flex items-center gap-3 py-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={highContrast}
                  onChange={(e) => dispatch(setHighContrast(e.target.checked))}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                    High Contrast
                  </div>
                  <div className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                    Increase color contrast
                  </div>
                </div>
              </label>

              <label className="flex items-center gap-3 py-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={reducedMotion}
                  onChange={(e) => dispatch(setReducedMotion(e.target.checked))}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                    Reduce Motion
                  </div>
                  <div className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                    Minimize animations
                  </div>
                </div>
              </label>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function ThemeToggle({
  variant = 'icon',
  size = 'md',
  showLabel = false,
  className
}: ThemeToggleProps) {
  switch (variant) {
    case 'button':
      return <ButtonToggle size={size} showLabel={showLabel} className={className} />;
    case 'switch':
      return <SwitchToggle size={size} className={className} />;
    case 'dropdown':
      return <DropdownToggle size={size} className={className} />;
    case 'icon':
    default:
      return <IconToggle size={size} className={className} />;
  }
}
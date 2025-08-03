import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setTheme } from '@/store/slices/userPreferencesSlice';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextType {
  // Current theme state
  theme: ThemeMode;
  actualTheme: 'light' | 'dark'; // The actual resolved theme
  
  // Theme actions
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  
  // System detection
  systemTheme: 'light' | 'dark';
  isSystemTheme: boolean;
  
  // Accessibility
  reducedMotion: boolean;
  highContrast: boolean;
  
  // Healthcare-specific
  isDarkMode: boolean;
  colorScheme: 'healthcare-light' | 'healthcare-dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Custom hook to detect system theme preference
function useSystemTheme() {
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? 'dark' : 'light');
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } 
    // Legacy browsers
    else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  return systemTheme;
}

// Custom hook to detect motion preference
function useReducedMotion() {
  const [reducedMotion, setReducedMotion] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  return reducedMotion;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const dispatch = useAppDispatch();
  const userPreferences = useAppSelector(state => state.userPreferences);
  const systemTheme = useSystemTheme();
  const systemReducedMotion = useReducedMotion();

  // Get current theme from Redux store
  const theme = userPreferences.theme;
  const reducedMotion = userPreferences.reducedMotion || systemReducedMotion;
  const highContrast = userPreferences.highContrast;

  // Resolve actual theme based on user preference and system theme
  const actualTheme = theme === 'system' ? systemTheme : theme;
  const isDarkMode = actualTheme === 'dark';
  const isSystemTheme = theme === 'system';
  const colorScheme = isDarkMode ? 'healthcare-dark' : 'healthcare-light';

  // Apply theme to DOM
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    // Add current theme class
    root.classList.add(actualTheme);
    
    // Set data attributes for CSS custom properties
    root.setAttribute('data-theme', actualTheme);
    root.setAttribute('data-color-scheme', colorScheme);
    
    // Apply accessibility preferences
    if (reducedMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }
    
    if (highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', isDarkMode ? '#0f1419' : '#ffffff');
    }

    // Store theme preference in localStorage for SSR compatibility
    try {
      localStorage.setItem('nazmito-theme', theme);
    } catch (error) {
      console.warn('Failed to save theme preference:', error);
    }
  }, [actualTheme, theme, colorScheme, reducedMotion, highContrast, isDarkMode]);

  // Theme change handler
  const handleSetTheme = useCallback((newTheme: ThemeMode) => {
    dispatch(setTheme(newTheme));
  }, [dispatch]);

  // Toggle between light and dark (ignoring system)
  const toggleTheme = useCallback(() => {
    if (theme === 'system') {
      // If currently system, toggle to opposite of system theme
      handleSetTheme(systemTheme === 'dark' ? 'light' : 'dark');
    } else {
      // Toggle between light and dark
      handleSetTheme(theme === 'dark' ? 'light' : 'dark');
    }
  }, [theme, systemTheme, handleSetTheme]);

  // Initialize theme from localStorage on mount
  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem('nazmito-theme') as ThemeMode;
      if (savedTheme && savedTheme !== theme && ['light', 'dark', 'system'].includes(savedTheme)) {
        dispatch(setTheme(savedTheme));
      }
    } catch (error) {
      console.warn('Failed to load theme preference:', error);
    }
  }, [theme, dispatch]);

  const contextValue: ThemeContextType = {
    theme,
    actualTheme,
    setTheme: handleSetTheme,
    toggleTheme,
    systemTheme,
    isSystemTheme,
    reducedMotion,
    highContrast,
    isDarkMode,
    colorScheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Helper hook for components that need to be theme-aware
export function useThemeClasses() {
  const { isDarkMode, actualTheme, reducedMotion, highContrast } = useTheme();
  
  return {
    isDarkMode,
    theme: actualTheme,
    reducedMotion,
    highContrast,
    // Common class utilities
    bg: isDarkMode ? 'bg-dark-bg-primary' : 'bg-gray-50',
    cardBg: isDarkMode ? 'bg-dark-bg-secondary' : 'bg-white',
    textPrimary: isDarkMode ? 'text-dark-text-primary' : 'text-gray-900',
    textSecondary: isDarkMode ? 'text-dark-text-secondary' : 'text-gray-600',
    textTertiary: isDarkMode ? 'text-dark-text-tertiary' : 'text-gray-500',
    border: isDarkMode ? 'border-dark-border-primary' : 'border-gray-200',
    borderSecondary: isDarkMode ? 'border-dark-border-secondary' : 'border-gray-300',
  };
}

// Healthcare-specific theme utilities
export function useHealthcareTheme() {
  const { isDarkMode, actualTheme } = useTheme();
  
  return {
    isDarkMode,
    theme: actualTheme,
    // Healthcare-specific color schemes that work in both light and dark
    primary: isDarkMode ? 'rgb(255 147 85)' : 'rgb(255 107 53)', // Adjusted orange for dark mode
    success: isDarkMode ? 'rgb(72 187 120)' : 'rgb(34 197 94)',
    warning: isDarkMode ? 'rgb(251 191 36)' : 'rgb(245 158 11)',
    error: isDarkMode ? 'rgb(248 113 113)' : 'rgb(239 68 68)',
    // Status colors for healthcare
    approved: isDarkMode ? 'rgb(72 187 120)' : 'rgb(34 197 94)',
    pending: isDarkMode ? 'rgb(251 191 36)' : 'rgb(245 158 11)',
    denied: isDarkMode ? 'rgb(248 113 113)' : 'rgb(239 68 68)',
    processing: isDarkMode ? 'rgb(96 165 250)' : 'rgb(59 130 246)',
  };
}
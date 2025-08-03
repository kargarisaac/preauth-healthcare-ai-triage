# Theme System Documentation

This document describes the comprehensive dark/light theme system implemented for the Nazmito healthcare application.

## Overview

The theme system provides a robust, accessible, and healthcare-appropriate theming solution with the following features:

- **Three theme modes**: Light, Dark, and System (auto-detection)
- **Healthcare-specific color schemes** with proper contrast ratios
- **Accessibility support** including high contrast and reduced motion
- **Persistent preferences** stored in localStorage and Redux
- **Smooth transitions** with customizable durations
- **System theme detection** with automatic updates

## Architecture

### Core Components

1. **ThemeContext** (`src/contexts/ThemeContext.tsx`)
   - Manages theme state and system detection
   - Provides theme utilities and helper hooks
   - Handles localStorage persistence and DOM updates

2. **ThemeToggle** (`src/components/ui/ThemeToggle.tsx`)
   - Multiple toggle variants (icon, button, switch, dropdown)
   - Integrated accessibility controls
   - Size and style customization

3. **Redux Integration** (`src/store/slices/userPreferencesSlice.ts`)
   - Persistent theme preferences
   - Accessibility settings (high contrast, reduced motion)
   - Notification preferences

4. **CSS Variables and Classes** (`src/styles/tailwind.css`)
   - Comprehensive dark mode support
   - Healthcare-appropriate color schemes
   - Smooth transitions and animations

## Usage

### Basic Setup

```tsx
import { ThemeProvider } from '@/contexts/ThemeContext';
import { useTheme } from '@/contexts/ThemeContext';

// Wrap your app with ThemeProvider
function App() {
  return (
    <ThemeProvider>
      <YourAppContent />
    </ThemeProvider>
  );
}

// Use theme in components
function MyComponent() {
  const { theme, actualTheme, toggleTheme } = useTheme();
  
  return (
    <div className="bg-white dark:bg-dark-bg-primary">
      Current theme: {actualTheme}
    </div>
  );
}
```

### Theme Toggle Components

```tsx
import ThemeToggle from '@components/ui/ThemeToggle';

// Icon toggle (minimal)
<ThemeToggle variant="icon" />

// Button with label
<ThemeToggle variant="button" showLabel />

// iOS-style switch
<ThemeToggle variant="switch" />

// Full dropdown with accessibility options
<ThemeToggle variant="dropdown" />
```

### Helper Hooks

```tsx
import { useThemeClasses, useHealthcareTheme } from '@/contexts/ThemeContext';

function MyComponent() {
  const themeClasses = useThemeClasses();
  const healthcareTheme = useHealthcareTheme();
  
  return (
    <div className={themeClasses.cardBg}>
      <h1 className={themeClasses.textPrimary}>Title</h1>
      <p className={themeClasses.textSecondary}>Description</p>
      
      {/* Healthcare-specific colors */}
      <div style={{ color: healthcareTheme.approved }}>
        Approved Status
      </div>
    </div>
  );
}
```

## Color Schemes

### Healthcare Status Colors

The system includes healthcare-appropriate status colors that work in both light and dark modes:

- **Approved**: Green (`#22c55e` / `#48bb78`)
- **Pending**: Orange (`#f59e0b` / `#fbbf24`)
- **Denied**: Red (`#ef4444` / `#f87171`)
- **Processing**: Blue (`#3b82f6` / `#60a5fa`)

### Dark Mode Colors

```css
:root {
  --dark-bg-primary: #0f1419;    /* Main background */
  --dark-bg-secondary: #1a202c;  /* Card backgrounds */
  --dark-bg-tertiary: #2d3748;   /* Hover states */
  --dark-text-primary: #f7fafc;  /* Primary text */
  --dark-text-secondary: #e2e8f0; /* Secondary text */
  --dark-text-tertiary: #a0aec0;  /* Muted text */
  --dark-border-primary: #2d3748; /* Primary borders */
  --dark-border-secondary: #4a5568; /* Secondary borders */
}
```

## Tailwind Configuration

The theme system extends Tailwind CSS with dark mode support:

```js
// tailwind.config.js
export default {
  darkMode: 'class', // Enables manual dark mode control
  theme: {
    extend: {
      colors: {
        'dark-bg-primary': '#0f1419',
        'dark-bg-secondary': '#1a202c',
        // ... other colors
      }
    }
  }
}
```

## Accessibility Features

### High Contrast Mode

```tsx
import { useAppDispatch } from '@/store/hooks';
import { setHighContrast } from '@/store/slices/userPreferencesSlice';

function AccessibilityControls() {
  const dispatch = useAppDispatch();
  
  return (
    <label>
      <input
        type="checkbox"
        onChange={(e) => dispatch(setHighContrast(e.target.checked))}
      />
      High Contrast Mode
    </label>
  );
}
```

### Reduced Motion

```tsx
import { setReducedMotion } from '@/store/slices/userPreferencesSlice';

// Automatically respects prefers-reduced-motion
// Also provides manual control via Redux
```

## System Theme Detection

The system automatically detects and responds to OS theme changes:

```tsx
// Automatic detection in ThemeContext
const systemTheme = useSystemTheme(); // 'light' | 'dark'

// Manual system theme usage
const { theme, systemTheme, isSystemTheme } = useTheme();
if (theme === 'system') {
  // Will use systemTheme value
}
```

## Browser Support

- **Modern browsers**: Full support with `matchMedia` API
- **Legacy browsers**: Graceful fallback to light mode
- **No JavaScript**: CSS-only dark mode via `prefers-color-scheme`

## Performance Considerations

- **CSS-in-JS avoided**: Uses CSS classes for better performance
- **Transition optimization**: Only animates necessary properties
- **Lazy loading**: Theme context only loads when needed
- **Memoization**: Theme calculations are memoized

## Testing

```tsx
// Test theme switching
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@/contexts/ThemeContext';

test('theme toggle switches between light and dark', () => {
  render(
    <ThemeProvider>
      <ThemeToggle variant="button" showLabel />
    </ThemeProvider>
  );
  
  // Test implementation here
});
```

## Migration Guide

### From Context-based Theming

```tsx
// Old approach
const { theme } = useContext(OldThemeContext);

// New approach
const { actualTheme } = useTheme();
```

### Adding Dark Mode to Existing Components

```tsx
// Before
<div className="bg-white text-gray-900">

// After
<div className="bg-white dark:bg-dark-bg-primary text-gray-900 dark:text-dark-text-primary">
```

## Best Practices

1. **Use semantic color classes**: Prefer `textPrimary` over hardcoded colors
2. **Test in both modes**: Always verify components work in light and dark
3. **Respect user preferences**: Don't override system preferences without good reason
4. **Maintain contrast ratios**: Ensure WCAG AA compliance (4.5:1 minimum)
5. **Optimize transitions**: Use `duration-200` for smooth but fast transitions

## Troubleshooting

### Flash of Incorrect Theme (FOIT)

The system includes pre-render theme detection in `index.html` to prevent FOIT:

```html
<script>
  // Theme initialization runs before React
  // Prevents flash of wrong theme
</script>
```

### Theme Not Persisting

Check localStorage permissions and Redux persistence configuration:

```tsx
// Verify Redux persistence
const persistConfig = {
  key: 'nazmito-root',
  storage,
  whitelist: ['userPreferences'], // Must include userPreferences
};
```

### CSS Classes Not Applying

Ensure Tailwind's dark mode is configured correctly:

```js
// tailwind.config.js
export default {
  darkMode: 'class', // Required for manual control
  // ...
}
```

## Future Enhancements

- [ ] Multiple color scheme variants (blue, green, purple)
- [ ] Seasonal themes (Ramadan, National Day)
- [ ] Custom brand color overrides
- [ ] Advanced accessibility features (motion sensitivity)
- [ ] Theme preview before applying
- [ ] Automatic theme scheduling (light during day, dark at night)

## Related Files

- `src/contexts/ThemeContext.tsx` - Main theme context
- `src/components/ui/ThemeToggle.tsx` - Toggle components
- `src/store/slices/userPreferencesSlice.ts` - Redux state
- `src/styles/tailwind.css` - CSS classes and variables
- `tailwind.config.js` - Tailwind configuration
- `index.html` - Pre-render theme detection
- `src/components/examples/ThemeShowcase.tsx` - Demo component
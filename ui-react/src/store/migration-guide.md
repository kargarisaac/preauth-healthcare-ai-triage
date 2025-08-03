# Redux Toolkit Migration Guide

This guide helps you migrate from React Context to Redux Toolkit state management.

## Overview

The application has been migrated from React Context pattern to Redux Toolkit for better scalability, performance, and developer experience.

## Key Changes

### 1. State Management Architecture

**Before (Context):**
```tsx
import { useApp } from '@contexts/AppContext';
import { useToast } from '@contexts/ToastContext';
import { useProcessing } from '@contexts/ProcessingContext';

function MyComponent() {
  const { requests, setLoading } = useApp();
  const { showToast } = useToast();
  const { processFile } = useProcessing();
  // ...
}
```

**After (Redux):**
```tsx
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { processFileAsync } from '@/store/slices/fileProcessingSlice';
import { showToast } from '@/store/slices/notificationSlice';

function MyComponent() {
  const dispatch = useAppDispatch();
  const requests = useAppSelector(state => state.fileProcessing.processingHistory);
  const isLoading = useAppSelector(state => state.fileProcessing.isProcessing);
  
  const handleProcessFile = async (file, format) => {
    await dispatch(processFileAsync({ file, format })).unwrap();
    dispatch(showToast({ type: 'success', title: 'Done!', message: 'File processed' }));
  };
}
```

### 2. Legacy Hook Compatibility

For gradual migration, legacy hooks are still available:

```tsx
import { useApp, useToast } from '@/store/ReduxProvider';
import { useProcessing } from '@/hooks/useProcessing';

// These work exactly like before but are now powered by Redux
function LegacyComponent() {
  const { requests, setLoading } = useApp();
  const { showToast } = useToast();
  const { processFile } = useProcessing();
  // No changes needed in component logic
}
```

## Migration Steps

### Step 1: Update App.tsx

Replace context providers with Redux provider:

```tsx
// Old
<AppProvider>
  <ToastProvider>
    <ProcessingProvider>
      {children}
    </ProcessingProvider>
  </ToastProvider>
</AppProvider>

// New
<ReduxProvider>
  {children}
</ReduxProvider>
```

### Step 2: Update Component Imports

**File Processing:**
```tsx
// Old
import { useProcessing } from '@contexts/ProcessingContext';

// New - Redux approach
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { processFileAsync, selectCurrentFile } from '@/store/slices/fileProcessingSlice';

// Or - Legacy compatibility
import { useProcessing } from '@/hooks/useProcessing';
```

**Notifications:**
```tsx
// Old
import { useToast } from '@contexts/ToastContext';

// New - Redux approach
import { useAppDispatch } from '@/store/hooks';
import { showToast } from '@/store/slices/notificationSlice';

// Or - Legacy compatibility
import { useToast } from '@/store/ReduxProvider';
```

### Step 3: Update State Access Patterns

**Reading State:**
```tsx
// Old
const { requests, loading, error } = useApp();

// New
const requests = useAppSelector(state => state.fileProcessing.processingHistory);
const loading = useAppSelector(state => state.fileProcessing.isProcessing);
const error = useAppSelector(state => state.fileProcessing.error);

// Or use memoized selectors for performance
const processingState = useAppSelector(selectProcessingState);
```

**Updating State:**
```tsx
// Old
setLoading(true);
setError('Something went wrong');

// New
dispatch(setProcessingStatus('processing'));
dispatch(setError('Something went wrong'));
```

### Step 4: Async Operations

**File Processing:**
```tsx
// Old
const processFile = async (format) => {
  setIsProcessing(true);
  try {
    const result = await api.processFile(file, format);
    setProcessingResults(result);
  } catch (error) {
    setError(error.message);
  } finally {
    setIsProcessing(false);
  }
};

// New
const handleProcessFile = async (format) => {
  try {
    await dispatch(processFileAsync({ file, format })).unwrap();
    // Success notification handled automatically by middleware
  } catch (error) {
    // Error notification handled automatically by middleware
  }
};
```

## New Features Available

### 1. Optimistic Updates

```tsx
// Add optimistic request before API call
dispatch(addOptimisticRequest(newRequest));

// Remove on success/failure
dispatch(removeOptimisticRequest(requestId));
```

### 2. Real-time Validation

```tsx
const handleValidateFile = async (functionIds) => {
  await dispatch(validateWithLLMAsync({
    fileId: fhirBundle.id,
    functionIds,
    realTimeUpdates: true, // WebSocket updates
  }));
};
```

### 3. Advanced Selectors

```tsx
// Get derived data with memoization
const validationInsights = useAppSelector(selectValidationInsights);
const dashboardMetrics = useAppSelector(selectDashboardMetrics);
const recentActivity = useAppSelector(selectRecentActivity);
```

### 4. User Preferences

```tsx
const dispatch = useAppDispatch();
const theme = useAppSelector(state => state.userPreferences.theme);

// Update preferences
dispatch(setTheme('dark'));
dispatch(setDefaultFileFormat('csv'));
dispatch(setAutoValidation(true));
```

### 5. Enhanced Notifications

```tsx
// Progress notifications
dispatch(showProgressNotification({
  id: 'validation-123',
  title: 'Running validation...',
  progress: 50,
}));

// System notifications
dispatch(showSystemNotification({
  type: 'maintenance',
  title: 'Scheduled Maintenance',
  message: 'System will be down for 30 minutes',
  priority: 'high',
}));
```

## Performance Benefits

### 1. Selective Re-renders

```tsx
// Only re-renders when currentFile changes
const currentFile = useAppSelector(selectCurrentFile);

// Re-renders on any processingState change
const processingState = useAppSelector(selectProcessingState);
```

### 2. Memoized Selectors

```tsx
// Expensive computation only runs when dependencies change
const complexData = useAppSelector(selectValidationInsights);
```

### 3. Middleware Benefits

- Automatic error handling
- Progress tracking
- Cache management
- Offline support
- Performance monitoring

## Debugging

### Redux DevTools

Install Redux DevTools extension for:
- Time-travel debugging
- State inspection
- Action replay
- Performance monitoring

### Debug Mode

Enable debug mode in user preferences:
```tsx
dispatch(setDebugMode(true));
```

This enables:
- Console logging of operations
- Performance notifications
- Extended error information

## Best Practices

### 1. Use Typed Hooks

```tsx
// Always use typed versions
import { useAppSelector, useAppDispatch } from '@/store/hooks';

// Not the generic versions
import { useSelector, useDispatch } from 'react-redux';
```

### 2. Prefer Selectors

```tsx
// Good - uses memoized selector
const processingState = useAppSelector(selectProcessingState);

// Avoid - creates new object on every render
const processingState = useAppSelector(state => ({
  isProcessing: state.fileProcessing.isProcessing,
  status: state.fileProcessing.processingStatus,
  // ...
}));
```

### 3. Use Async Thunks

```tsx
// Good - uses async thunk with error handling
dispatch(processFileAsync({ file, format }));

// Avoid - manual API calls in components
fetch('/api/process', { ... });
```

### 4. Leverage Middleware

Let middleware handle:
- Error notifications
- Progress tracking  
- Cache invalidation
- Offline detection

## Rollback Plan

If issues arise, you can temporarily switch back:

1. Restore original context providers in App.tsx
2. Use legacy hooks remain functional
3. Gradually fix Redux-specific issues
4. Re-enable Redux provider

The migration is designed to be gradual and reversible.

## Support

For migration issues:
1. Check browser console for Redux DevTools
2. Enable debug mode for detailed logging
3. Use legacy compatibility hooks as fallback
4. Review this guide for common patterns
# Redux Toolkit State Management

A comprehensive Redux Toolkit implementation for the Healthcare AI Pre-authorization Platform.

## Overview

This implementation migrates the application from React Context API to Redux Toolkit, providing:

- **Scalable State Management**: Centralized state with predictable updates
- **Performance Optimization**: Memoized selectors and minimal re-renders  
- **Developer Experience**: Time-travel debugging, hot reloading, type safety
- **Real-time Features**: WebSocket integration for live updates
- **Persistence**: User preferences and critical state persistence
- **Middleware**: Automatic error handling, progress tracking, caching

## Architecture

### Store Structure

```
store/
├── index.ts                 # Store configuration with persistence
├── hooks.ts                 # Typed hooks and memoized selectors
├── ReduxProvider.tsx        # Provider with middleware components
├── middleware/
│   └── apiMiddleware.ts     # API call handling, caching, offline support
└── slices/
    ├── fileProcessingSlice.ts    # File upload, processing, FHIR conversion
    ├── validationSlice.ts        # LLM validation, real-time progress
    ├── userPreferencesSlice.ts   # Settings, themes, defaults
    └── notificationSlice.ts      # Toast messages, system alerts
```

### Key Features

#### 1. File Processing (`fileProcessingSlice`)
- **Upload Management**: Progress tracking, validation, error handling
- **FHIR Conversion**: XML/CSV to FHIR Bundle processing
- **History Tracking**: Recent processing requests with caching
- **Optimistic Updates**: Immediate UI feedback before API completion

```typescript
// Usage example
const dispatch = useAppDispatch();
const processingState = useAppSelector(selectProcessingState);

await dispatch(processFileAsync({ file, format: 'eclaim' }));
```

#### 2. LLM Validation (`validationSlice`)
- **Real-time Updates**: WebSocket-powered progress tracking
- **Function Management**: Configurable validation functions
- **Quality Scoring**: Automatic quality calculation from findings
- **Insights Generation**: Categorized findings and performance metrics

```typescript
// Start validation with real-time updates
await dispatch(validateWithLLMAsync({
  fileId: bundle.id,
  functionIds: selectedFunctions,
  realTimeUpdates: true
}));
```

#### 3. User Preferences (`userPreferencesSlice`)
- **UI Settings**: Theme, language, layout preferences
- **Processing Defaults**: Auto-validation, file format defaults
- **Performance Options**: Virtualization, cache settings
- **Accessibility**: Reduced motion, high contrast, font size

```typescript
// Update preferences
dispatch(setTheme('dark'));
dispatch(setAutoValidation(true));
dispatch(setDefaultFileFormat('csv'));
```

#### 4. Notifications (`notificationSlice`)
- **Toast Management**: Success, error, warning, info notifications
- **Progress Tracking**: Long-running operation progress
- **System Alerts**: Maintenance, updates, announcements
- **History**: Notification history with read/unread tracking

```typescript
// Show notification
dispatch(showToast({
  type: 'success',
  title: 'Processing Complete',
  message: 'File converted to FHIR successfully',
  category: 'processing'
}));
```

## Usage Patterns

### 1. Component Integration

```tsx
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { 
  processFileAsync,
  selectCurrentFile,
  selectProcessingState 
} from '@/store/slices/fileProcessingSlice';

function FileProcessor() {
  const dispatch = useAppDispatch();
  const currentFile = useAppSelector(selectCurrentFile);
  const { isProcessing, error } = useAppSelector(selectProcessingState);

  const handleProcess = async () => {
    if (currentFile) {
      await dispatch(processFileAsync({ 
        file: currentFile, 
        format: 'eclaim' 
      }));
    }
  };

  return (
    <div>
      {/* UI implementation */}
    </div>
  );
}
```

### 2. Async Operations

All async operations use Redux Toolkit's `createAsyncThunk`:

```typescript
// Automatically handles loading, success, and error states
export const processFileAsync = createAsyncThunk(
  'fileProcessing/processFile',
  async (params: { file: File; format: string }, { rejectWithValue }) => {
    try {
      // API call implementation
      const result = await apiService.processFile(params);
      return result;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);
```

### 3. Memoized Selectors

Performance-optimized selectors prevent unnecessary re-renders:

```typescript
// Only recalculates when validation data changes
export const selectValidationInsights = createSelector(
  (state: RootState) => state.validation.validationResults,
  (state: RootState) => state.validation.summary,
  (results, summary) => {
    // Expensive computation here
    return computeInsights(results, summary);
  }
);
```

## Migration from Context API

### Gradual Migration Strategy

The implementation provides backward compatibility:

```tsx
// Legacy Context usage (still works)
import { useApp, useToast } from '@/store/ReduxProvider';
import { useProcessing } from '@/hooks/useProcessing';

// Modern Redux usage
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { processFileAsync } from '@/store/slices/fileProcessingSlice';
```

### Migration Steps

1. **Update App.tsx**: Replace context providers with `ReduxProvider`
2. **Component Migration**: Gradually update components to use Redux hooks
3. **State Access**: Use typed selectors instead of context values
4. **Actions**: Replace context methods with Redux actions
5. **Testing**: Update tests to use Redux store

See [migration-guide.md](./migration-guide.md) for detailed instructions.

## Performance Optimizations

### 1. Selective Re-renders
```tsx
// Only re-renders when specific state changes
const currentFile = useAppSelector(selectCurrentFile);
const isProcessing = useAppSelector(state => state.fileProcessing.isProcessing);
```

### 2. Memoized Selectors
```tsx
// Expensive computations are cached
const validationInsights = useAppSelector(selectValidationInsights);
```

### 3. Middleware Benefits
- Automatic progress tracking
- Error notification handling
- Cache management
- Offline detection

### 4. Bundle Optimization
```typescript
// Code splitting for large validation functions
const heavyValidation = lazy(() => import('./heavyValidationFunctions'));
```

## Real-time Features

### WebSocket Integration

```typescript
// Automatic WebSocket connection for validation progress
export const validateWithLLMAsync = createAsyncThunk(
  'validation/validateWithLLM',
  async (params, { dispatch }) => {
    // Start validation
    const result = await api.startValidation(params);
    
    // Set up WebSocket for real-time updates
    if (params.realTimeUpdates) {
      dispatch(setupWebSocketConnection(result.validationId));
    }
    
    return result;
  }
);
```

### Progress Tracking

```tsx
// Real-time progress updates
const validationProgress = useAppSelector(selectValidationProgress);

return (
  <div>
    {validationProgress.map(progress => (
      <ProgressBar
        key={progress.functionId}
        label={progress.currentStep}
        value={progress.progress}
        estimatedTime={progress.estimatedRemaining}
      />
    ))}
  </div>
);
```

## Testing

### Store Testing
```tsx
import { configureStore } from '@reduxjs/toolkit';
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';

const mockStore = configureStore({
  reducer: {
    fileProcessing: fileProcessingSlice.reducer,
    // other reducers
  },
  preloadedState: {
    fileProcessing: {
      currentFile: mockFile,
      isProcessing: false,
      // other state
    }
  }
});

const ComponentWithRedux = ({ children }) => (
  <Provider store={mockStore}>
    {children}
  </Provider>
);
```

### Async Thunk Testing
```tsx
import { processFileAsync } from '@/store/slices/fileProcessingSlice';

test('processes file successfully', async () => {
  const mockFile = new File([''], 'test.xml');
  const action = processFileAsync({ file: mockFile, format: 'eclaim' });
  
  const result = await action(dispatch, getState, undefined);
  
  expect(result.type).toBe('fileProcessing/processFile/fulfilled');
});
```

## Debugging

### Redux DevTools
Install Redux DevTools browser extension for:
- State inspection
- Action history
- Time-travel debugging
- Performance monitoring

### Debug Mode
```tsx
// Enable debug mode in user preferences
dispatch(setDebugMode(true));

// Provides:
// - Console logging of operations
// - Performance notifications
// - Extended error information
```

## Deployment Considerations

### Environment Variables
```env
# Development
VITE_REDUX_DEVTOOLS=true
VITE_DEBUG_MODE=true

# Production
VITE_REDUX_DEVTOOLS=false
VITE_DEBUG_MODE=false
```

### Build Optimization
```typescript
// Production store configuration
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Configure for production
        ignoredActions: [PERSIST_ACTIONS],
      },
    }).concat(apiMiddleware.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});
```

## Future Enhancements

### Planned Features
1. **RTK Query Integration**: Replace manual API calls with RTK Query
2. **Offline-First**: Enhanced offline capabilities with sync
3. **State Hydration**: Improved persistence and rehydration
4. **Performance Monitoring**: Built-in performance metrics
5. **A/B Testing**: Feature flag management

### Extension Points
- Custom middleware for domain-specific logic
- Additional slices for new features
- Enhanced selectors for complex computations
- Plugin architecture for validation functions

## Support and Resources

- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [Migration Guide](./migration-guide.md)
- [Example Component](../components/examples/ReduxExample.tsx)
- [Performance Best Practices](https://redux.js.org/style-guide/style-guide)

For questions or issues, enable debug mode and check browser console for detailed logging.
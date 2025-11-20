import React, { useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { 
  processFileAsync,
  selectCurrentFile,
  selectProcessingState,
  setCurrentFile,
  resetProcessing,
} from '../../store/slices/fileProcessingSlice';
import {
  validateWithLLMAsync,
  selectValidationState,
  selectValidationProgress,
  setSelectedFunctions,
} from '../../store/slices/validationSlice';
import { showToast } from '../../store/slices/notificationSlice';
import { setTheme, setAutoValidation } from '../../store/slices/userPreferencesSlice';
import Button from '../ui/Button';
import Card from '../ui/Card';

/**
 * Example component demonstrating Redux Toolkit usage
 * This shows how to use the new state management system
 */
export function ReduxExample() {
  const dispatch = useAppDispatch();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Accessing state with typed selectors
  const currentFile = useAppSelector(selectCurrentFile);
  const processingState = useAppSelector(selectProcessingState);
  const validationState = useAppSelector(selectValidationState);
  const validationProgress = useAppSelector(selectValidationProgress);
  
  // Direct state access (less preferred, but sometimes needed)
  const theme = useAppSelector(state => state.userPreferences.theme);
  const autoValidation = useAppSelector(state => state.userPreferences.autoValidation);
  const toasts = useAppSelector(state => state.notifications.toasts);

  // Event handlers using Redux actions
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Create UploadedFile object for Redux
      const uploadedFile = {
        ...file,
        id: Date.now().toString(),
        status: 'idle' as const,
        progress: 0,
      };
      
      dispatch(setCurrentFile(uploadedFile));
    }
  };

  const handleProcessFile = async () => {
    if (!selectedFile) {
      dispatch(showToast({
        type: 'error',
        title: 'No File Selected',
        message: 'Please select a file to process.',
        category: 'user',
      }));
      return;
    }

    try {
      // Determine format (simplified logic)
      const format = selectedFile.name.endsWith('.csv') ? 'csv' : 'eclaim';
      
      // Process file using async thunk
      await dispatch(processFileAsync({ 
        file: selectedFile, 
        format 
      })).unwrap();

      // Show success notification
      dispatch(showToast({
        type: 'success',
        title: 'Processing Complete',
        message: 'File has been successfully processed.',
        category: 'processing',
      }));

    } catch (error) {
      // Error handling is automatic via middleware, but we can add custom logic
      console.error('Processing failed:', error);
    }
  };

  const handleValidateFile = async () => {
    if (!currentFile) {
      dispatch(showToast({
        type: 'warning',
        title: 'No Processed File',
        message: 'Please process a file first before validation.',
        category: 'validation',
      }));
      return;
    }

    try {
      // Select validation functions (example)
      const sampleFunctions = ['clinical-validation', 'administrative-check'];
      dispatch(setSelectedFunctions(sampleFunctions));

      // Start LLM validation
      await dispatch(validateWithLLMAsync({
        fileId: currentFile.id,
        functionIds: sampleFunctions,
        realTimeUpdates: true,
      })).unwrap();

    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    dispatch(setTheme(newTheme));
  };

  const handleAutoValidationToggle = () => {
    dispatch(setAutoValidation(!autoValidation));
  };

  const handleReset = () => {
    dispatch(resetProcessing());
    setSelectedFile(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card title="Redux Toolkit Example" className="p-6">
        <p className="text-gray-600 mb-6">
          This component demonstrates how to use Redux Toolkit for state management
          in the Healthcare AI Platform application.
        </p>

        {/* File Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File
            </label>
            <input
              type="file"
              accept=".xml,.csv"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          {currentFile && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                Selected: {currentFile.name} ({Math.round(currentFile.size / 1024)} KB)
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3 mt-6">
          <Button
            onClick={handleProcessFile}
            disabled={!selectedFile || processingState.isProcessing}
            loading={processingState.isProcessing}
          >
            Process File
          </Button>

          <Button
            onClick={handleValidateFile}
            disabled={!currentFile || validationState.isValidating}
            loading={validationState.isValidating}
            variant="secondary"
          >
            Validate with LLM
          </Button>

          <Button
            onClick={handleReset}
            variant="tertiary"
          >
            Reset
          </Button>
        </div>

        {/* Processing Status */}
        {processingState.isProcessing && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
            <p className="text-sm text-yellow-800">
              Processing... Status: {processingState.status}
            </p>
            {processingState.progress > 0 && (
              <div className="w-full bg-yellow-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${processingState.progress}%` }}
                />
              </div>
            )}
          </div>
        )}

        {/* Validation Progress */}
        {validationProgress.length > 0 && (
          <div className="mt-4 p-3 bg-purple-50 rounded-lg">
            <p className="text-sm text-purple-800 mb-2">Validation Progress:</p>
            {validationProgress.map(progress => (
              <div key={progress.functionId} className="mb-2">
                <div className="flex justify-between text-xs text-purple-700">
                  <span>{progress.currentStep}</span>
                  <span>{progress.progress}%</span>
                </div>
                <div className="w-full bg-purple-200 rounded-full h-1">
                  <div 
                    className="bg-purple-600 h-1 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {validationState.summary && (
          <div className="mt-4 p-3 bg-green-50 rounded-lg">
            <p className="text-sm text-green-800">
              Validation Complete! Quality Score: {validationState.qualityScore}/100
            </p>
            <p className="text-xs text-green-600 mt-1">
              {validationState.summary.totalFindings} findings across {validationState.summary.totalFunctions} functions
            </p>
          </div>
        )}

        {/* Error Display */}
        {(processingState.error || validationState.error) && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-800">
              Error: {processingState.error || validationState.error}
            </p>
          </div>
        )}
      </Card>

      {/* Settings Example */}
      <Card title="User Preferences" className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Theme</span>
            <Button
              onClick={handleThemeToggle}
              variant="secondary"
              size="sm"
            >
              {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Auto Validation</span>
            <Button
              onClick={handleAutoValidationToggle}
              variant={autoValidation ? 'primary' : 'secondary'}
              size="sm"
            >
              {autoValidation ? 'Enabled' : 'Disabled'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Active Toasts */}
      {toasts.length > 0 && (
        <Card title="Active Notifications" className="p-6">
          <div className="space-y-2">
            {toasts.map(toast => (
              <div 
                key={toast.id}
                className={`p-2 rounded text-sm ${
                  toast.type === 'success' ? 'bg-green-100 text-green-800' :
                  toast.type === 'error' ? 'bg-red-100 text-red-800' :
                  toast.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-blue-100 text-blue-800'
                }`}
              >
                <strong>{toast.title}</strong>: {toast.message}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Redux DevTools Tip */}
      <Card className="p-4 bg-gray-50">
        <p className="text-sm text-gray-600">
          💡 <strong>Tip:</strong> Install the Redux DevTools browser extension to inspect 
          state changes, time-travel debug, and monitor performance in real-time.
        </p>
      </Card>
    </div>
  );
}

export default ReduxExample;
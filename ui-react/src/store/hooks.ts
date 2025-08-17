import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import { createSelector } from '@reduxjs/toolkit';
import type { RootState, AppDispatch } from './index';

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Memoized selectors for performance
export const selectCurrentFile = createSelector(
  (state: RootState) => state.fileProcessing.currentFile,
  (currentFile) => currentFile
);

export const selectProcessingState = createSelector(
  (state: RootState) => state.fileProcessing,
  (fileProcessing) => ({
    isProcessing: fileProcessing.isProcessing,
    status: fileProcessing.processingStatus,
    progress: fileProcessing.processingProgress,
    error: fileProcessing.error,
  })
);

export const selectValidationState = createSelector(
  (state: RootState) => state.validation,
  (validation) => ({
    isValidating: validation.isValidating,
    results: validation.validationResults,
    summary: validation.summary,
    qualityScore: validation.qualityScore,
    error: validation.error,
  })
);

export const selectValidationProgress = createSelector(
  (state: RootState) => state.validation.validationProgress,
  (progress) => Object.values(progress)
);

export const selectActiveToasts = createSelector(
  (state: RootState) => state.notifications.toasts,
  (toasts) => toasts
);

export const selectNotificationHistory = createSelector(
  (state: RootState) => state.notifications.history,
  (state: RootState) => state.notifications.unreadCount,
  (history, unreadCount) => ({
    history,
    unreadCount,
    hasUnread: unreadCount > 0,
  })
);

export const selectUserPreferences = createSelector(
  (state: RootState) => state.userPreferences,
  (preferences) => preferences
);

export const selectThemeSettings = createSelector(
  (state: RootState) => state.userPreferences,
  (preferences) => ({
    theme: preferences.theme,
    language: preferences.language,
    direction: preferences.direction,
    reducedMotion: preferences.reducedMotion,
    highContrast: preferences.highContrast,
    fontSize: preferences.fontSize,
  })
);

export const selectDashboardSettings = createSelector(
  (state: RootState) => state.userPreferences,
  (preferences) => ({
    layout: preferences.dashboardLayout,
    sidebarCollapsed: preferences.sidebarCollapsed,
    showMinimap: preferences.showMinimap,
    itemsPerPage: preferences.itemsPerPage,
    enableVirtualization: preferences.enableVirtualization,
  })
);

export const selectValidationSettings = createSelector(
  (state: RootState) => state.userPreferences,
  (preferences) => ({
    autoValidation: preferences.autoValidation,
    realTimeUpdates: preferences.realTimeUpdates,
    defaultFunctions: preferences.defaultValidationFunctions,
    timeout: preferences.validationTimeout,
    maxConcurrent: preferences.maxConcurrentValidations,
  })
);

export const selectNotificationSettings = createSelector(
  (state: RootState) => state.userPreferences,
  (state: RootState) => state.notifications.settings,
  (userPrefs, notificationSettings) => ({
    enabled: userPrefs.enableNotifications && notificationSettings.enableNotifications,
    sound: userPrefs.enableSoundNotifications && notificationSettings.enableSound,
    desktop: notificationSettings.enableDesktop,
    duration: userPrefs.notificationDuration * 1000, // Convert to milliseconds
    showSuccess: userPrefs.showSuccessNotifications,
    showWarning: userPrefs.showWarningNotifications,
    showError: userPrefs.showErrorNotifications,
  })
);

export const selectProcessingHistory = createSelector(
  (state: RootState) => state.fileProcessing.processingHistory,
  (state: RootState) => state.fileProcessing.optimisticRequests,
  (history, optimistic) => [...optimistic, ...history]
);

export const selectSystemNotifications = createSelector(
  (state: RootState) => state.notifications.systemNotifications,
  (notifications) => Array.isArray(notifications) ? notifications.filter(n => !n.dismissed && (!n.endDate || n.endDate > new Date())) : []
);

export const selectProgressNotifications = createSelector(
  (state: RootState) => state.notifications.progressNotifications,
  (notifications) => Object.values(notifications).filter(n => n.status === 'running')
);

// Complex selectors for derived data
export const selectValidationInsights = createSelector(
  (state: RootState) => state.validation.validationResults,
  (state: RootState) => state.validation.summary,
  (results, summary) => {
    if (!summary) return null;
    
    const allResults = Object.values(results);
    const findingsByCategory: Record<string, any[]> = {};
    
    allResults.forEach(result => {
      if (result.findings) {
        result.findings.forEach(finding => {
          if (!findingsByCategory[finding.category]) {
            findingsByCategory[finding.category] = [];
          }
          findingsByCategory[finding.category].push(finding);
        });
      }
    });
    
    const avgConfidence = allResults.length > 0 
      ? allResults.reduce((sum, r) => sum + (r.confidence || 0), 0) / allResults.length
      : 0;
    
    const executionTime = allResults.reduce((sum, r) => sum + (r.executionTime || 0), 0);
    
    return {
      categoryBreakdown: findingsByCategory,
      averageConfidence: avgConfidence,
      executionTime,
      successRate: summary.totalFunctions > 0 
        ? (summary.completedFunctions / summary.totalFunctions) * 100
        : 0,
    };
  }
);

export const selectDashboardMetrics = createSelector(
  (state: RootState) => state.fileProcessing.processingHistory,
  (state: RootState) => state.validation.validationHistory,
  (processingHistory, validationHistory) => {
    const last24Hours = new Date(Date.now() - 24 * 60 * 60 * 1000);
    
    const recentProcessing = processingHistory.filter(
      req => new Date(req.date) > last24Hours
    );
    
    const recentValidations = validationHistory.filter(
      val => new Date(val.timestamp) > last24Hours
    );
    
    return {
      processingCount: recentProcessing.length,
      validationCount: recentValidations.length,
      approvedCount: recentProcessing.filter(r => r.status === 'Approved').length,
      pendingCount: recentProcessing.filter(r => r.status === 'Pending').length,
      deniedCount: recentProcessing.filter(r => r.status === 'Denied').length,
      avgQualityScore: recentValidations.length > 0
        ? recentValidations.reduce((sum, v) => sum + (v.summary.averageConfidence || 0), 0) / recentValidations.length
        : 0,
    };
  }
);

export const selectFormattedFileSize = createSelector(
  (state: RootState) => state.fileProcessing.currentFile,
  (currentFile) => {
    if (!currentFile) return null;
    
    const bytes = currentFile.size;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
    if (bytes === 0) return '0 Bytes';
    
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
);

export const selectRecentActivity = createSelector(
  (state: RootState) => state.fileProcessing.processingHistory,
  (state: RootState) => state.validation.validationHistory,
  (state: RootState) => state.notifications.history,
  (processing, validation, notifications) => {
    const activities = [
      ...processing.map(p => ({
        id: p.id,
        type: 'processing' as const,
        title: `Processed ${p.format} file`,
        description: `${p.service} for ${p.memberName}`,
        timestamp: new Date(p.date),
        status: p.status.toLowerCase(),
      })),
      ...validation.map(v => ({
        id: v.id,
        type: 'validation' as const,
        title: 'LLM Validation Completed',
        description: `${v.summary.totalFindings} findings across ${v.summary.totalFunctions} functions`,
        timestamp: new Date(v.timestamp),
        status: v.summary.overallStatus,
      })),
      ...notifications.slice(0, 10).map(n => ({
        id: n.id,
        type: 'notification' as const,
        title: n.title,
        description: n.message,
        timestamp: new Date(n.timestamp),
        status: n.type,
      })),
    ];
    
    return activities
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 20);
  }
);

// Performance-optimized selectors
export const selectIsLoading = createSelector(
  (state: RootState) => state.fileProcessing.isProcessing,
  (state: RootState) => state.validation.isValidating,
  (isProcessing, isValidating) => isProcessing || isValidating
);

export const selectHasErrors = createSelector(
  (state: RootState) => state.fileProcessing.error,
  (state: RootState) => state.validation.error,
  (processingError, validationError) => !!(processingError || validationError)
);

export const selectErrorMessages = createSelector(
  (state: RootState) => state.fileProcessing.error,
  (state: RootState) => state.validation.error,
  (processingError, validationError) => {
    const errors = [];
    if (processingError) errors.push({ type: 'processing', message: processingError });
    if (validationError) errors.push({ type: 'validation', message: validationError });
    return errors;
  }
);
import React, { Suspense, lazy, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ReduxProvider } from './store/ReduxProvider';
import { PerformanceProvider } from '@contexts/PerformanceContext';
import { ThemeProvider } from '@contexts/ThemeContext';
import { AppProvider } from '@contexts/AppContext';
import { ToastProvider } from '@contexts/ToastContext';
import { ProcessingProvider } from '@contexts/ProcessingContext';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import { DashboardSkeleton } from '@components/ui/SkeletonLoader';
import { PWAInstallPrompt } from '@components/ui/PWAInstallPrompt';
import { ErrorBoundary } from '@components/ui/ErrorBoundary';

// Lazy load pages with better loading states
const LandingPage = lazy(() =>
  import('@pages/Landing/LandingPage').then(module => ({
    default: module.default
  }))
);

const DashboardPage = lazy(() =>
  Promise.all([
    import('@pages/Dashboard/DashboardPage'),
    new Promise(resolve => setTimeout(resolve, 200)) // Minimum loading time
  ]).then(([module]) => ({ default: module.default }))
);

const AnalyticsShowcase = lazy(() =>
  import('@pages/Analytics/AnalyticsShowcase')
);

// Enhanced loading component with adaptive behavior
const AdaptiveLoadingSpinner: React.FC<{ route?: string }> = React.memo(({ route }) => {
  if (route === '/dashboard') {
    return <DashboardSkeleton />;
  }
  return <LoadingSpinner />;
});

AdaptiveLoadingSpinner.displayName = 'AdaptiveLoadingSpinner';

// Main App component with performance optimizations
function App() {
  useEffect(() => {
    // Prefetch critical routes on idle
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        // Prefetch dashboard page if on landing page
        if (window.location.pathname === '/') {
          import('@pages/Dashboard/DashboardPage');
        }
      });
    }
  }, []);

  return (
    <ErrorBoundary>
      <ReduxProvider>
        <ThemeProvider>
          <AppProvider>
            <ToastProvider>
              <ProcessingProvider>
                <PerformanceProvider>
            <div className="min-h-screen bg-gray-50 dark:bg-dark-bg-primary transition-colors duration-200">
              <Suspense fallback={<AdaptiveLoadingSpinner />}>
                <Routes>
                <Route
                  path="/"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <LandingPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/dashboard/*"
                  element={
                    <Suspense fallback={<AdaptiveLoadingSpinner route="/dashboard" />}>
                      <DashboardPage />
                    </Suspense>
                  }
                />
                <Route
                  path="/analytics"
                  element={
                    <Suspense fallback={<LoadingSpinner />}>
                      <AnalyticsShowcase />
                    </Suspense>
                  }
                />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>

              {/* PWA Install Prompt */}
              <PWAInstallPrompt
                variant="banner"
                position="bottom"
                autoShow={true}
              />
            </div>
                </PerformanceProvider>
              </ProcessingProvider>
            </ToastProvider>
          </AppProvider>
        </ThemeProvider>
      </ReduxProvider>
    </ErrorBoundary>
  );
}

export default React.memo(App);

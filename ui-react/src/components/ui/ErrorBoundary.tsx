import React, { Component, ReactNode } from 'react';
import { trackError, trackAnalytics } from '@utils/performance';
import { AlertTriangle, RefreshCw, Home, HelpCircle } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  name?: string;
  level?: 'page' | 'component' | 'critical';
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  errorId?: string;
}

// Healthcare-specific error messages
const getHealthcareErrorMessage = (error?: Error) => {
  if (!error) return 'An unexpected error occurred';
  
  const message = error.message.toLowerCase();
  
  if (message.includes('network') || message.includes('fetch')) {
    return 'Network connection issue. Please check your internet connection and try again.';
  }
  
  if (message.includes('permission') || message.includes('unauthorized')) {
    return 'Access denied. Please ensure you have the required permissions to access this healthcare data.';
  }
  
  if (message.includes('validation') || message.includes('invalid')) {
    return 'Data validation error. Please check your input and try again.';
  }
  
  if (message.includes('timeout')) {
    return 'Request timeout. The healthcare system may be experiencing high load. Please try again.';
  }
  
  return 'An error occurred while processing your healthcare data. Our team has been notified.';
};

const getRecoveryActions = (level: string) => {
  switch (level) {
    case 'critical':
      return [
        { label: 'Contact Support', action: 'support', icon: HelpCircle },
        { label: 'Go to Home', action: 'home', icon: Home },
      ];
    case 'page':
      return [
        { label: 'Reload Page', action: 'reload', icon: RefreshCw },
        { label: 'Go to Dashboard', action: 'dashboard', icon: Home },
      ];
    default:
      return [
        { label: 'Try Again', action: 'retry', icon: RefreshCw },
      ];
  }
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return { 
      hasError: true, 
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const { name = 'Unknown', level = 'component', onError } = this.props;
    
    // Generate unique error ID for tracking
    const errorId = this.state.errorId || `error_${Date.now()}`;
    
    // Enhanced error logging with healthcare context
    const errorContext = {
      componentName: name,
      level,
      errorId,
      retryCount: this.retryCount,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      componentStack: errorInfo.componentStack,
      errorBoundary: 'ErrorBoundary',
      healthcareContext: this.getHealthcareContext(),
    };

    console.error('ErrorBoundary caught an error:', {
      error,
      errorInfo,
      context: errorContext,
    });

    // Track error with performance monitoring
    trackError(error, JSON.stringify(errorContext));
    
    // Track error analytics
    trackAnalytics({
      name: 'error_boundary_triggered',
      category: 'error',
      data: {
        errorType: error.name,
        errorMessage: error.message,
        componentName: name,
        level,
        errorId,
      },
    });

    // Call custom error handler
    onError?.(error, errorInfo);

    this.setState({ errorInfo });
  }

  private getHealthcareContext = () => {
    try {
      return {
        currentPath: window.location.pathname,
        isProcessingFile: window.location.pathname.includes('upload'),
        isDashboard: window.location.pathname.includes('dashboard'),
        isAnalytics: window.location.pathname.includes('analytics'),
        hasStoredData: localStorage.getItem('healthcare-preauth_data') !== null,
      };
    } catch {
      return {};
    }
  };

  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      
      trackAnalytics({
        name: 'error_boundary_retry',
        category: 'error',
        data: {
          errorId: this.state.errorId,
          retryAttempt: this.retryCount,
        },
      });

      this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    } else {
      this.handleAction('reload');
    }
  };

  private handleAction = (action: string) => {
    trackAnalytics({
      name: 'error_boundary_action',
      category: 'error',
      data: {
        action,
        errorId: this.state.errorId,
      },
    });

    switch (action) {
      case 'reload':
        window.location.reload();
        break;
      case 'home':
        window.location.href = '/';
        break;
      case 'dashboard':
        window.location.href = '/dashboard';
        break;
      case 'support':
        // Open support chat or email
        window.open('mailto:support@healthcare-preauth.com?subject=Error Report&body=Error ID: ' + this.state.errorId);
        break;
      case 'retry':
        this.handleRetry();
        break;
    }
  };

  render() {
    if (this.state.hasError) {
      const { level = 'component' } = this.props;
      const recoveryActions = getRecoveryActions(level);
      const errorMessage = getHealthcareErrorMessage(this.state.error);
      
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="flex justify-center mb-6">
              <div className="p-3 bg-red-100 rounded-full">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 mb-3">
              {level === 'critical' ? 'Critical System Error' : 'Something went wrong'}
            </h1>
            
            <p className="text-gray-600 mb-6">
              {errorMessage}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                  Technical Details
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-800 max-h-32 overflow-auto">
                  <div><strong>Error:</strong> {this.state.error.message}</div>
                  <div><strong>ID:</strong> {this.state.errorId}</div>
                  <div><strong>Retries:</strong> {this.retryCount}/{this.maxRetries}</div>
                </div>
              </details>
            )}

            <div className="flex flex-col gap-3">
              {recoveryActions.map(({ label, action, icon: Icon }) => (
                <button
                  key={action}
                  onClick={() => this.handleAction(action)}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>

            {this.retryCount < this.maxRetries && (
              <button
                onClick={this.handleRetry}
                className="mt-4 text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Try Again ({this.maxRetries - this.retryCount} attempts remaining)
              </button>
            )}

            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-400">
                Error ID: {this.state.errorId}
                <br />
                If this problem persists, please contact our support team.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

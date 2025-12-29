"use client";

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID for tracking
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to our custom error reporting system
    this.logError(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  private logError = async (error: Error, errorInfo: ErrorInfo) => {
    const errorReport = {
      errorId: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: this.getUserId(),
    };

    try {
      // Store in localStorage for now (simple solution)
      const existingErrors = JSON.parse(localStorage.getItem('app_errors') || '[]');
      existingErrors.push(errorReport);
      
      // Keep only last 50 errors
      const recentErrors = existingErrors.slice(-50);
      localStorage.setItem('app_errors', JSON.stringify(recentErrors));

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('🚨 Application Error Caught');
        console.error('Error:', error);
        console.error('Error Info:', errorInfo);
        console.error('Error ID:', this.state.errorId);
        console.groupEnd();
      }
    } catch (loggingError) {
      console.error('Failed to log error:', loggingError);
    }
  };

  private getUserId = (): string | null => {
    try {
      // Try to get user ID from auth context or localStorage
      const authData = localStorage.getItem('auth_user');
      if (authData) {
        const user = JSON.parse(authData);
        return user.user_id || user.id || null;
      }
    } catch {
      // Ignore errors when getting user ID
    }
    return null;
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportError = () => {
    const errorDetails = {
      errorId: this.state.errorId,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      timestamp: new Date().toISOString(),
    };

    // Create mailto link for simple error reporting
    const subject = encodeURIComponent(`Error Report - ${this.state.errorId}`);
    const body = encodeURIComponent(`
Error Details:
${JSON.stringify(errorDetails, null, 2)}

Please describe what you were doing when this error occurred:
[Your description here]
    `);
    
    window.open(`mailto:support@yourapp.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-destructive" />
              </div>
              <CardTitle className="text-xl">Something went wrong</CardTitle>
              <CardDescription>
                We apologize for the inconvenience. The application encountered an unexpected error.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <Badge variant="secondary" className="font-mono text-xs">
                  {this.state.errorId}
                </Badge>
              </div>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-sm font-medium text-destructive mb-1">
                    {this.state.error.message}
                  </p>
                  <details className="text-xs text-muted-foreground">
                    <summary className="cursor-pointer hover:text-foreground">
                      Stack trace
                    </summary>
                    <pre className="mt-2 whitespace-pre-wrap break-all">
                      {this.state.error.stack}
                    </pre>
                  </details>
                </div>
              )}

              <div className="flex flex-col gap-2">
                <Button onClick={this.handleRetry} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try again
                </Button>
                <Button variant="outline" onClick={this.handleGoHome} className="w-full">
                  <Home className="w-4 h-4 mr-2" />
                  Go to homepage
                </Button>
                <Button variant="ghost" onClick={this.handleReportError} className="w-full">
                  <Bug className="w-4 h-4 mr-2" />
                  Report this error
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for manually logging errors
export const useErrorReporting = () => {
  const logError = (error: Error, context?: string) => {
    const errorReport = {
      errorId: `MAN_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      message: error.message,
      stack: error.stack,
      context: context || 'Manual report',
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    try {
      const existingErrors = JSON.parse(localStorage.getItem('app_errors') || '[]');
      existingErrors.push(errorReport);
      localStorage.setItem('app_errors', JSON.stringify(existingErrors.slice(-50)));
      
      if (process.env.NODE_ENV === 'development') {
        console.error('Manual error report:', errorReport);
      }
    } catch (loggingError) {
      console.error('Failed to log manual error:', loggingError);
    }
  };

  const getStoredErrors = () => {
    try {
      return JSON.parse(localStorage.getItem('app_errors') || '[]');
    } catch {
      return [];
    }
  };

  const clearStoredErrors = () => {
    localStorage.removeItem('app_errors');
  };

  return { logError, getStoredErrors, clearStoredErrors };
};

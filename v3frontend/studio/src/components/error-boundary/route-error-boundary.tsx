"use client";

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  level?: 'page' | 'component' | 'critical';
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

export class RouteErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error with context
    this.logRouteError(error, errorInfo);
    
    // Call optional error handler
    this.props.onError?.(error, errorInfo);
  }

  private logRouteError = (error: Error, errorInfo: ErrorInfo) => {
    const errorReport = {
      errorId: `ROUTE_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      level: this.props.level || 'page',
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      pathname: window.location.pathname,
      retryCount: this.state.retryCount,
    };

    try {
      const existingErrors = JSON.parse(localStorage.getItem('app_errors') || '[]');
      existingErrors.push(errorReport);
      localStorage.setItem('app_errors', JSON.stringify(existingErrors.slice(-50)));
      
      if (process.env.NODE_ENV === 'development') {
        console.group(`🚨 ${this.props.level?.toUpperCase()} Error`);
        console.error('Error:', error);
        console.error('Component Stack:', errorInfo.componentStack);
        console.error('Retry Count:', this.state.retryCount);
        console.groupEnd();
      }
    } catch (loggingError) {
      console.error('Failed to log route error:', loggingError);
    }
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { level = 'page' } = this.props;
      const canRetry = this.state.retryCount < this.maxRetries;

      // Critical errors show minimal UI
      if (level === 'critical') {
        return (
          <Alert variant="destructive" className="m-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              A critical error occurred. Please refresh the page.
              {canRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  className="ml-2"
                  onClick={this.handleRetry}
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Retry
                </Button>
              )}
            </AlertDescription>
          </Alert>
        );
      }

      // Component-level errors show inline
      if (level === 'component') {
        return (
          <div className="p-4 border border-destructive/20 rounded-md bg-destructive/5">
            <div className="flex items-center gap-2 text-destructive mb-2">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">Component Error</span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              This component failed to load properly.
            </p>
            {canRetry && (
              <Button variant="outline" size="sm" onClick={this.handleRetry}>
                <RefreshCw className="w-3 h-3 mr-1" />
                Retry ({this.maxRetries - this.state.retryCount} left)
              </Button>
            )}
          </div>
        );
      }

      // Page-level errors show full fallback
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="mb-6 w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-destructive" />
          </div>
          
          <h2 className="text-2xl font-semibold mb-2">Page Error</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            This page encountered an error and couldn't load properly. 
            {this.state.retryCount > 0 && ` (Attempt ${this.state.retryCount + 1})`}
          </p>

          <div className="flex gap-3">
            {canRetry && (
              <Button onClick={this.handleRetry}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Try again
              </Button>
            )}
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go back
            </Button>
          </div>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="mt-6 text-left max-w-2xl">
              <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                Show error details
              </summary>
              <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-40">
                {this.state.error.stack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

// Functional wrapper for easier use
interface RouteErrorWrapperProps {
  children: ReactNode;
  level?: 'page' | 'component' | 'critical';
  fallback?: ReactNode;
}

export function RouteErrorWrapper({ children, level, fallback }: RouteErrorWrapperProps) {
  return (
    <RouteErrorBoundary level={level} fallback={fallback}>
      {children}
    </RouteErrorBoundary>
  );
}

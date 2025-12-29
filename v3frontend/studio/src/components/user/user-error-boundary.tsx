"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  AlertCircle, 
  RefreshCw, 
  Home, 
  Bug, 
  Wifi,
  WifiOff,
  Server,
  Shield
} from 'lucide-react';

interface UserErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorType: 'network' | 'authentication' | 'server' | 'client' | 'unknown';
}

interface UserErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
}

export class UserErrorBoundary extends React.Component<UserErrorBoundaryProps, UserErrorBoundaryState> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: UserErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorType: 'unknown'
    };
  }

  static getDerivedStateFromError(error: Error): Partial<UserErrorBoundaryState> {
    const errorType = UserErrorBoundary.categorizeError(error);
    return {
      hasError: true,
      error,
      errorType
    };
  }

  private static categorizeError(error: Error): UserErrorBoundaryState['errorType'] {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return 'network';
    }
    if (message.includes('unauthorized') || message.includes('authentication') || message.includes('401')) {
      return 'authentication';
    }
    if (message.includes('server') || message.includes('500') || message.includes('503')) {
      return 'server';
    }
    if (message.includes('404') || message.includes('not found')) {
      return 'client';
    }
    
    return 'unknown';
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('UserErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // Log error to monitoring service
    this.logErrorToService(error, errorInfo);
  }

  private logErrorToService = (error: Error, errorInfo: React.ErrorInfo) => {
    // In a real app, send to monitoring service like Sentry
    console.error('Error logged:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  };

  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorType: 'unknown'
      });
    }
  };

  private handleReset = () => {
    this.retryCount = 0;
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorType: 'unknown'
    });
  };

  private getErrorIcon = () => {
    switch (this.state.errorType) {
      case 'network':
        return <WifiOff className="h-8 w-8 text-orange-500" />;
      case 'authentication':
        return <Shield className="h-8 w-8 text-red-500" />;
      case 'server':
        return <Server className="h-8 w-8 text-red-500" />;
      case 'client':
        return <Bug className="h-8 w-8 text-yellow-500" />;
      default:
        return <AlertCircle className="h-8 w-8 text-red-500" />;
    }
  };

  private getErrorTitle = () => {
    switch (this.state.errorType) {
      case 'network':
        return 'Connection Problem';
      case 'authentication':
        return 'Authentication Error';
      case 'server':
        return 'Server Error';
      case 'client':
        return 'Page Not Found';
      default:
        return 'Something Went Wrong';
    }
  };

  private getErrorDescription = () => {
    switch (this.state.errorType) {
      case 'network':
        return 'Unable to connect to our servers. Please check your internet connection and try again.';
      case 'authentication':
        return 'Your session has expired or you don\'t have permission to access this page.';
      case 'server':
        return 'Our servers are experiencing issues. We\'re working to fix this as quickly as possible.';
      case 'client':
        return 'The page you\'re looking for doesn\'t exist or has been moved.';
      default:
        return 'An unexpected error occurred. Our team has been notified.';
    }
  };

  private getErrorActions = () => {
    const canRetry = this.retryCount < this.maxRetries;
    
    switch (this.state.errorType) {
      case 'network':
        return (
          <div className="flex gap-2">
            {canRetry && (
              <Button onClick={this.handleRetry} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try Again ({this.maxRetries - this.retryCount} left)
              </Button>
            )}
            <Button variant="outline" onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Page
            </Button>
          </div>
        );
      
      case 'authentication':
        return (
          <div className="flex gap-2">
            <Button onClick={() => window.location.href = '/login'}>
              <Shield className="h-4 w-4 mr-2" />
              Sign In Again
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </div>
        );
      
      case 'server':
        return (
          <div className="flex gap-2">
            {canRetry && (
              <Button onClick={this.handleRetry} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try Again ({this.maxRetries - this.retryCount} left)
              </Button>
            )}
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </div>
        );
      
      case 'client':
        return (
          <Button onClick={() => window.location.href = '/'}>
            <Home className="h-4 w-4 mr-2" />
            Go Home
          </Button>
        );
      
      default:
        return (
          <div className="flex gap-2">
            {canRetry && (
              <Button onClick={this.handleRetry} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try Again ({this.maxRetries - this.retryCount} left)
              </Button>
            )}
            <Button variant="outline" onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Page
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </div>
        );
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback component
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} reset={this.handleReset} />;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4">
                {this.getErrorIcon()}
              </div>
              <CardTitle className="text-xl">
                {this.getErrorTitle()}
              </CardTitle>
              <CardDescription>
                {this.getErrorDescription()}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {this.state.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="font-mono text-xs">
                    {this.state.error.message}
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="flex justify-center">
                {this.getErrorActions()}
              </div>

              {/* Developer Info (only in development) */}
              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-muted-foreground">
                    Technical Details (Dev Only)
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                    {this.state.error?.stack}
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for functional components to use error boundary
export const useErrorHandler = () => {
  return (error: Error, errorInfo?: React.ErrorInfo) => {
    console.error('Error caught by hook:', error, errorInfo);
    // Could integrate with error reporting service
  };
};

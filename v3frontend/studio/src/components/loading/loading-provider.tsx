"use client";

import { createContext, useContext, useState, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

interface LoadingContextType {
  loadingStates: Record<string, LoadingState>;
  setLoading: (key: string, state: LoadingState | boolean) => void;
  clearLoading: (key: string) => void;
  clearAllLoading: () => void;
  isAnyLoading: boolean;
  // Global convenience methods
  setIsLoading: (isLoading: boolean, message?: string) => void;
  isLoading: boolean;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

export function LoadingProvider({ children }: { children: ReactNode }) {
  const [loadingStates, setLoadingStates] = useState<Record<string, LoadingState>>({});

  const setLoading = (key: string, state: LoadingState | boolean) => {
    setLoadingStates(prev => ({
      ...prev,
      [key]: typeof state === 'boolean' 
        ? { isLoading: state }
        : state
    }));
  };

  const clearLoading = (key: string) => {
    setLoadingStates(prev => {
      const newState = { ...prev };
      delete newState[key];
      return newState;
    });
  };

  const clearAllLoading = () => {
    setLoadingStates({});
  };

  const isAnyLoading = Object.values(loadingStates).some(state => state.isLoading);

  // Global convenience methods
  const setIsLoading = (isLoading: boolean, message?: string) => {
    setLoading('global', { isLoading, message });
  };

  const isLoading = loadingStates['global']?.isLoading || false;

  return (
    <LoadingContext.Provider value={{
      loadingStates,
      setLoading,
      clearLoading,
      clearAllLoading,
      isAnyLoading,
      setIsLoading,
      isLoading,
    }}>
      {children}
      <GlobalLoadingOverlay />
    </LoadingContext.Provider>
  );
}

export function useLoading() {
  const context = useContext(LoadingContext);
  if (context === undefined) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
}

// Global loading overlay for critical operations
function GlobalLoadingOverlay() {
  const { loadingStates } = useLoading();
  
  // Show overlay for global operations
  const globalLoading = loadingStates['global'];
  
  if (!globalLoading?.isLoading) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center">
      <div className="bg-card border rounded-lg p-6 shadow-lg max-w-sm w-full mx-4">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin" />
          <div className="flex-1">
            <p className="font-medium">
              {globalLoading.message || 'Loading...'}
            </p>
            {globalLoading.progress !== undefined && (
              <div className="mt-2">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Progress</span>
                  <span>{Math.round(globalLoading.progress)}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${globalLoading.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Component loading wrapper
interface LoadingWrapperProps {
  loading: boolean;
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
  message?: string;
}

export function LoadingWrapper({ 
  loading, 
  children, 
  fallback, 
  className,
  message 
}: LoadingWrapperProps) {
  if (loading) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="flex items-center space-x-3">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-muted-foreground">
            {message || 'Loading...'}
          </span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Button loading state
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  loadingText?: string;
  children: ReactNode;
}

export function LoadingButton({ 
  loading, 
  loadingText, 
  children, 
  disabled,
  className,
  ...props 
}: LoadingButtonProps) {
  return (
    <button
      {...props}
      disabled={loading || disabled}
      className={cn(
        "inline-flex items-center justify-center",
        className
      )}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
      {loading ? loadingText || 'Loading...' : children}
    </button>
  );
}

// Hook for managing component-level loading
export function useComponentLoading(key?: string) {
  const { setLoading, clearLoading, loadingStates } = useLoading();
  const loadingKey = key || 'component';
  
  const isLoading = loadingStates[loadingKey]?.isLoading || false;
  const loadingState = loadingStates[loadingKey];

  const startLoading = (message?: string, progress?: number) => {
    setLoading(loadingKey, { isLoading: true, message, progress });
  };

  const stopLoading = () => {
    clearLoading(loadingKey);
  };

  const updateProgress = (progress: number, message?: string) => {
    setLoading(loadingKey, { 
      isLoading: true, 
      progress, 
      message: message || loadingState?.message 
    });
  };

  return {
    isLoading,
    loadingState,
    startLoading,
    stopLoading,
    updateProgress,
  };
}

// Hook for API loading states
export function useApiLoading() {
  const { setLoading, clearLoading, loadingStates } = useLoading();

  const setApiLoading = (endpoint: string, loading: boolean, message?: string) => {
    const key = `api_${endpoint}`;
    if (loading) {
      setLoading(key, { isLoading: true, message });
    } else {
      clearLoading(key);
    }
  };

  const isApiLoading = (endpoint: string) => {
    const key = `api_${endpoint}`;
    return loadingStates[key]?.isLoading || false;
  };

  const getApiLoadingState = (endpoint: string) => {
    const key = `api_${endpoint}`;
    return loadingStates[key];
  };

  return {
    setApiLoading,
    isApiLoading,
    getApiLoadingState,
  };
}

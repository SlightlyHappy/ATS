"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  persistent?: boolean;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
  success: (title: string, description?: string, options?: Partial<Toast>) => void;
  error: (title: string, description?: string, options?: Partial<Toast>) => void;
  warning: (title: string, description?: string, options?: Partial<Toast>) => void;
  info: (title: string, description?: string, options?: Partial<Toast>) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const TOAST_DURATION = {
  success: 4000,
  info: 5000,
  warning: 6000,
  error: 8000,
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? TOAST_DURATION[toast.type],
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove toast after duration (unless persistent)
    if (!newToast.persistent && newToast.duration) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
  }, [removeToast]);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const success = useCallback((title: string, description?: string, options?: Partial<Toast>) => {
    addToast({ ...options, type: 'success', title, description });
  }, [addToast]);

  const error = useCallback((title: string, description?: string, options?: Partial<Toast>) => {
    addToast({ ...options, type: 'error', title, description });
  }, [addToast]);

  const warning = useCallback((title: string, description?: string, options?: Partial<Toast>) => {
    addToast({ ...options, type: 'warning', title, description });
  }, [addToast]);

  const info = useCallback((title: string, description?: string, options?: Partial<Toast>) => {
    addToast({ ...options, type: 'info', title, description });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{
      toasts,
      addToast,
      removeToast,
      clearAllToasts,
      success,
      error,
      warning,
      info,
    }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

function ToastContainer() {
  const { toasts } = useToast();

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToast();

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const styles = {
    success: "bg-green-50 border-green-200 text-green-800 dark:bg-green-900/50 dark:border-green-800 dark:text-green-200",
    error: "bg-red-50 border-red-200 text-red-800 dark:bg-red-900/50 dark:border-red-800 dark:text-red-200",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/50 dark:border-yellow-800 dark:text-yellow-200",
    info: "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/50 dark:border-blue-800 dark:text-blue-200",
  };

  const Icon = icons[toast.type];

  return (
    <div className={cn(
      "border rounded-lg p-4 shadow-lg animate-in slide-in-from-top-1 duration-300",
      styles[toast.type]
    )}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
        
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm">
            {toast.title}
          </div>
          {toast.description && (
            <div className="text-sm opacity-90 mt-1">
              {toast.description}
            </div>
          )}
          {toast.action && (
            <button
              onClick={toast.action.onClick}
              className="text-sm font-medium underline hover:no-underline mt-2"
            >
              {toast.action.label}
            </button>
          )}
        </div>

        <button
          onClick={() => removeToast(toast.id)}
          className="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// Specialized toast hooks for common scenarios
export function useApiToasts() {
  const { success, error, warning } = useToast();

  const handleApiSuccess = (message: string, description?: string) => {
    success(message, description);
  };

  const handleApiError = (error: any, context?: string) => {
    const title = context || 'Request failed';
    const description = error?.message || error?.error || 'An unexpected error occurred';
    error(title, description);
  };

  const handleValidationError = (errors: Record<string, string[]>) => {
    const errorMessages = Object.entries(errors)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('\n');
    
    error('Validation failed', errorMessages);
  };

  const handleNetworkError = () => {
    warning(
      'Network error', 
      'Please check your connection and try again',
      { 
        action: { 
          label: 'Retry', 
          onClick: () => window.location.reload() 
        }
      }
    );
  };

  return {
    handleApiSuccess,
    handleApiError,
    handleValidationError,
    handleNetworkError,
  };
}

export function useFormToasts() {
  const { success, error } = useToast();

  const handleFormSuccess = (action: string) => {
    success(`${action} successful`, 'Your changes have been saved');
  };

  const handleFormError = (action: string, errorMessage?: string) => {
    error(
      `${action} failed`, 
      errorMessage || 'Please check your input and try again'
    );
  };

  return {
    handleFormSuccess,
    handleFormError,
  };
}

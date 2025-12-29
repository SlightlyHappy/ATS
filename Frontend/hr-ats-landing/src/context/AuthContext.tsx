// Authentication context and API functions
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// API Base URL
const API_BASE_URL = 'https://hrtoolsbackend-production.up.railway.app';

// Types
interface User {
  user_id: number;
  email?: string;
  username?: string;
  name?: string;
  access_type: 'trial' | 'premium' | 'enterprise' | 'admin';
  is_admin: boolean;
  trial_info?: {
    resume_limits: { used: number; limit: number };
    legal_limits: { used: number; limit: number };
  };
  credits?: {
    trial_credits: number;
    premium_credits: number;
    total_used: number;
    credits_remaining: number;
  };
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials, isAdmin: boolean) => Promise<void>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  apiRequest: (endpoint: string, options?: RequestInit) => Promise<any>;
}

interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}

interface LoginResponse {
  success: boolean;
  token: string;
  user: User;
  message?: string;
}

// Auth Context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth Provider Component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Session timeout duration (5 minutes)
  const SESSION_TIMEOUT = 5 * 60 * 1000; // 5 minutes in milliseconds

  // Check if session is expired
  const isSessionExpired = () => {
    const loginTime = localStorage.getItem('login_time');
    if (!loginTime) return true;
    
    const sessionAge = Date.now() - parseInt(loginTime);
    return sessionAge > SESSION_TIMEOUT;
  };

  // Initialize auth state from localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('auth_user');

    if (savedToken && savedUser && !isSessionExpired()) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        // Validate session
        validateSession(savedToken);
      } catch (error) {
        console.error('Failed to restore auth state:', error);
        logout();
      }
    } else if (savedToken || savedUser) {
      // Clear expired session
      logout();
    }
    setLoading(false);
  }, []);

  // Auto-logout when session expires
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (user && token) {
      const loginTime = localStorage.getItem('login_time');
      if (loginTime) {
        const timeRemaining = SESSION_TIMEOUT - (Date.now() - parseInt(loginTime));
        
        if (timeRemaining > 0) {
          timeoutId = setTimeout(() => {
            console.log('Session expired - auto logout');
            logout();
          }, timeRemaining);
        } else {
          logout();
        }
      }
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [user, token]);

  // Validate session with backend
  const validateSession = async (authToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/session`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Session validation failed');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error('Invalid session');
      }

      // Update user data with latest info
      setUser(data.user);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
    } catch (error) {
      console.error('Session validation failed:', error);
      logout();
    }
  };

  // Login function
  const login = async (credentials: LoginCredentials, isAdmin: boolean = false) => {
    setLoading(true);
    try {
      const endpoint = isAdmin ? '/api/auth/admin-login' : '/api/auth/user-login';
      const payload = isAdmin 
        ? { username: credentials.username, password: credentials.password }
        : { email: credentials.email, password: credentials.password };

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data: LoginResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }

      if (!data.success) {
        throw new Error(data.message || 'Login failed');
      }

      // Store auth data with timestamp
      setToken(data.token);
      setUser(data.user);
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      localStorage.setItem('login_time', Date.now().toString());

    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      if (token) {
        // Notify backend about logout
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state
      setUser(null);
      setToken(null);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      localStorage.removeItem('login_time');
    }
  };

  // API request method with auth
  const makeApiRequest = async (endpoint: string, options: RequestInit = {}) => {
    return apiRequest(endpoint, options, token || undefined);
  };

  const isAuthenticated = !!user && !!token;
  const isAdmin = user?.is_admin || false;

  const contextValue: AuthContextType = {
    user,
    token,
    login,
    logout,
    loading,
    isAuthenticated,
    isAdmin,
    apiRequest: makeApiRequest
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// API Helper Functions
export const apiRequest = async (endpoint: string, options: RequestInit = {}, token?: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };

  // Add existing headers if they exist and are strings
  if (options.headers) {
    Object.entries(options.headers).forEach(([key, value]) => {
      if (typeof value === 'string') {
        headers[key] = value;
      }
    });
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
};

// Protected Route Component
interface ProtectedRouteProps {
  children: ReactNode;
  adminOnly?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  adminOnly = false 
}) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-gray-600">Please log in to access this page.</p>
        </div>
      </div>
    );
  }

  if (adminOnly && !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Admin Access Required</h2>
          <p className="text-gray-600">You need administrator privileges to access this page.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default AuthContext;

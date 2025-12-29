import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { createClient } from '@supabase/supabase-js';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// Create Supabase client only if credentials are available
const supabase = supabaseUrl && supabaseAnonKey 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [useSupabase, setUseSupabase] = useState(!!supabase);

  // Check for existing session on app startup
  useEffect(() => {
    checkExistingSession();
    
    // If Supabase is available, listen for auth state changes
    if (supabase) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          console.log('Supabase auth state change:', event, session?.user?.email);
          if (session?.user && event !== 'SIGNED_OUT') {
            await loadSupabaseUserProfile(session.user);
          } else if (event === 'SIGNED_OUT') {
            setUser(null);
            setIsAuthenticated(false);
            // Also clear any local storage tokens
            localStorage.removeItem('bear_systems_token');
            delete axios.defaults.headers.common['Authorization'];
          }
          setLoading(false);
        }
      );

      return () => subscription?.unsubscribe();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const checkExistingSession = async () => {
    try {
      // First, try Supabase if available
      if (supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          console.log('Found existing Supabase session');
          await loadSupabaseUserProfile(session.user);
          return;
        }
      }

      // Fall back to custom backend authentication
      const token = localStorage.getItem('bear_systems_token');
      if (token) {
        // Validate session with backend
        const response = await axios.get('/api/auth/session', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.valid) {
          setUser(response.data.user);
          setIsAuthenticated(true);
          setUseSupabase(false);
          // Set default axios header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        } else {
          // Invalid session, clear stored token
          localStorage.removeItem('bear_systems_token');
        }
      }
    } catch (error) {
      console.error('Session validation failed:', error);
      localStorage.removeItem('bear_systems_token');
    } finally {
      setLoading(false);
    }
  };

  const loadSupabaseUserProfile = async (authUser) => {
    try {
      if (!supabase) return;
      
      const { data: profile, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('id', authUser.id)
        .single();

      if (error && error.code !== 'PGRST116') { // Not found error
        console.error('Failed to load user profile:', error);
        return;
      }

      if (profile) {
        setUser({
          ...authUser,
          ...profile,
          user_id: profile.id
        });
        setIsAuthenticated(true);
        setUseSupabase(true);
        
        // Set up axios with Supabase session token for backend calls
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
        }
      }
    } catch (error) {
      console.error('Failed to load Supabase user profile:', error);
    }
  };

  const login = async (email, password, isAdmin = false) => {
    try {
      // Always try Supabase authentication first if available (even for admins if they have Supabase accounts)
      if (supabase && !isAdmin) {
        console.log('Attempting Supabase login for:', email);
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password
        });

        if (error) {
          console.log('Supabase login failed, trying backend:', error.message);
        } else if (data.user) {
          console.log('✅ Supabase login successful');
          // The onAuthStateChange listener will handle setting user state
          return { success: true, user: data.user, provider: 'supabase' };
        }
      }

      // Backend authentication (for admins and fallback)
      console.log(`${isAdmin ? 'Admin' : 'User'} login via backend API`);
      const endpoint = isAdmin ? '/api/auth/admin-login' : '/api/auth/user-login';
      const payload = isAdmin 
        ? { username: email, password } 
        : { email, password };

      const response = await axios.post(endpoint, payload);
      
      if (response.data.success) {
        const { token, user: userData } = response.data;
        
        // Store token and user data
        localStorage.setItem('bear_systems_token', token);
        setUser({
          ...userData,
          provider: userData.provider || 'sqlite',
          needs_supabase_sync: userData.needs_supabase_sync || false
        });
        setIsAuthenticated(true);
        setUseSupabase(userData.provider === 'supabase');
        
        // Set default axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        const provider = userData.provider || 'sqlite';
        if (provider === 'sqlite') {
          console.log('⚠️  User authenticated via SQLite fallback');
        } else {
          console.log('✅ User authenticated via backend');
        }
        
        return { success: true, user: userData, provider };
      } else {
        return { success: false, error: response.data.message || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || error.message || 'Login failed. Please check your credentials.' 
      };
    }
  };

  const logout = async () => {
    try {
      // If using Supabase, sign out from Supabase
      if (useSupabase && supabase) {
        console.log('Logging out from Supabase');
        const { error } = await supabase.auth.signOut();
        if (error) {
          console.error('Supabase logout error:', error);
        }
        // The onAuthStateChange listener will handle clearing state
        return;
      }

      // Custom backend logout
      console.log('Logging out from custom backend');
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state and storage regardless of server response
      localStorage.removeItem('bear_systems_token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setIsAuthenticated(false);
      setUseSupabase(false);
    }
  };

  const createUser = async (userData) => {
    try {
      // Try Supabase signup first if available
      if (supabase && !userData.isAdmin) {
        console.log('Creating user with Supabase');
        const { data, error } = await supabase.auth.signUp({
          email: userData.email,
          password: userData.password,
          options: {
            data: {
              full_name: userData.full_name,
              company_name: userData.company_name,
              job_title: userData.job_title
            }
          }
        });

        if (error) {
          console.log('Supabase signup failed, trying custom backend:', error.message);
        } else {
          return { 
            success: true, 
            data: data.user, 
            needsConfirmation: !data.session,
            provider: 'supabase'
          };
        }
      }

      // Fall back to custom backend
      console.log('Creating user with custom backend');
      const response = await axios.post('/api/auth/create-user', userData);
      return { success: true, data: response.data, provider: 'custom' };
    } catch (error) {
      console.error('User creation error:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || error.message || 'Failed to create user' 
      };
    }
  };

  const updateProfile = async (updates) => {
    try {
      if (useSupabase && supabase) {
        // Update Supabase user profile
        const { data, error } = await supabase
          .from('user_profiles')
          .update(updates)
          .eq('id', user.id)
          .select()
          .single();

        if (error) throw error;

        setUser(prev => ({ ...prev, ...data }));
        return { success: true, data };
      } else {
        // Update via custom backend
        const response = await axios.put('/api/auth/profile', updates);
        setUser(prev => ({ ...prev, ...response.data }));
        return { success: true, data: response.data };
      }
    } catch (error) {
      console.error('Profile update error:', error);
      return { 
        success: false, 
        error: error.message || 'Failed to update profile'
      };
    }
  };

  const refreshUserData = async () => {
    try {
      if (useSupabase && supabase) {
        // Refresh from Supabase
        const { data: { user: authUser } } = await supabase.auth.getUser();
        if (authUser) {
          await loadSupabaseUserProfile(authUser);
          return user;
        }
      } else {
        // Refresh from custom backend
        const response = await axios.get('/api/auth/session');
        if (response.data.valid) {
          setUser(response.data.user);
          return response.data.user;
        }
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
    return null;
  };

  // Helper functions for user access levels
  const isTrialUser = () => user?.access_type === 'trial';
  const isFullUser = () => user?.access_type === 'full';
  const isEnterpriseUser = () => user?.access_type === 'enterprise';
  const isAdmin = () => user?.is_admin === true;

  // Trial management helpers
  const canUploadMore = () => {
    if (!isTrialUser()) return true;
    return (user?.trial_usage || 0) < (user?.trial_limit || 100);
  };

  const getRemainingTrialUses = () => {
    if (!isTrialUser()) return null;
    return Math.max(0, (user?.trial_limit || 100) - (user?.trial_usage || 0));
  };

  const value = {
    // Core auth state
    user,
    loading,
    isAuthenticated,
    
    // Auth methods
    login,
    logout,
    createUser,
    updateProfile,
    refreshUserData,
    
    // User type helpers
    isTrialUser,
    isFullUser,
    isEnterpriseUser,
    isAdmin,
    
    // Trial management
    canUploadMore,
    getRemainingTrialUses,
    
    // User data shortcuts
    userEmail: user?.email,
    accessType: user?.access_type,
    trialUsage: user?.trial_usage || 0,
    trialLimit: user?.trial_limit || 100,
    userId: user?.user_id || user?.id,
    
    // System info
    useSupabase,
    supabaseAvailable: !!supabase,
    
    // Direct access to clients (for advanced usage)
    supabase: useSupabase ? supabase : null,
    axios
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;

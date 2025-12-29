import React, { createContext, useContext, useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseAnonKey);

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

  // Check for existing session on app startup
  useEffect(() => {
    checkExistingSession();
    
    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session?.user) {
          await loadUserProfile(session.user);
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
        setLoading(false);
      }
    );

    return () => subscription?.unsubscribe();
  }, []);

  const checkExistingSession = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        await loadUserProfile(session.user);
      }
    } catch (error) {
      console.error('Session check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserProfile = async (authUser) => {
    try {
      const { data: profile, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('id', authUser.id)
        .single();

      if (error && error.code !== 'PGRST116') { // Not found error
        throw error;
      }

      if (profile) {
        setUser({
          ...authUser,
          ...profile,
          user_id: profile.id
        });
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  const login = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) {
        return { 
          success: false, 
          error: error.message 
        };
      }

      return { 
        success: true, 
        user: data.user 
      };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: 'Login failed. Please check your credentials.' 
      };
    }
  };

  const signUp = async (email, password, userData = {}) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: userData // This goes to raw_user_meta_data
        }
      });

      if (error) {
        return { 
          success: false, 
          error: error.message 
        };
      }

      return { 
        success: true, 
        user: data.user,
        needsConfirmation: !data.session
      };
    } catch (error) {
      console.error('Signup error:', error);
      return { 
        success: false, 
        error: 'Signup failed. Please try again.' 
      };
    }
  };

  const logout = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const updateProfile = async (updates) => {
    try {
      const { data, error } = await supabase
        .from('user_profiles')
        .update(updates)
        .eq('id', user.id)
        .select()
        .single();

      if (error) throw error;

      setUser(prev => ({ ...prev, ...data }));
      return { success: true, data };
    } catch (error) {
      console.error('Profile update error:', error);
      return { 
        success: false, 
        error: error.message 
      };
    }
  };

  // Helper functions for user access levels
  const isTrialUser = () => user?.access_type === 'trial';
  const isFullUser = () => user?.access_type === 'full';
  const isEnterpriseUser = () => user?.access_type === 'enterprise';
  const isAdmin = () => user?.is_admin === true;

  // Check trial limits
  const canUploadMore = () => {
    if (!isTrialUser()) return true;
    return (user?.trial_usage || 0) < (user?.trial_limit || 100);
  };

  const getRemainingTrialUses = () => {
    if (!isTrialUser()) return null;
    return Math.max(0, (user?.trial_limit || 100) - (user?.trial_usage || 0));
  };

  const value = {
    // Core auth
    user,
    loading,
    isAuthenticated,
    login,
    signUp,
    logout,
    updateProfile,
    
    // User type checks
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
    userId: user?.id,
    
    // Supabase client for direct access if needed
    supabase
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import axios from 'axios';

const TrialContext = createContext();

export const useTrial = () => {
  const context = useContext(TrialContext);
  if (!context) {
    throw new Error('useTrial must be used within a TrialProvider');
  }
  return context;
};

export const TrialProvider = ({ children }) => {
  const { user, isAuthenticated, isTrialUser } = useAuth();
  const [trialStatus, setTrialStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadTrialStatus = useCallback(async () => {
    if (!isTrialUser()) return;
    
    try {
      setLoading(true);
      const response = await axios.get('/api/trial/status');
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to load trial status:', error);
    } finally {
      setLoading(false);
    }
  }, [isTrialUser]);

  // Load trial status when user changes
  useEffect(() => {
    if (isAuthenticated && isTrialUser()) {
      loadTrialStatus();
    } else {
      setTrialStatus(null);
    }
  }, [user, isAuthenticated, isTrialUser, loadTrialStatus]);

  const getRemainingAnalyses = () => {
    if (!isTrialUser() || !trialStatus) return null;
    return Math.max(0, trialStatus.trial_limit - trialStatus.trial_usage);
  };

  const getUsagePercentage = () => {
    if (!isTrialUser() || !trialStatus) return 0;
    return Math.min(100, (trialStatus.trial_usage / trialStatus.trial_limit) * 100);
  };

  const isNearLimit = () => {
    if (!isTrialUser()) return false;
    const remaining = getRemainingAnalyses();
    return remaining !== null && remaining <= 10; // Alert when 10 or fewer left
  };

  const isAtLimit = () => {
    if (!isTrialUser()) return false;
    const remaining = getRemainingAnalyses();
    return remaining !== null && remaining <= 0;
  };

  const canUploadMore = () => {
    if (!isTrialUser()) return true; // Full users have unlimited
    return !isAtLimit();
  };

  const canExportCSV = () => {
    return !isTrialUser(); // Only full users can export
  };

  const getUpgradeInfo = async () => {
    try {
      const response = await axios.get('/api/trial/upgrade-info');
      return response.data;
    } catch (error) {
      console.error('Failed to get upgrade info:', error);
      return {
        contact_email: 'support@bearsystems.co.in',
        phone: '+91-XXX-XXXXXXX',
        website: 'https://bearsystems.co.in'
      };
    }
  };

  const incrementUsage = async (count = 1) => {
    if (!isTrialUser()) return;
    
    try {
      const response = await axios.post('/api/trial/increment-usage', { count });
      if (response.data.success) {
        setTrialStatus(prev => prev ? {
          ...prev,
          trial_usage: prev.trial_usage + count
        } : null);
      }
    } catch (error) {
      console.error('Failed to increment trial usage:', error);
    }
  };

  // Trial status helpers
  const getStatusColor = () => {
    if (!isTrialUser()) return 'green';
    if (isAtLimit()) return 'red';
    if (isNearLimit()) return 'yellow';
    return 'green';
  };

  const getStatusMessage = () => {
    if (!isTrialUser()) return 'Full Access';
    if (isAtLimit()) return 'Trial Limit Reached';
    if (isNearLimit()) return 'Trial Limit Approaching';
    return 'Trial Active';
  };

  const getTrialBadgeText = () => {
    if (!isTrialUser()) return null;
    const remaining = getRemainingAnalyses();
    if (remaining === null) return 'Trial';
    return `Trial: ${remaining} left`;
  };

  // Restriction helpers for UI components
  const getUploadRestriction = () => {
    if (!isTrialUser()) return null;
    if (isAtLimit()) {
      return {
        blocked: true,
        title: 'Trial Limit Reached',
        message: 'You have reached your 100 resume limit. Upgrade to full access to continue.',
        action: 'Upgrade Now'
      };
    }
    if (isNearLimit()) {
      const remaining = getRemainingAnalyses();
      return {
        blocked: false,
        title: 'Trial Limit Approaching',
        message: `You have ${remaining} resumes remaining in your trial.`,
        action: 'Consider Upgrading'
      };
    }
    return null;
  };

  const getExportRestriction = () => {
    if (canExportCSV()) return null;
    return {
      blocked: true,
      title: 'CSV Export Not Available',
      message: 'CSV export is only available to full access users. Upgrade to export your resume analysis data.',
      action: 'Upgrade to Export'
    };
  };

  const getFeatureRestriction = (feature) => {
    switch (feature) {
      case 'upload':
        return getUploadRestriction();
      case 'export':
        return getExportRestriction();
      default:
        return null;
    }
  };

  const value = {
    // Status data
    trialStatus,
    loading,
    
    // Trial calculations
    getRemainingAnalyses,
    getUsagePercentage,
    isNearLimit,
    isAtLimit,
    
    // Permission checks
    canUploadMore,
    canExportCSV,
    
    // UI helpers
    getStatusColor,
    getStatusMessage,
    getTrialBadgeText,
    
    // Restriction helpers
    getUploadRestriction,
    getExportRestriction,
    getFeatureRestriction,
    
    // Actions
    loadTrialStatus,
    getUpgradeInfo,
    incrementUsage,
    
    // Shortcut properties
    isTrialActive: isTrialUser(),
    remainingAnalyses: getRemainingAnalyses(),
    usagePercentage: getUsagePercentage(),
    trialUsage: trialStatus?.trial_usage || 0,
    trialLimit: trialStatus?.trial_limit || 100
  };

  return (
    <TrialContext.Provider value={value}>
      {children}
    </TrialContext.Provider>
  );
};

export default TrialContext;

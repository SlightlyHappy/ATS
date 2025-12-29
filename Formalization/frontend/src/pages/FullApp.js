import React, { useState, useEffect } from 'react';
import { useTrial } from '../contexts/TrialContext';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import '../styles/premium.css';
import '../styles/components.css';
import FileUpload from '../components/FileUpload';
import ModernDashboard from '../components/ModernDashboard';
import RoleRequirements from '../components/RoleRequirements';
import EmailManager from '../components/EmailManager';
import DebugConsole from '../components/DebugConsole';
import AISettings from '../components/AISettings';
import HRLegal from '../components/HRLegal';
import TrialBanner from '../components/TrialBanner';
import UpgradePrompt from '../components/UpgradePrompt';
import apiClient from '../utils/apiClient';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Debug logging function
const debugLog = async (level, message, data = null) => {
  const logEntry = {
    level,
    message,
    data,
    timestamp: new Date().toISOString()
  };
  
  // Log to console
  console.log(`[${level.toUpperCase()}] ${message}`, data || '');
  
  // Send to backend
  try {
    await apiClient.post('/api/debug/logs', logEntry);
  } catch (error) {
    console.error('Failed to send debug log to backend:', error);
  }
};

// Make debugLog available globally
window.debugLog = debugLog;

function FullApp() {
  const [resumes, setResumes] = useState([]);
  // eslint-disable-next-line no-unused-vars
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [roleRequirements, setRoleRequirements] = useState(null);
  const [aiSettings, setAiSettings] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { 
    getUploadRestriction, 
    getExportRestriction,
    isTrialActive,
    loadTrialStatus,
    trialUsage,
    remainingAnalyses
  } = useTrial();

  useEffect(() => {
    debugLog('info', 'FullApp component mounted');
    
    // Initialize default AI settings for Ollama (since it's running)
    if (!aiSettings) {
      const defaultAiSettings = {
        provider: 'ollama',
        model: 'qwen2.5:7b',
        isConfigured: true,
        apiKey: '' // Ollama doesn't need API key
      };
      setAiSettings(defaultAiSettings);
      debugLog('info', 'Initialized default AI settings for Ollama');
    }
    
    // Load initial data
    fetchResumes();
    fetchRoleRequirements();
    
    // Load trial status if user is on trial
    if (isTrialActive) {
      loadTrialStatus();
    }
  }, [isTrialActive, aiSettings]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchResumes = async () => {
    try {
      debugLog('info', 'Fetching resumes...');
      
      const response = await apiClient.get('/api/resumes');
      setResumes(response.data.resumes || []);
      debugLog('info', `Loaded ${response.data.resumes?.length || 0} resumes`);
    } catch (error) {
      debugLog('error', 'Failed to fetch resumes', error.response?.data);
    }
  };

  const fetchRoleRequirements = async () => {
    try {
      const response = await apiClient.get('/api/role-requirements');
      setRoleRequirements(response.data);
    } catch (error) {
      debugLog('error', 'Failed to fetch role requirements', error.response?.data);
    }
  };

  const handleNewUploads = (uploadResults) => {
    debugLog('info', 'New uploads received', {
      total: uploadResults.length,
      successful: uploadResults.filter(r => r.status === 'success').length
    });
    
    // Add successful uploads to the resumes list
    const successfulUploads = uploadResults.filter(result => result.status === 'success');
    if (successfulUploads.length > 0) {
      setResumes(prev => [...successfulUploads, ...prev]);
      
      // Refresh trial status after upload
      if (isTrialActive) {
        loadTrialStatus();
      }
    }
  };

  const handleRoleRequirementsChange = (newRequirements) => {
    setRoleRequirements(newRequirements);
    debugLog('info', 'Role requirements updated');
  };

  const handleAISettingsChange = (newSettings) => {
    setAiSettings(newSettings);
    debugLog('info', 'AI settings updated', newSettings);
  };

  const handleClearResumes = async () => {
    try {
      setLoading(true);
      debugLog('info', 'Clearing all resumes...');
      
      await apiClient.delete('/api/clear');
      setResumes([]);
      
      // Refresh trial status after clearing
      if (isTrialActive) {
        loadTrialStatus();
      }
      
      debugLog('info', 'All resumes cleared successfully');
    } catch (error) {
      debugLog('error', 'Failed to clear resumes', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    // Check if export is allowed
    const exportRestriction = getExportRestriction();
    if (exportRestriction?.blocked) {
      debugLog('warning', 'CSV export blocked for trial user');
      // You could show a modal here with upgrade info
      return;
    }

    try {
      debugLog('info', 'Exporting resumes to CSV...');
      
      const response = await apiClient.get('/api/export', {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'resume_analysis.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      debugLog('info', 'CSV export completed successfully');
    } catch (error) {
      debugLog('error', 'Failed to export CSV', error.response?.data);
      
      if (error.response?.status === 403) {
        // Handle trial limitation
        debugLog('warning', 'CSV export not available in trial version');
      }
    }
  };

  // Check upload restrictions for trial users
  const uploadRestriction = isTrialActive ? getUploadRestriction() : { blocked: false };

  return (
      <div className="min-h-screen bg-gray-50">
        {/* Trial Banner for trial users */}
        {isTrialActive && (
          <TrialBanner 
            trialUsage={trialUsage}
            remainingAnalyses={remainingAnalyses}
            isNearLimit={remainingAnalyses <= 10}
            isAtLimit={remainingAnalyses <= 0}
          />
        )}

        {/* Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          resumes={resumes}
          setSidebarOpen={setSidebarOpen}
          isTrialUser={isTrialActive}
        />

        {/* Main Content */}
        <main className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-64' : ''}`}>
          <Header 
            sidebarOpen={sidebarOpen}
            setSidebarOpen={setSidebarOpen}
            activeTab={activeTab}
          />
          
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {activeTab === 'upload' && (
              <div className="animate-slide-in-up">
                {uploadRestriction?.blocked ? (
                  <UpgradePrompt 
                    title={uploadRestriction.title}
                    message={uploadRestriction.message}
                    actionText={uploadRestriction.action}
                  />
                ) : (
                  <>
                    {uploadRestriction && !uploadRestriction.blocked && (
                      <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-yellow-800">
                              {uploadRestriction.title}
                            </h3>
                            <p className="mt-1 text-sm text-yellow-700">
                              {uploadRestriction.message}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                    <FileUpload 
                      onFilesUploaded={handleNewUploads}
                      roleRequirements={roleRequirements}
                      aiSettings={aiSettings}
                    />
                  </>
                )}
              </div>
            )}

            {activeTab === 'requirements' && (
              <div className="animate-slide-in-up">
                <RoleRequirements 
                  onRequirementsChange={handleRoleRequirementsChange}
                />
              </div>
            )}

            {activeTab === 'ai-settings' && (
              <div className="animate-slide-in-up">
                <AISettings 
                  onSettingsChange={handleAISettingsChange}
                />
              </div>
            )}
            
            {activeTab === 'dashboard' && (
              <div className="animate-slide-in-up">
                <ModernDashboard 
                  resumes={resumes}
                  roleRequirements={roleRequirements}
                  onClearResumes={handleClearResumes}
                  onExportCSV={handleExportCSV}
                  onRefresh={fetchResumes}
                  isTrialUser={isTrialActive}
                  exportRestriction={getExportRestriction()}
                />
              </div>
            )}

            {activeTab === 'email' && (
              <div className="animate-slide-in-up">
                <EmailManager />
              </div>
            )}

            {activeTab === 'hr-legal' && (
              <div className="animate-slide-in-up">
                <HRLegal />
              </div>
            )}

            {activeTab === 'debug' && (
              <div className="animate-slide-in-up">
                <DebugConsole 
                  apiBaseUrl={API_BASE_URL}
                />
              </div>
            )}
          </div>
        </main>
      </div>
  );
}

export default FullApp;

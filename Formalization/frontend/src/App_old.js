import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import './styles/premium.css';
import './styles/components.css';
import FileUpload from './components/FileUpload';
import ModernDashboard from './components/ModernDashboard';
import RoleRequirements from './components/RoleRequirements';
import EmailManager from './components/EmailManager';
import DebugConsole from './components/DebugConsole';
import AISettings from './components/AISettings';
import HRLegal from './components/HRLegal';
import axios from 'axios';

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
    await axios.post(`${API_BASE_URL}/api/debug/logs`, logEntry);
  } catch (error) {
    console.error('Failed to send debug log to backend:', error);
  }
};

// Make debugLog available globally
window.debugLog = debugLog;

function App() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [roleRequirements, setRoleRequirements] = useState(null);
  const [aiSettings, setAiSettings] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    debugLog('info', 'App component mounted');
    fetchResumes();
    fetchRoleRequirements();
    loadAISettings();
  }, []);

  const loadAISettings = () => {
    const savedSettings = localStorage.getItem('aiSettings');
    if (savedSettings) {
      try {
        setAiSettings(JSON.parse(savedSettings));
      } catch (error) {
        console.error('Error loading AI settings:', error);
      }
    }
  };

  const fetchResumes = async () => {
    try {
      debugLog('info', 'Fetching resumes from backend');
      const response = await axios.get(`${API_BASE_URL}/api/resumes`);
      setResumes(response.data.resumes);
      debugLog('info', `Fetched ${response.data.resumes.length} resumes`);
    } catch (error) {
      debugLog('error', 'Error fetching resumes', error.message);
      console.error('Error fetching resumes:', error);
    }
  };

  const fetchRoleRequirements = async () => {
    try {
      debugLog('info', 'Fetching role requirements');
      const response = await axios.get(`${API_BASE_URL}/api/role-requirements`);
      setRoleRequirements(response.data);
      debugLog('info', 'Role requirements fetched', { hasJobTitle: !!response.data.job_title });
    } catch (error) {
      debugLog('error', 'Error fetching role requirements', error.message);
      console.error('Error fetching role requirements:', error);
    }
  };

  const handleFilesUploaded = async (uploadResults) => {
    setLoading(true);
    try {
      debugLog('info', 'Files uploaded, refreshing data');
      // Refresh the resumes list after upload
      await fetchResumes();
      // Switch to dashboard tab after successful upload
      if (uploadResults.some(result => result.status === 'success')) {
        setActiveTab('dashboard');
        debugLog('info', 'Switched to dashboard after successful upload');
      }
    } catch (error) {
      debugLog('error', 'Error refreshing resumes after upload', error.message);
      console.error('Error refreshing resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearResumes = async () => {
    try {
      debugLog('info', 'Clearing all resumes');
      await axios.delete(`${API_BASE_URL}/api/clear`);
      setResumes([]);
      debugLog('info', 'All resumes cleared successfully');
    } catch (error) {
      debugLog('error', 'Error clearing resumes', error.message);
      console.error('Error clearing resumes:', error);
    }
  };

  const handleRoleRequirementsUpdate = async (requirements) => {
    try {
      debugLog('info', 'Updating role requirements', { job_title: requirements.job_title });
      await axios.post(`${API_BASE_URL}/api/role-requirements`, requirements);
      setRoleRequirements(requirements);
      debugLog('info', 'Role requirements updated successfully');
      
      // Optionally refresh resumes to re-analyze with new requirements
      if (resumes.length > 0) {
        debugLog('info', 'Re-analyzing existing resumes with new role requirements');
        // Note: This would require re-processing, which might be expensive
        // For now, just notify the user
        alert('Role requirements updated! Upload new resumes to see analysis with new criteria.');
      }
    } catch (error) {
      debugLog('error', 'Error updating role requirements', error.message);
      console.error('Error updating role requirements:', error);
    }
  };

  const handleExportCSV = async () => {
    try {
      debugLog('info', 'Exporting resume data as CSV');
      const response = await axios.get(`${API_BASE_URL}/api/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'resume_analysis.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      debugLog('info', 'CSV export completed successfully');
    } catch (error) {
      debugLog('error', 'Error exporting CSV', error.message);
      console.error('Error exporting CSV:', error);
    }
  };

  const handleAISettingsChange = (settings) => {
    setAiSettings(settings);
    debugLog('info', 'AI settings updated', { provider: settings.provider, model: settings.model });
  };

  return (
    <ThemeProvider>
      <div className="App">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          isOpen={sidebarOpen}
          resumes={resumes}
          setSidebarOpen={setSidebarOpen}
        />

        <main className="main-content">
          <div className="content-container">
            {activeTab === 'upload' && (
              <div className="animate-slide-in-up">
                <FileUpload 
                  onFilesUploaded={handleFilesUploaded}
                  loading={loading}
                  aiSettings={aiSettings}
                />
              </div>
            )}

            {activeTab === 'requirements' && (
              <div className="animate-slide-in-up">
                <RoleRequirements 
                  roleRequirements={roleRequirements}
                  onUpdate={handleRoleRequirementsUpdate}
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
    </ThemeProvider>
  );
}

export default App;

import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, MessageSquare, FileSearch, Shield, FileText, RefreshCw } from 'lucide-react';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';
import LegalChat from './LegalChat';
import ComplianceChecker from './ComplianceChecker';
import DocumentGenerator from './DocumentGenerator';
import LegalQueryForm from './LegalQueryForm';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const HRLegal = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  const initializeSystem = useCallback(async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/initialize`);
      if (response.data.success) {
        setSystemStatus(response.data.status);
        setError(null);
      } else {
        setError(response.data.error || 'Failed to initialize system');
      }
    } catch (error) {
      console.error('Failed to initialize system:', error);
      setError('Failed to initialize HR Legal system');
    }
  }, []);

  const checkSystemStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/legal/status`);
      setSystemStatus(response.data);
      setError(null);
      
      // If system is not available, try to initialize it
      if (!response.data.available) {
        await initializeSystem();
      }
    } catch (error) {
      console.error('Failed to check system status:', error);
      setError('Failed to connect to HR Legal system');
      setSystemStatus({ available: false, error: error.message });
    } finally {
      setLoading(false);
    }
  }, [initializeSystem]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/legal/stats`);
      if (response.data.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  useEffect(() => {
    checkSystemStatus();
    fetchStats();
    // Auto-refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [checkSystemStatus, fetchStats]);

  const handleRebuildIndex = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/legal/rebuild-index`);
      if (response.data.success) {
        alert('Legal knowledge base index rebuilt successfully!');
        await checkSystemStatus();
        await fetchStats();
      } else {
        alert(`Failed to rebuild index: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Failed to rebuild index:', error);
      alert(`Error rebuilding index: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/clear-cache`);
      if (response.data.success) {
        alert('Legal system caches cleared successfully!');
        await fetchStats();
      } else {
        alert(`Failed to clear cache: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
      alert(`Error clearing cache: ${error.message}`);
    }
  };

  if (loading && !systemStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center bg-white rounded-2xl shadow-lg border border-gray-200 p-12 max-w-md mx-auto">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Shield size={24} className="text-white" />
          </div>
          <LoadingSpinner size="large" />
          <h3 className="text-xl font-semibold text-gray-900 mt-6 mb-2">Connecting to HR Legal System</h3>
          <p className="text-gray-600">Please wait while we establish connection...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-6">
        <div className="text-center bg-white rounded-2xl shadow-lg border border-gray-200 p-12 max-w-md mx-auto">
          <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <AlertCircle size={32} className="text-red-600" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-3">System Unavailable</h3>
          <p className="text-gray-600 mb-8 leading-relaxed">{error}</p>
          <Button 
            onClick={checkSystemStatus} 
            variant="primary"
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl shadow-lg transition-all duration-200"
          >
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Header Section */}
      <div className="relative overflow-hidden bg-white shadow-sm border-b">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-purple-600/5"></div>
        <div className="relative max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Shield size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  HR Legal Assistant
                </h1>
                <p className="text-gray-600 text-lg mt-1">AI-powered legal guidance for HR professionals</p>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className={`flex items-center gap-3 px-4 py-2 rounded-full text-sm font-medium shadow-sm ${
                systemStatus?.available 
                  ? 'bg-green-50 text-green-700 border border-green-200' 
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                <div className={`w-2.5 h-2.5 rounded-full ${
                  systemStatus?.available ? 'bg-green-500' : 'bg-red-500'
                } animate-pulse`}></div>
                {systemStatus?.available ? 'System Online' : 'System Offline'}
              </div>
              
              {stats && systemStatus?.available && (
                <div className="hidden md:flex items-center gap-4 text-sm text-gray-500">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <span>{stats.agent_stats?.total_queries || 0} Queries</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                    <span>{stats.system_status?.knowledge_base_size || 0} Documents</span>
                  </div>
                </div>
              )}
              
              <Button
                variant="ghost"
                size="sm"
                onClick={checkSystemStatus}
                icon={RefreshCw}
                disabled={loading}
                className="hover:bg-gray-100 transition-colors"
              >
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="flex bg-gray-50/50">
            {[
              { id: 'chat', label: 'Legal Chat', icon: MessageSquare, desc: 'Interactive AI assistance' },
              { id: 'query', label: 'Advanced Query', icon: FileSearch, desc: 'Detailed legal research' },
              { id: 'compliance', label: 'Compliance Check', icon: Shield, desc: 'Verify HR compliance' },
              { id: 'documents', label: 'Documents', icon: FileText, desc: 'Generate legal docs' }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={`flex-1 p-6 text-left transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-white shadow-sm border-b-2 border-blue-500 text-gray-900'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                  }`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      activeTab === tab.id 
                        ? 'bg-blue-100 text-blue-600' 
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      <Icon size={16} />
                    </div>
                    <span className="font-medium">{tab.label}</span>
                  </div>
                  <p className="text-sm text-gray-500 leading-relaxed">{tab.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 pb-12">
        {!systemStatus?.available ? (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12">
            <div className="text-center max-w-md mx-auto">
              <div className="w-20 h-20 bg-gradient-to-r from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Shield size={32} className="text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">System Initialization Required</h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                The HR Legal system needs to be initialized before you can access legal assistance features.
              </p>
              <Button 
                onClick={initializeSystem} 
                variant="primary" 
                disabled={loading}
                className="px-8 py-3 text-lg font-medium bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl shadow-lg transition-all duration-200"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="small" />
                    Initializing System...
                  </div>
                ) : (
                  'Initialize System'
                )}
              </Button>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 min-h-[600px]">
            <div className="p-8">
              {activeTab === 'chat' && <LegalChat />}
              {activeTab === 'query' && <LegalQueryForm />}
              {activeTab === 'compliance' && <ComplianceChecker />}
              {activeTab === 'documents' && <DocumentGenerator />}
            </div>
          </div>
        )}
      </div>

      {/* System Management Actions - Only show when system is available */}
      {systemStatus?.available && (
        <div className="max-w-7xl mx-auto px-6 pb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Management</h3>
            <div className="flex gap-4">
              <Button
                onClick={handleRebuildIndex}
                variant="secondary"
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 rounded-lg transition-colors"
              >
                <RefreshCw size={16} />
                Rebuild Knowledge Index
              </Button>
              <Button
                onClick={handleClearCache}
                variant="secondary"
                className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 rounded-lg transition-colors"
              >
                <AlertCircle size={16} />
                Clear System Cache
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HRLegal;

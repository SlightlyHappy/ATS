import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle2 } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';
import apiClient from '../utils/apiClient';
import { useTrial } from '../contexts/TrialContext';
import { useAuth } from '../contexts/AuthContext';
import UpgradePrompt from './UpgradePrompt';

const FileUpload = ({ onFilesUploaded, loading, aiSettings }) => {
  console.log('🎬 [VERBOSE] FileUpload component rendering with props:', {
    onFilesUploaded: typeof onFilesUploaded,
    loading,
    aiSettings: aiSettings ? {
      isConfigured: aiSettings.isConfigured,
      provider: aiSettings.provider,
      model: aiSettings.model
    } : null
  });
  
  // Validate required props
  if (typeof onFilesUploaded !== 'function') {
    console.error('❌ [VERBOSE] CRITICAL: onFilesUploaded prop is not a function!', {
      received: typeof onFilesUploaded,
      value: onFilesUploaded
    });
    // Provide a fallback to prevent crashes
    onFilesUploaded = () => {
      console.warn('⚠️ [VERBOSE] Fallback onFilesUploaded called - this indicates a prop error');
    };
  }
  
  const [uploadProgress, setUploadProgress] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  
  // Test backend connection on component mount
  React.useEffect(() => {
    const testBackendConnection = async () => {
      try {
        console.log('🏥 [VERBOSE] Testing backend connection...');
        const response = await apiClient.get('/api/health');
        console.log('✅ [VERBOSE] Backend health check successful:', response.data);
        setConnectionStatus('connected');
      } catch (error) {
        console.error('❌ [VERBOSE] Backend health check failed:', error);
        setConnectionStatus('disconnected');
        if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          console.error('🚨 [VERBOSE] Backend server appears to be down or unreachable');
        }
      }
    };
    
    testBackendConnection();
  }, []);
  
  // Get auth context
  console.log('🔐 [VERBOSE] Getting auth context...');
  const { user } = useAuth();
  console.log('🔐 [VERBOSE] Auth user:', user ? { id: user.id, email: user.email } : 'No user');
  
  // Get trial context - always call the hook
  console.log('🎯 [VERBOSE] Getting trial context...');
  const trialContext = useTrial();
  console.log('✅ [VERBOSE] Trial context loaded:', trialContext ? Object.keys(trialContext) : 'null');
  
  // Safely extract trial functions with fallbacks and additional validation
  const safeTrialContext = React.useMemo(() => {
    console.log('🧠 [VERBOSE] Processing trial context in useMemo...');
    console.log('🧠 [VERBOSE] Trial context type:', typeof trialContext);
    console.log('🧠 [VERBOSE] Trial context value:', trialContext);
    
    if (!trialContext || typeof trialContext !== 'object') {
      console.log('⚠️ [VERBOSE] Using fallback trial context (no valid context found)');
      return {
        isTrialActive: false,
        getRemainingAnalyses: () => null,
        getUploadRestriction: () => null,
        incrementUsage: () => {}
      };
    }
    
    console.log('✅ [VERBOSE] Processing valid trial context with keys:', Object.keys(trialContext));
    
    const processedContext = {
      isTrialActive: typeof trialContext.isTrialActive === 'boolean' ? trialContext.isTrialActive : false,
      getRemainingAnalyses: typeof trialContext.getRemainingAnalyses === 'function' ? trialContext.getRemainingAnalyses : () => null,
      getUploadRestriction: typeof trialContext.getUploadRestriction === 'function' ? trialContext.getUploadRestriction : () => null,
      incrementUsage: typeof trialContext.incrementUsage === 'function' ? trialContext.incrementUsage : () => {}
    };
    
    console.log('🧠 [VERBOSE] Processed trial context:', {
      isTrialActive: processedContext.isTrialActive,
      getRemainingAnalyses: typeof processedContext.getRemainingAnalyses,
      getUploadRestriction: typeof processedContext.getUploadRestriction,
      incrementUsage: typeof processedContext.incrementUsage
    });
    
    return processedContext;
  }, [trialContext]);
  
  const { isTrialActive, getRemainingAnalyses, getUploadRestriction, incrementUsage } = safeTrialContext;
  
  console.log('🎯 [VERBOSE] Final trial context values:', { 
    isTrialActive, 
    getRemainingAnalyses: typeof getRemainingAnalyses, 
    getUploadRestriction: typeof getUploadRestriction, 
    incrementUsage: typeof incrementUsage 
  });

  const onDrop = useCallback(async (acceptedFiles) => {
    console.log('🚀 [VERBOSE] onDrop called with files:', acceptedFiles);
    console.log('🚀 [VERBOSE] Files count:', acceptedFiles?.length || 0);
    console.log('🚀 [VERBOSE] Files details:', acceptedFiles?.map(f => ({ name: f.name, size: f.size, type: f.type })));
    
    if (acceptedFiles.length === 0) {
      console.log('❌ [VERBOSE] No files provided, returning early');
      return;
    }

    // Check backend connection first
    if (connectionStatus === 'disconnected') {
      console.log('❌ [VERBOSE] Backend disconnected, cannot upload');
      alert('Backend server is not reachable. Please ensure the server is running on port 8000.');
      return;
    }
    
    if (connectionStatus === 'checking') {
      console.log('❌ [VERBOSE] Backend connection still checking, cannot upload yet');
      alert('Still checking backend connection. Please wait a moment and try again.');
      return;
    }

    // Check if AI settings are configured
    console.log('🔍 [VERBOSE] Checking AI settings:', aiSettings);
    if (!aiSettings || !aiSettings.isConfigured || !aiSettings.provider || !aiSettings.model) {
      console.log('❌ [VERBOSE] AI settings check failed:', {
        aiSettings: !!aiSettings,
        isConfigured: aiSettings?.isConfigured,
        provider: aiSettings?.provider,
        model: aiSettings?.model
      });
      alert('Please configure AI settings first in the AI Settings tab.');
      return;
    }
    
    console.log('✅ [VERBOSE] AI settings check passed');
    
    // Check trial restrictions
    console.log('🔍 [VERBOSE] Checking trial restrictions...');
    console.log('🔍 [VERBOSE] isTrialActive:', isTrialActive);
    console.log('🔍 [VERBOSE] getUploadRestriction type:', typeof getUploadRestriction);
    
    if (isTrialActive && typeof getUploadRestriction === 'function') {
      try {
        const restriction = getUploadRestriction();
        console.log('🔍 [VERBOSE] Trial restriction result:', restriction);
        if (restriction && restriction.blocked) {
          console.log('❌ [VERBOSE] Upload blocked by trial restriction:', restriction.message);
          alert(restriction.message);
          return;
        }
      } catch (error) {
        console.error('❌ [VERBOSE] Error checking trial restriction:', error);
      }
    }
    
    console.log('✅ [VERBOSE] All checks passed, starting upload...');

    setIsUploading(true);
    console.log('📊 [VERBOSE] Setting isUploading to true');
    
    const initialProgress = acceptedFiles.map(file => ({
      file: file.name,
      status: 'uploading',
      message: 'Processing...'
    }));
    console.log('📊 [VERBOSE] Initial progress state:', initialProgress);
    setUploadProgress(initialProgress);

    try {
      console.log('🔨 [VERBOSE] Creating FormData...');
      const formData = new FormData();
      acceptedFiles.forEach((file, index) => {
        console.log(`📎 [VERBOSE] Appending file ${index + 1}:`, {
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified
        });
        formData.append('files', file);
      });

      // Add AI settings to the form data
      console.log('⚙️ [VERBOSE] Adding AI settings to FormData:', aiSettings);
      formData.append('aiSettings', JSON.stringify(aiSettings));

      // Log all FormData entries
      console.log('📋 [VERBOSE] FormData contents:');
      for (let [key, value] of formData.entries()) {
        if (value instanceof File) {
          console.log(`  ${key}: File(${value.name}, ${value.size} bytes)`);
        } else {
          console.log(`  ${key}:`, value);
        }
      }

      console.log('🌐 [VERBOSE] Making upload request to /api/upload...');
      console.log('🌐 [VERBOSE] API client base URL:', apiClient.defaults?.baseURL || 'default');
      
      const startTime = Date.now();
      const response = await apiClient.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes timeout
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`📈 [VERBOSE] Upload progress: ${percentCompleted}% (${progressEvent.loaded}/${progressEvent.total} bytes)`);
        }
      });
      
      const endTime = Date.now();
      console.log(`⏱️ [VERBOSE] Upload request completed in ${endTime - startTime}ms`);
      console.log('✅ [VERBOSE] Upload response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        dataType: typeof response.data,
        dataKeys: response.data ? Object.keys(response.data) : 'No data'
      });
      console.log('📦 [VERBOSE] Full response data:', response.data);
      
      // Safely extract results with fallbacks
      console.log('🔍 [VERBOSE] Processing response data...');
      let results = [];
      if (response && response.data) {
        console.log('🔍 [VERBOSE] Response data exists, checking format...');
        if (Array.isArray(response.data.results)) {
          console.log('✅ [VERBOSE] Found results array in response.data.results');
          results = response.data.results;
        } else if (Array.isArray(response.data)) {
          console.log('✅ [VERBOSE] Response.data is directly an array');
          results = response.data;
        } else {
          console.warn('⚠️ [VERBOSE] Unexpected response format:', response.data);
          console.log('🔍 [VERBOSE] Response data type:', typeof response.data);
          console.log('🔍 [VERBOSE] Response data keys:', Object.keys(response.data));
          results = [{
            filename: 'Unknown',
            status: 'error',
            message: 'Unexpected response format from server'
          }];
        }
      } else {
        console.error('❌ [VERBOSE] No response or response data');
        console.log('🔍 [VERBOSE] Response object:', response);
        results = [{
          filename: 'Unknown',
          status: 'error',
          message: 'No response received from server'
        }];
      }
      
      console.log('📊 [VERBOSE] Final processed results:', results);
      console.log('📊 [VERBOSE] Results count:', results.length);
      
      setUploadProgress(results);
      console.log('✅ [VERBOSE] Upload progress state updated');
      
      onFilesUploaded(results);
      console.log('✅ [VERBOSE] onFilesUploaded callback called');
      
      // Increment trial usage if in trial mode
      if (isTrialActive && Array.isArray(results)) {
        try {
          console.log('📈 [VERBOSE] Incrementing trial usage...');
          console.log('📈 [VERBOSE] Results count for increment:', results.length);
          console.log('📈 [VERBOSE] incrementUsage function type:', typeof incrementUsage);
          console.log('📈 [VERBOSE] incrementUsage function:', incrementUsage);
          if (typeof incrementUsage === 'function') {
            incrementUsage(results.length);
            console.log('✅ [VERBOSE] Trial usage incremented successfully');
          } else {
            console.warn('⚠️ [VERBOSE] incrementUsage is not a function:', typeof incrementUsage);
          }
        } catch (error) {
          console.error('❌ [VERBOSE] Error incrementing trial usage:', error);
        }
      }

    } catch (error) {
      console.error('❌ [VERBOSE] Upload error caught:', error);
      console.error('❌ [VERBOSE] Error name:', error.name);
      console.error('❌ [VERBOSE] Error message:', error.message);
      console.error('❌ [VERBOSE] Error stack:', error.stack);
      
      if (error.response) {
        console.error('❌ [VERBOSE] Error response status:', error.response.status);
        console.error('❌ [VERBOSE] Error response statusText:', error.response.statusText);
        console.error('❌ [VERBOSE] Error response headers:', error.response.headers);
        console.error('❌ [VERBOSE] Error response data:', error.response.data);
      } else if (error.request) {
        console.error('❌ [VERBOSE] Error request (no response received):', error.request);
        console.error('❌ [VERBOSE] Request readyState:', error.request.readyState);
        console.error('❌ [VERBOSE] Request status:', error.request.status);
      } else {
        console.error('❌ [VERBOSE] Error in setting up request:', error.message);
      }
      
      if (error.code) {
        console.error('❌ [VERBOSE] Error code:', error.code);
      }
      
      // Extract error message from response if available
      const errorMessage = error.response?.data?.error || error.message || 'Upload failed';
      console.log('📝 [VERBOSE] Final error message to display:', errorMessage);
      
      const errorProgress = acceptedFiles.map((file, index) => ({
        file: file.name,
        status: 'error',
        message: errorMessage
      }));
      console.log('📊 [VERBOSE] Error progress state:', errorProgress);
      setUploadProgress(errorProgress);
    } finally {
      console.log('🏁 [VERBOSE] Upload process finished, setting isUploading to false');
      setIsUploading(false);
    }
  }, [onFilesUploaded, aiSettings, isTrialActive, getUploadRestriction, incrementUsage, connectionStatus]);

  const {
    getRootProps,
    getInputProps,
    isDragActive
  } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    },
    multiple: true,
    disabled: isUploading || connectionStatus !== 'connected'
  });

  const clearProgress = () => {
    setUploadProgress([]);
  };

  // Get trial information
  const showTrialInfo = isTrialActive;
  const remainingAnalyses = showTrialInfo && typeof getRemainingAnalyses === 'function' ? getRemainingAnalyses() : null;
  const uploadRestriction = showTrialInfo && typeof getUploadRestriction === 'function' ? getUploadRestriction() : null;
  const canUpload = !uploadRestriction?.blocked;

  return (
    <div className="flex flex-col items-center justify-start min-h-[calc(100vh-10rem)] w-full py-8 px-4">
      <div className="w-full max-w-5xl mx-auto space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4 mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-primary mb-2">Resume Upload & Analysis</h1>
          <p className="text-lg text-secondary max-w-2xl mx-auto">
            Transform your hiring process with AI-powered resume screening and intelligent candidate analysis
          </p>
          
          {/* Trial Information */}
          {showTrialInfo && (
            <div className="mt-4 text-sm font-medium">
              <span className={`${remainingAnalyses > 0 ? 'text-blue-500' : 'text-red-500'}`}>
                {remainingAnalyses > 0 
                  ? `Trial Mode: ${remainingAnalyses} analyses remaining` 
                  : 'Trial Mode: Upload limit reached'}
              </span>
            </div>
          )}
        </div>
        
        {/* Upgrade Prompt - Show when trial limit reached */}
        {showTrialInfo && !canUpload && (
          <UpgradePrompt 
            title="Trial Limit Reached"
            message="You've reached the upload limit for your trial account. Upgrade to continue analyzing resumes."
            actionText="Upgrade to Full Access"
          />
        )}

        <Card 
          title="Upload Resume Files" 
          description="Drag & drop or select files for intelligent processing"
          className="mb-8 upload-card animate-slide-up"
        >
        {/* AI Settings Status */}
        {connectionStatus === 'disconnected' && (
          <div className="flex items-center gap-3 p-4 rounded-xl mb-6 text-sm font-medium transition-all duration-300 hover:scale-[1.02] animate-fade-in" style={{
            backgroundColor: 'var(--color-danger-lighter)',
            color: 'var(--color-danger)',
            border: '1px solid var(--color-danger-light)'
          }}>
            <AlertCircle size={18} className="animate-pulse" />
            <span>⚠️ Backend Connection Failed - Check if server is running on port 8000</span>
          </div>
        )}
        
        {connectionStatus === 'checking' && (
          <div className="flex items-center gap-3 p-4 rounded-xl mb-6 text-sm font-medium transition-all duration-300 hover:scale-[1.02] animate-fade-in" style={{
            backgroundColor: 'var(--color-info-lighter)',
            color: 'var(--color-info)',
            border: '1px solid var(--color-info-light)'
          }}>
            <LoadingSpinner size="small" />
            <span>🔍 Checking backend connection...</span>
          </div>
        )}
        
        {connectionStatus === 'connected' && aiSettings && aiSettings.isConfigured && aiSettings.provider && aiSettings.model ? (
          <div className="flex items-center gap-3 p-4 rounded-xl mb-6 text-sm font-medium transition-all duration-300 hover:scale-[1.02] animate-fade-in" style={{
            backgroundColor: 'var(--color-success-lighter)',
            color: 'var(--color-success)',
            border: '1px solid var(--color-success-light)'
          }}>
            <CheckCircle2 size={18} className="animate-bounce-subtle" />
            <span>✅ Backend Connected | AI Provider: {aiSettings.provider?.toUpperCase() || 'UNKNOWN'} - {aiSettings.model || 'No model'}</span>
          </div>
        ) : connectionStatus === 'connected' ? (
          <div className="flex items-center gap-3 p-4 rounded-xl mb-6 text-sm font-medium transition-all duration-300 hover:scale-[1.02] animate-fade-in" style={{
            backgroundColor: 'var(--color-warning-lighter)',
            color: 'var(--color-warning)',
            border: '1px solid var(--color-warning-light)'
          }}>
            <AlertCircle size={18} className="animate-pulse" />
            <span>✅ Backend Connected | ⚠️ AI not configured. Please configure AI settings first.</span>
          </div>
        ) : null}
        
        <div 
          {...getRootProps()} 
          className={`file-upload-container group transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-xl ${
            isDragActive ? 'drag-active scale-[1.05] shadow-2xl' : ''
          } ${
            (connectionStatus !== 'connected' || !aiSettings || !aiSettings.isConfigured || !aiSettings.provider || !aiSettings.model || isUploading) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-primary'
          }`}
          style={{ 
            background: isDragActive ? 'linear-gradient(135deg, var(--color-primary-lighter), var(--color-surface))' : undefined,
            borderWidth: '2px',
            borderStyle: 'dashed',
            borderColor: isDragActive ? 'var(--color-primary)' : 'var(--color-border)',
            borderRadius: '1rem',
            padding: '3rem 2rem',
            minHeight: '300px'
          }}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-8">
            <div className={`upload-icon transition-all duration-500 ${isDragActive ? 'animate-bounce' : 'group-hover:scale-110'}`}>
              {isUploading ? 
                <LoadingSpinner size="large" /> : 
                <Upload size={48} className={`transition-all duration-300 ${isDragActive ? 'text-primary' : 'text-secondary group-hover:text-primary'}`} />
              }
            </div>
            
            {isUploading ? (
              <div className="upload-text text-center animate-pulse">
                <div className="text-xl font-semibold text-primary mb-2">Processing files...</div>
                <div className="text-sm text-secondary">AI is analyzing your documents</div>
              </div>
            ) : isDragActive ? (
              <div className="upload-text text-primary text-center animate-bounce-subtle">
                <div className="text-xl font-semibold mb-2">Drop files here</div>
                <div className="text-sm">Release to upload</div>
              </div>
            ) : (
              <div className="text-center space-y-4 animate-fade-in">
                <div className="upload-text">
                  <div className="text-xl font-semibold text-primary mb-2">
                    {connectionStatus === 'disconnected' ? 
                      'Backend server not connected' :
                      connectionStatus === 'checking' ? 
                        'Checking backend connection...' :
                        (!aiSettings || !aiSettings.isConfigured || !aiSettings.provider || !aiSettings.model) ? 
                          'Configure AI settings first' : 
                          'Upload Resume Files'
                    }
                  </div>
                  <div className="text-sm text-secondary">
                    {connectionStatus === 'disconnected' ? 
                      'Please ensure server is running on port 8000' :
                      connectionStatus === 'checking' ? 
                        'Please wait...' :
                        (!aiSettings || !aiSettings.isConfigured || !aiSettings.provider || !aiSettings.model) ? 
                          'Then return here to upload files' : 
                          'Drag & drop files or click to browse'
                    }
                  </div>
                </div>
                <div className="upload-subtext">
                  <div className="flex flex-wrap justify-center gap-2 text-xs text-tertiary">
                    <span className="px-2 py-1 bg-surface rounded-full">PDF</span>
                    <span className="px-2 py-1 bg-surface rounded-full">DOCX</span>
                    <span className="px-2 py-1 bg-surface rounded-full">Images</span>
                  </div>
                </div>
              </div>
            )}
            
            {!isUploading && (
              <Button 
                variant="primary"
                size="lg"
                disabled={isUploading || connectionStatus !== 'connected' || !aiSettings || !aiSettings.isConfigured || !aiSettings.provider || !aiSettings.model}
                icon={Upload}
                className="transition-all duration-300 hover:scale-105 hover:shadow-lg"
              >
                {connectionStatus === 'disconnected' ? 'Backend Disconnected' :
                 connectionStatus === 'checking' ? 'Checking Connection...' :
                 'Choose Files'}
              </Button>
            )}
          </div>
        </div>
        </Card>

        {uploadProgress.length > 0 && (
          <Card 
            title="Upload Results"
            className="animate-slide-up"
            action={
              <Button 
                variant="secondary" 
                size="sm"
                onClick={clearProgress}
                className="transition-all duration-200 hover:scale-105"
              >
                Clear
              </Button>
            }
          >
            <div className="space-y-3">
              {uploadProgress.map((item, index) => (
                <div 
                  key={index} 
                  className="flex items-start justify-between p-5 rounded-xl border bg-surface transition-all duration-300 hover:bg-surface-hover hover:scale-[1.01] hover:shadow-md animate-fade-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-primary mb-2 text-lg">
                      {item.filename || item.file}
                    </div>
                    {item.message && (
                      <div className="text-sm text-secondary mb-2 opacity-80">
                        {item.message}
                      </div>
                    )}
                    {item.analysis && item.analysis.parsed_info && item.analysis.parsed_info.name && (
                      <div className="text-sm font-medium animate-fade-in" style={{ color: 'var(--color-success)' }}>
                        ✨ Candidate: {item.analysis.parsed_info.name}
                      </div>
                    )}
                  </div>
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300 hover:scale-110 ${
                    item.status === 'success' ? 'text-success animate-bounce-subtle' :
                    item.status === 'error' ? 'text-danger animate-shake' :
                    'text-secondary animate-pulse'
                  }`} style={{
                    backgroundColor: 
                      item.status === 'success' ? 'var(--color-success-light)' :
                      item.status === 'error' ? 'var(--color-danger-light)' :
                      'var(--color-surface)'
                  }}>
                    {item.status === 'success' ? <CheckCircle2 size={20} /> : 
                     item.status === 'error' ? <AlertCircle size={20} /> : 
                     item.status === 'uploading' ? <LoadingSpinner size="small" /> : <FileText size={20} />}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

      <Card 
        title="Quick Guidelines" 
        className="animate-slide-up max-w-3xl mx-auto"
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3 p-4 rounded-lg bg-surface hover:bg-surface-hover transition-all duration-200 animate-fade-in">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white text-sm font-semibold">
              📄
            </div>
            <div>
              <div className="font-medium text-primary text-sm">File Types</div>
              <div className="text-xs text-secondary">PDF, DOCX, Images</div>
            </div>
          </div>
          
          <div className="flex items-center gap-3 p-4 rounded-lg bg-surface hover:bg-surface-hover transition-all duration-200 animate-fade-in" style={{ animationDelay: '50ms' }}>
            <div className="w-8 h-8 bg-success rounded-lg flex items-center justify-center text-white text-sm font-semibold">
              📊
            </div>
            <div>
              <div className="font-medium text-primary text-sm">Size Limit</div>
              <div className="text-xs text-secondary">Max 16MB</div>
            </div>
          </div>
        
          
          <div className="flex items-center gap-3 p-4 rounded-lg bg-surface hover:bg-surface-hover transition-all duration-200 animate-fade-in" style={{ animationDelay: '150ms' }}>
            <div className="w-8 h-8 bg-info rounded-lg flex items-center justify-center text-white text-sm font-semibold">
              🔒
            </div>
            <div>
              <div className="font-medium text-primary text-sm">Privacy</div>
              <div className="text-xs text-secondary">100% Local (if using Ollama)</div>
            </div>
          </div>
        </div>
      </Card>
      </div>
    </div>
  );
};

export default FileUpload;
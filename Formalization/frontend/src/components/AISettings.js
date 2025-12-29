import React, { useState, useEffect } from 'react';
import { 
  Check, AlertCircle, Zap, Shield, Globe, 
  Brain, Key, TestTube, Save, ExternalLink,
  Sparkles, Lock, Rocket, Star, Clock, Activity
} from 'lucide-react';
import Card from './Card';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';

const AISettings = ({ onSettingsChange }) => {
  const [aiProvider, setAiProvider] = useState('ollama');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showAdminView, setShowAdminView] = useState(false);
  const [storedKeys, setStoredKeys] = useState([]);

  // Available models for each provider
  const modelOptions = {
    ollama: [
      { value: 'llama3', label: 'Llama 3 (8B)', description: 'General purpose, good balance' },
      { value: 'qwen2.5:7b', label: 'Qwen 2.5 (7B)', description: 'Optimized for analysis' },
      { value: 'llama3.1', label: 'Llama 3.1 (8B)', description: 'Latest version' },
      { value: 'mistral', label: 'Mistral 7B', description: 'Fast and efficient' },
      { value: 'codellama', label: 'Code Llama', description: 'Technical resume analysis' }
    ],
    openai: [
      { value: 'gpt-4o', label: 'GPT-4o', description: 'Most capable, expensive' },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini', description: 'Balanced performance' },
      { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', description: 'Fast and cost-effective' }
    ],
    gemini: [
      { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', description: 'Most capable' },
      { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', description: 'Fast and efficient' },
      { value: 'gemini-pro', label: 'Gemini Pro', description: 'Balanced performance' }
    ]
  };

  // Default models for each provider
  const defaultModels = {
    ollama: 'qwen2.5:7b',
    openai: 'gpt-4o-mini',
    gemini: 'gemini-1.5-flash'
  };

  useEffect(() => {
    // Load saved settings from localStorage (without API keys)
    const savedSettings = localStorage.getItem('aiSettings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        setAiProvider(settings.provider || 'ollama');
        setModel(settings.model || defaultModels[settings.provider] || defaultModels.ollama);
        setIsConfigured(settings.isConfigured || false);
        // Don't load API key from localStorage - keys are stored securely on backend
      } catch (error) {
        console.error('Error loading AI settings:', error);
      }
    } else {
      // Set default model for ollama
      setModel(defaultModels.ollama);
    }
  }, []);

  useEffect(() => {
    // Set default model when provider changes
    if (aiProvider && !model) {
      setModel(defaultModels[aiProvider]);
    }
  }, [aiProvider]);

  const handleProviderChange = (provider) => {
    setAiProvider(provider);
    setModel(defaultModels[provider]);
    setApiKey('');
    setIsConfigured(false);
    setTestResult(null);
  };

  const handleModelChange = (selectedModel) => {
    setModel(selectedModel);
    setIsConfigured(false);
    setTestResult(null);
  };

  const handleApiKeyChange = (key) => {
    setApiKey(key);
    setIsConfigured(false);
    setTestResult(null);
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setShowAdminView(false);
    setStoredKeys([]);

    try {
      const settings = {
        provider: aiProvider,
        apiKey: aiProvider !== 'ollama' ? apiKey : '',
        model: model
      };

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/test-ai`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      const result = await response.json();
      
      if (response.ok) {
        if (result.admin_view) {
          setShowAdminView(true);
          setStoredKeys(result.stored_keys || []);
          setTestResult({ success: true, message: 'Admin access granted! Stored keys displayed below.' });
        } else {
          setTestResult({ success: true, message: 'Connection successful!' });
          setIsConfigured(true);
          saveSettings(settings);
        }
      } else {
        setTestResult({ success: false, message: result.error || 'Connection failed' });
        setIsConfigured(false);
      }
    } catch (error) {
      setTestResult({ success: false, message: `Error: ${error.message}` });
      setIsConfigured(false);
    } finally {
      setTesting(false);
    }
  };

  const saveSettings = (settings) => {
    const settingsToSave = {
      provider: settings.provider,
      model: settings.model,
      isConfigured: true
      // Don't save API keys - they are stored securely on backend
    };
    
    localStorage.setItem('aiSettings', JSON.stringify(settingsToSave));
    onSettingsChange(settingsToSave);
  };

  const handleSaveSettings = () => {
    const settings = {
      provider: aiProvider,
      apiKey: aiProvider !== 'ollama' ? apiKey : '',
      model: model,
      isConfigured: isConfigured
    };
    
    saveSettings(settings);
  };

  const requiresApiKey = aiProvider !== 'ollama';

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      gap: 'var(--spacing-xl)',
      maxWidth: '1200px',
      margin: '0 auto',
      width: '100%',
      padding: 'var(--spacing-lg)',
      background: 'linear-gradient(135deg, var(--color-surface) 0%, var(--color-surface-elevated) 100%)',
      minHeight: '100vh'
    }}>
      {/* Header Section */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 'var(--spacing-xl)',
        position: 'relative',
        animation: 'fadeInUp 0.6s ease-out'
      }}>
        <div style={{
          position: 'absolute',
          top: '-20px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100px',
          height: '4px',
          background: 'linear-gradient(90deg, var(--color-primary), var(--color-primary-light))',
          borderRadius: '2px',
          animation: 'slideIn 0.8s ease-out'
        }}></div>
        
        <h1 style={{ 
          fontSize: '2.75rem', 
          fontWeight: '800', 
          color: 'var(--color-text-primary)', 
          marginBottom: 'var(--spacing-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--spacing-md)',
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          <div style={{
            padding: 'var(--spacing-sm)',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'pulse 2s infinite'
          }}>
            <Brain size={36} />
          </div>
          AI Configuration
        </h1>
        <p style={{ 
          color: 'var(--color-text-secondary)', 
          fontSize: '1.25rem',
          fontWeight: '400',
          maxWidth: '600px',
          margin: '0 auto',
          lineHeight: '1.6'
        }}>
          Choose your AI provider and model for intelligent resume analysis
        </p>
      </div>

      <Card title="AI Provider" subtitle="Select your preferred AI service for resume analysis">
        <div style={{ display: 'grid', gap: 'var(--spacing-lg)' }}>
          {/* Ollama Option */}
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-lg)',
              padding: 'var(--spacing-lg)',
              border: `2px solid ${aiProvider === 'ollama' ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-lg)',
              backgroundColor: aiProvider === 'ollama' ? 'var(--color-primary-light)' : 'transparent',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
            onClick={() => handleProviderChange('ollama')}
          >
            <input
              type="radio"
              value="ollama"
              checked={aiProvider === 'ollama'}
              onChange={() => handleProviderChange('ollama')}
              style={{ marginRight: 0 }}
            />
            <div style={{
              padding: 'var(--spacing-md)',
              borderRadius: '50%',
              backgroundColor: 'var(--color-success-light)',
              color: 'var(--color-success)'
            }}>
              <Shield size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: '600', 
                color: 'var(--color-text-primary)', 
                marginBottom: 'var(--spacing-xs)' 
              }}>
                Ollama (Local)
              </div>
              <div style={{ 
                color: 'var(--color-text-secondary)', 
                fontSize: '0.875rem' 
              }}>
                Free, private, runs on your computer
              </div>
            </div>
          </div>

          {/* OpenAI Option */}
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-lg)',
              padding: 'var(--spacing-lg)',
              border: `2px solid ${aiProvider === 'openai' ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-lg)',
              backgroundColor: aiProvider === 'openai' ? 'var(--color-primary-light)' : 'transparent',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
            onClick={() => handleProviderChange('openai')}
          >
            <input
              type="radio"
              value="openai"
              checked={aiProvider === 'openai'}
              onChange={() => handleProviderChange('openai')}
              style={{ marginRight: 0 }}
            />
            <div style={{
              padding: 'var(--spacing-md)',
              borderRadius: '50%',
              backgroundColor: 'var(--color-primary-light)',
              color: 'var(--color-primary)'
            }}>
              <Zap size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: '600', 
                color: 'var(--color-text-primary)', 
                marginBottom: 'var(--spacing-xs)' 
              }}>
                OpenAI
              </div>
              <div style={{ 
                color: 'var(--color-text-secondary)', 
                fontSize: '0.875rem' 
              }}>
                Most capable, requires API key and credits
              </div>
            </div>
          </div>

          {/* Gemini Option */}
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-lg)',
              padding: 'var(--spacing-lg)',
              border: `2px solid ${aiProvider === 'gemini' ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-lg)',
              backgroundColor: aiProvider === 'gemini' ? 'var(--color-primary-light)' : 'transparent',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)'
            }}
            onClick={() => handleProviderChange('gemini')}
          >
            <input
              type="radio"
              value="gemini"
              checked={aiProvider === 'gemini'}
              onChange={() => handleProviderChange('gemini')}
              style={{ marginRight: 0 }}
            />
            <div style={{
              padding: 'var(--spacing-md)',
              borderRadius: '50%',
              backgroundColor: 'var(--color-warning-light)',
              color: 'var(--color-warning)'
            }}>
              <Globe size={24} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: '600', 
                color: 'var(--color-text-primary)', 
                marginBottom: 'var(--spacing-xs)' 
              }}>
                Google Gemini
              </div>
              <div style={{ 
                color: 'var(--color-text-secondary)', 
                fontSize: '0.875rem' 
              }}>
                Fast and efficient, requires API key
              </div>
            </div>
          </div>
        </div>
      </Card>

      <Card title="Model Selection" subtitle="Choose the specific AI model for your analysis">
        <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
          <select 
            value={model} 
            onChange={(e) => handleModelChange(e.target.value)}
            style={{
              width: '100%',
              padding: 'var(--spacing-md)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              fontSize: '1rem'
            }}
          >
            {modelOptions[aiProvider]?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <p style={{ 
            color: 'var(--color-text-secondary)', 
            fontSize: '0.875rem',
            fontStyle: 'italic' 
          }}>
            {modelOptions[aiProvider]?.find(opt => opt.value === model)?.description}
          </p>
        </div>
      </Card>

      {requiresApiKey && (
        <Card 
          title="API Key" 
          subtitle={`Enter your ${aiProvider === 'openai' ? 'OpenAI' : 'Google'} API key`}
        >
          <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              placeholder={`Enter your ${aiProvider} API key`}
              style={{
                width: '100%',
                padding: 'var(--spacing-md)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: '1rem'
              }}
            />
            <p style={{ 
              color: 'var(--color-text-secondary)', 
              fontSize: '0.875rem' 
            }}>
              {aiProvider === 'openai' && (
                <>Get your API key from <a 
                  href="https://platform.openai.com/api-keys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ color: 'var(--color-primary)', textDecoration: 'none' }}
                >OpenAI Platform</a></>
              )}
              {aiProvider === 'gemini' && (
                <>Get your API key from <a 
                  href="https://makersuite.google.com/app/apikey" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ color: 'var(--color-primary)', textDecoration: 'none' }}
                >Google AI Studio</a></>
              )}
            </p>
          </div>
        </Card>
      )}

      <Card title="Configuration" subtitle="Test and save your AI settings">
        <div style={{ display: 'grid', gap: 'var(--spacing-lg)' }}>
          <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
            <Button
              variant="primary"
              loading={testing}
              disabled={testing || (requiresApiKey && !apiKey)}
              onClick={testConnection}
              icon={testing ? undefined : Check}
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </Button>
            
            <Button
              variant="outline"
              disabled={!isConfigured}
              onClick={handleSaveSettings}
            >
              Save Settings
            </Button>
          </div>

          {testResult && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: testResult.success ? 'var(--color-success-light)' : 'var(--color-danger-light)',
              color: testResult.success ? 'var(--color-success)' : 'var(--color-danger)',
              border: `1px solid ${testResult.success ? 'var(--color-success)' : 'var(--color-danger)'}`,
              fontWeight: '500'
            }}>
              {testResult.success ? <Check size={16} /> : <AlertCircle size={16} />}
              {testResult.message}
            </div>
          )}

          {showAdminView && (
            <div style={{
              padding: 'var(--spacing-lg)',
              backgroundColor: 'var(--color-warning-light)',
              border: `2px solid var(--color-warning)`,
              borderRadius: 'var(--radius-lg)',
              color: 'var(--color-warning)'
            }}>
              <h4 style={{ 
                marginBottom: 'var(--spacing-md)', 
                color: 'var(--color-warning)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-sm)'
              }}>
                🔐 Admin View - Stored API Keys
              </h4>
              {storedKeys.length > 0 ? (
                <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
                  {storedKeys.map((keyInfo, index) => (
                    <div 
                      key={index} 
                      style={{
                        backgroundColor: 'var(--color-surface-elevated)',
                        padding: 'var(--spacing-md)',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--color-border)'
                      }}
                    >
                      <div style={{ 
                        fontWeight: '600', 
                        color: 'var(--color-text-primary)',
                        marginBottom: 'var(--spacing-xs)' 
                      }}>
                        {keyInfo.provider} - {keyInfo.model}
                      </div>
                      <div style={{
                        fontFamily: 'monospace',
                        backgroundColor: 'var(--color-surface)',
                        padding: 'var(--spacing-sm)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.75rem',
                        wordBreak: 'break-all',
                        marginBottom: 'var(--spacing-xs)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-primary)'
                      }}>
                        {keyInfo.api_key}
                      </div>
                      <div style={{ 
                        fontSize: '0.75rem', 
                        color: 'var(--color-text-secondary)' 
                      }}>
                        Stored: {new Date(keyInfo.stored_at).toLocaleString()} | 
                        Used: {keyInfo.usage_count} times | 
                        Last: {keyInfo.last_used !== 'Never' ? new Date(keyInfo.last_used).toLocaleString() : 'Never'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--color-text-secondary)' }}>No API keys stored yet.</p>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card title="Provider Information" subtitle="Learn more about each AI provider option">
        <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
          <div style={{
            padding: 'var(--spacing-md)',
            backgroundColor: 'var(--color-surface)',
            borderRadius: 'var(--radius-md)',
            borderLeft: '4px solid var(--color-success)'
          }}>
            <div style={{ fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
              Ollama
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Free, private, runs locally. Requires Ollama installation.
            </div>
          </div>
          
          <div style={{
            padding: 'var(--spacing-md)',
            backgroundColor: 'var(--color-surface)',
            borderRadius: 'var(--radius-md)',
            borderLeft: '4px solid var(--color-primary)'
          }}>
            <div style={{ fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
              OpenAI
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Most capable models, pay-per-use. Requires internet connection.
            </div>
          </div>
          
          <div style={{
            padding: 'var(--spacing-md)',
            backgroundColor: 'var(--color-surface)',
            borderRadius: 'var(--radius-md)',
            borderLeft: '4px solid var(--color-warning)'
          }}>
            <div style={{ fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
              Gemini
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Google's AI, competitive pricing. Requires internet connection.
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AISettings;

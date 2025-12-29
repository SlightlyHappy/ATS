import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './DebugConsole.css';

const DebugConsole = ({ apiBaseUrl }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    source: '',
    level: '',
    limit: 100
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const logsEndRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchLogs();
    
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 3000); // Refresh every 3 seconds
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [filters, autoRefresh]);

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    scrollToBottom();
  }, [logs]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.source) params.append('source', filters.source);
      if (filters.level) params.append('level', filters.level);
      params.append('limit', filters.limit.toString());

      const response = await axios.get(`${apiBaseUrl}/api/debug/logs?${params}`);
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Error fetching debug logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    try {
      await axios.delete(`${apiBaseUrl}/api/debug/logs`);
      setLogs([]);
      window.debugLog('info', 'Debug logs cleared from console');
    } catch (error) {
      console.error('Error clearing debug logs:', error);
    }
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return '#e74c3c';
      case 'warning': return '#f39c12';
      case 'info': return '#3498db';
      case 'debug': return '#95a5a6';
      default: return '#2c3e50';
    }
  };

  const getSourceColor = (source) => {
    switch (source) {
      case 'backend': return '#27ae60';
      case 'frontend': return '#8e44ad';
      default: return '#34495e';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  const addTestLog = async (level) => {
    const testMessages = {
      info: 'Test info message from frontend',
      warning: 'Test warning message from frontend',
      error: 'Test error message from frontend',
      debug: 'Test debug message from frontend'
    };

    await window.debugLog(level, testMessages[level], { test: true, timestamp: Date.now() });
    fetchLogs(); // Refresh immediately after adding test log
  };

  return (
    <div className="debug-console">
      <div className="console-header">
        <h2>Debug Console</h2>
        <p>Real-time logs from frontend and backend</p>
      </div>

      <div className="console-controls">
        <div className="filters">
          <div className="filter-group">
            <label>Source:</label>
            <select 
              value={filters.source} 
              onChange={(e) => handleFilterChange('source', e.target.value)}
            >
              <option value="">All Sources</option>
              <option value="frontend">Frontend</option>
              <option value="backend">Backend</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Level:</label>
            <select 
              value={filters.level} 
              onChange={(e) => handleFilterChange('level', e.target.value)}
            >
              <option value="">All Levels</option>
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Limit:</label>
            <select 
              value={filters.limit} 
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
            >
              <option value={50}>50 logs</option>
              <option value={100}>100 logs</option>
              <option value={200}>200 logs</option>
              <option value={500}>500 logs</option>
            </select>
          </div>
        </div>

        <div className="console-actions">
          <button 
            className="btn-toggle"
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{ backgroundColor: autoRefresh ? '#27ae60' : '#95a5a6' }}
          >
            {autoRefresh ? '⏸️ Pause' : '▶️ Auto-refresh'}
          </button>
          
          <button onClick={fetchLogs} className="btn-refresh" disabled={loading}>
            🔄 Refresh
          </button>
          
          <button onClick={clearLogs} className="btn-clear">
            🗑️ Clear
          </button>
          
          <button onClick={scrollToBottom} className="btn-scroll">
            ⬇️ Bottom
          </button>
        </div>
      </div>

      <div className="test-controls">
        <span>Test logs:</span>
        <button onClick={() => addTestLog('debug')} className="test-btn debug">Debug</button>
        <button onClick={() => addTestLog('info')} className="test-btn info">Info</button>
        <button onClick={() => addTestLog('warning')} className="test-btn warning">Warning</button>
        <button onClick={() => addTestLog('error')} className="test-btn error">Error</button>
      </div>

      <div className="logs-container">
        {loading && (
          <div className="loading-indicator">
            Loading logs...
          </div>
        )}
        
        {logs.length === 0 && !loading && (
          <div className="no-logs">
            No logs available. Upload some resumes or interact with the app to generate logs.
          </div>
        )}

        {logs.map((log, index) => (
          <div key={index} className={`log-entry level-${log.level}`}>
            <div className="log-header">
              <span 
                className="log-timestamp"
                title={log.timestamp}
              >
                {formatTimestamp(log.timestamp)}
              </span>
              <span 
                className="log-source" 
                style={{ backgroundColor: getSourceColor(log.source) }}
              >
                {log.source}
              </span>
              <span 
                className="log-level" 
                style={{ backgroundColor: getLevelColor(log.level) }}
              >
                {log.level.toUpperCase()}
              </span>
            </div>
            <div className="log-message">
              {log.message}
            </div>
            {log.data && (
              <div className="log-data">
                <pre>{JSON.stringify(log.data, null, 2)}</pre>
              </div>
            )}
          </div>
        ))}
        
        <div ref={logsEndRef} />
      </div>

      <div className="console-stats">
        <span>Total logs: {logs.length}</span>
        <span>Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}</span>
        <span>Last updated: {new Date().toLocaleTimeString()}</span>
      </div>
    </div>
  );
};

export default DebugConsole;

import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LegalQueryForm = () => {
  const [query, setQuery] = useState('');
  const [config, setConfig] = useState({
    response_length: 'medium',
    custom_word_count: '',
    response_style: 'professional',
    detail_level: 'balanced',
    audience_level: 'intermediate',
    include_citations: true,
    include_confidence: true,
    show_reasoning: false,
    include_follow_ups: true,
    include_examples: true,
    structured_output: true,
    retrieval_depth: 5,
    similarity_threshold: 0.7
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a legal question');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/query`, {
        question: query.trim(),
        config: config,
        user_role: 'hr_professional',
        urgency: 'normal'
      });

      if (response.data.success) {
        setResult(response.data.response);
      } else {
        throw new Error(response.data.error || 'Query processing failed');
      }
    } catch (error) {
      console.error('Query error:', error);
      setError(error.response?.data?.error || error.message || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    setQuery('');
    setResult(null);
    setError(null);
  };

  const loadSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  const formatResponse = (content) => {
    if (!content) return '';
    
    return content
      .replace(/^\d+\.\s/gm, '• ')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .split('\n')
      .map((line, index) => (
        <div key={index} dangerouslySetInnerHTML={{ __html: line }} />
      ));
  };

  const sampleQueries = [
    "What are the mandatory benefits an employer must provide to employees in India?",
    "How should we handle employee grievances to ensure legal compliance?",
    "What are the legal requirements for conducting employee background checks?",
    "What documentation is required for employee termination in India?",
    "How can we ensure our performance evaluation process is legally compliant?",
    "What are the legal considerations for implementing a work-from-home policy?"
  ];

  return (
    <div className="legal-query-form">
      <div className="query-header">
        <h3>Advanced Legal Query</h3>
        <p>Get detailed legal analysis with customizable response parameters</p>
      </div>

      <form onSubmit={handleSubmit} className="query-form">
        <div className="form-group">
          <label htmlFor="query">Legal Question:</label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your detailed legal question here..."
            rows={4}
            className="query-textarea"
            required
          />
          <div className="character-count">
            {query.length} characters
          </div>
        </div>

        <div className="sample-queries">
          <h4>Sample Questions:</h4>
          <div className="sample-buttons">
            {sampleQueries.map((sampleQuery, index) => (
              <button
                key={index}
                type="button"
                onClick={() => loadSampleQuery(sampleQuery)}
                className="sample-query-btn"
              >
                {sampleQuery}
              </button>
            ))}
          </div>
        </div>

        <div className="config-panel">
          <h4>Response Configuration</h4>
          
          <div className="config-grid">
            <div className="config-group">
              <label>Response Length:</label>
              <select
                value={config.response_length}
                onChange={(e) => handleConfigChange('response_length', e.target.value)}
              >
                <option value="short">Short (100-200 words)</option>
                <option value="medium">Medium (300-500 words)</option>
                <option value="long">Long (600-1000 words)</option>
                <option value="comprehensive">Comprehensive (1000+ words)</option>
                <option value="custom">Custom Word Count</option>
              </select>
              {config.response_length === 'custom' && (
                <input
                  type="number"
                  placeholder="Word count"
                  value={config.custom_word_count}
                  onChange={(e) => handleConfigChange('custom_word_count', parseInt(e.target.value))}
                  min="50"
                  max="2000"
                />
              )}
            </div>

            <div className="config-group">
              <label>Response Style:</label>
              <select
                value={config.response_style}
                onChange={(e) => handleConfigChange('response_style', e.target.value)}
              >
                <option value="professional">Professional</option>
                <option value="conversational">Conversational</option>
                <option value="technical">Technical</option>
                <option value="legal">Legal (Formal)</option>
                <option value="educational">Educational</option>
              </select>
            </div>

            <div className="config-group">
              <label>Detail Level:</label>
              <select
                value={config.detail_level}
                onChange={(e) => handleConfigChange('detail_level', e.target.value)}
              >
                <option value="overview">Overview</option>
                <option value="balanced">Balanced</option>
                <option value="detailed">Detailed</option>
                <option value="comprehensive">Comprehensive</option>
              </select>
            </div>

            <div className="config-group">
              <label>Audience Level:</label>
              <select
                value={config.audience_level}
                onChange={(e) => handleConfigChange('audience_level', e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>
            </div>

            <div className="config-group">
              <label>Retrieval Depth:</label>
              <input
                type="range"
                min="3"
                max="10"
                value={config.retrieval_depth}
                onChange={(e) => handleConfigChange('retrieval_depth', parseInt(e.target.value))}
              />
              <span>{config.retrieval_depth} sources</span>
            </div>

            <div className="config-group">
              <label>Similarity Threshold:</label>
              <input
                type="range"
                min="0.5"
                max="0.9"
                step="0.1"
                value={config.similarity_threshold}
                onChange={(e) => handleConfigChange('similarity_threshold', parseFloat(e.target.value))}
              />
              <span>{(config.similarity_threshold * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="config-checkboxes">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.include_citations}
                onChange={(e) => handleConfigChange('include_citations', e.target.checked)}
              />
              Include Citations
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.include_confidence}
                onChange={(e) => handleConfigChange('include_confidence', e.target.checked)}
              />
              Show Confidence Score
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.show_reasoning}
                onChange={(e) => handleConfigChange('show_reasoning', e.target.checked)}
              />
              Show Reasoning Chain
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.include_follow_ups}
                onChange={(e) => handleConfigChange('include_follow_ups', e.target.checked)}
              />
              Include Follow-up Questions
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.include_examples}
                onChange={(e) => handleConfigChange('include_examples', e.target.checked)}
              />
              Include Case Examples
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={config.structured_output}
                onChange={(e) => handleConfigChange('structured_output', e.target.checked)}
              />
              Structured Output
            </label>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="submit-button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              '🔍 Analyze Query'
            )}
          </button>
          <button
            type="button"
            onClick={clearForm}
            className="clear-button"
          >
            🗑️ Clear
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {result && (
        <div className="query-result">
          <div className="result-header">
            <h4>📋 Legal Analysis</h4>
            <div className="result-meta">
              {result.metadata && (
                <>
                  <span>Confidence: {(result.metadata.confidence_score * 100).toFixed(1)}%</span>
                  <span>Sources: {result.metadata.sources_used || 0}</span>
                  <span>Processing Time: {result.metadata.processing_time || 0}s</span>
                </>
              )}
            </div>
          </div>

          <div className="response-content">
            {formatResponse(result.content)}
          </div>

          {result.reasoning_chain && config.show_reasoning && (
            <div className="reasoning-chain">
              <h5>🧠 Reasoning Chain:</h5>
              <div className="reasoning-steps">
                {result.reasoning_chain.map((step, index) => (
                  <div key={index} className="reasoning-step">
                    <strong>Step {index + 1}:</strong> {step}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.citations && result.citations.length > 0 && (
            <div className="result-citations">
              <h5>📚 Legal References:</h5>
              <ul>
                {result.citations.map((citation, index) => (
                  <li key={index}>
                    <strong>{citation.title}</strong>
                    {citation.relevance_score && (
                      <span className="relevance-score">
                        (Relevance: {(citation.relevance_score * 100).toFixed(1)}%)
                      </span>
                    )}
                    {citation.content_snippet && (
                      <div className="citation-snippet">
                        "{citation.content_snippet}"
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.follow_up_questions && result.follow_up_questions.length > 0 && (
            <div className="result-follow-ups">
              <h5>❓ Follow-up Questions:</h5>
              <div className="follow-up-list">
                {result.follow_up_questions.map((question, index) => (
                  <button
                    key={index}
                    className="follow-up-item"
                    onClick={() => loadSampleQuery(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="result-actions">
            <button
              onClick={() => {
                const reportContent = `LEGAL ANALYSIS REPORT\n\n` +
                  `Query: ${query}\n\n` +
                  `Analysis Date: ${new Date().toLocaleDateString()}\n\n` +
                  `RESPONSE:\n${result.content}\n\n` +
                  (result.citations ? `LEGAL REFERENCES:\n${result.citations.map(c => `- ${c.title}`).join('\n')}\n\n` : '') +
                  (result.follow_up_questions ? `FOLLOW-UP QUESTIONS:\n${result.follow_up_questions.map((q, i) => `${i+1}. ${q}`).join('\n')}\n\n` : '') +
                  `Configuration Used:\n` +
                  `- Response Length: ${config.response_length}\n` +
                  `- Style: ${config.response_style}\n` +
                  `- Detail Level: ${config.detail_level}\n` +
                  `- Audience: ${config.audience_level}`;
                
                const blob = new Blob([reportContent], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `legal-analysis-${Date.now()}.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="download-button"
            >
              📥 Download Analysis
            </button>
            
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.content)
                  .then(() => alert('Analysis copied to clipboard!'))
                  .catch(() => alert('Failed to copy to clipboard'));
              }}
              className="copy-button"
            >
              📋 Copy Response
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LegalQueryForm;

import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ComplianceChecker = () => {
  const [content, setContent] = useState('');
  const [contentType, setContentType] = useState('job_description');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const contentTypes = {
    job_description: 'Job Description',
    employment_contract: 'Employment Contract',
    hr_policy: 'HR Policy',
    termination_letter: 'Termination Letter',
    offer_letter: 'Offer Letter',
    general: 'General Document'
  };

  const sampleContent = {
    job_description: `Software Engineer - Full Stack Developer

Company: TechCorp India Pvt Ltd
Location: Bangalore, Karnataka

Job Requirements:
- Bachelor's degree in Computer Science or related field
- 3+ years of experience in full-stack development
- Proficiency in React, Node.js, and databases
- Must be willing to work flexible hours including weekends
- Age preference: 22-30 years
- Unmarried candidates preferred

Responsibilities:
- Develop and maintain web applications
- Collaborate with cross-functional teams
- Participate in code reviews and testing

Compensation: Competitive salary based on experience`,

    employment_contract: `EMPLOYMENT AGREEMENT

This Employment Agreement is entered into between TechCorp India Pvt Ltd and [Employee Name].

TERMS AND CONDITIONS:
1. Position: Software Developer
2. Salary: Rs. 8,00,000 per annum
3. Working Hours: 9 AM to 6 PM, Monday to Friday
4. Probation Period: 6 months
5. Notice Period: 30 days

ADDITIONAL CLAUSES:
- Employee agrees to work overtime without additional compensation when required
- Employee cannot join any competitor for 2 years after leaving
- All personal devices may be searched by company security
- Employee's family information must be provided for security clearance

[Signature blocks]`,

    hr_policy: `LEAVE POLICY

Annual Leave Entitlement:
- All employees are entitled to 12 days of annual leave
- Leave can only be taken with 30 days advance notice
- No carry forward of unused leave allowed
- Medical emergencies require 7 days advance notice
- Female employees get additional 3 days leave per month

Leave Approval:
- All leave requests must be approved by immediate supervisor
- Leave during festival seasons will not be approved
- Weekend work may be required if leave is taken during weekdays

This policy is effective immediately and supersedes all previous leave policies.`
  };

  const handleContentTypeChange = (type) => {
    setContentType(type);
    if (sampleContent[type]) {
      setContent(sampleContent[type]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Please enter content to check for compliance');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/compliance-check`, {
        content: content.trim(),
        type: contentType,
        user_role: 'hr_professional'
      });

      if (response.data.success) {
        setResult(response.data.compliance_analysis);
      } else {
        throw new Error(response.data.error || 'Compliance check failed');
      }
    } catch (error) {
      console.error('Compliance check error:', error);
      setError(error.response?.data?.error || error.message || 'Failed to check compliance');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    setContent('');
    setResult(null);
    setError(null);
  };

  const formatAnalysis = (content) => {
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

  return (
    <div className="compliance-checker">
      <div className="checker-header">
        <h3>Legal Compliance Checker</h3>
        <p>Check your HR documents for legal compliance with Indian labor laws</p>
      </div>

      <form onSubmit={handleSubmit} className="compliance-form">
        <div className="form-group">
          <label htmlFor="contentType">Document Type:</label>
          <select
            id="contentType"
            value={contentType}
            onChange={(e) => handleContentTypeChange(e.target.value)}
            className="content-type-select"
          >
            {Object.entries(contentTypes).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="content">Document Content:</label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={`Enter your ${contentTypes[contentType].toLowerCase()} content here...`}
            rows={12}
            className="content-textarea"
            required
          />
          <div className="character-count">
            {content.length} characters
          </div>
        </div>

        <div className="sample-buttons">
          <span>Quick samples:</span>
          {Object.entries(sampleContent).map(([key, _]) => (
            <button
              key={key}
              type="button"
              onClick={() => handleContentTypeChange(key)}
              className={`sample-btn ${contentType === key ? 'active' : ''}`}
            >
              {contentTypes[key]}
            </button>
          ))}
        </div>

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading || !content.trim()}
            className="submit-button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              '🔍 Check Compliance'
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
        <div className="compliance-result">
          <div className="result-header">
            <h4>📋 Compliance Analysis Results</h4>
            <div className="result-meta">
              <span>Document Type: {contentTypes[contentType]}</span>
              {result.metadata && (
                <span>Confidence: {(result.metadata.confidence_score * 100).toFixed(1)}%</span>
              )}
            </div>
          </div>

          <div className="analysis-content">
            {formatAnalysis(result.content)}
          </div>

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
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.follow_up_questions && result.follow_up_questions.length > 0 && (
            <div className="result-follow-ups">
              <h5>❓ Recommended Follow-up Questions:</h5>
              <div className="follow-up-list">
                {result.follow_up_questions.map((question, index) => (
                  <div key={index} className="follow-up-item">
                    {question}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="result-actions">
            <button
              onClick={() => {
                const blob = new Blob([
                  `COMPLIANCE ANALYSIS REPORT\n\n` +
                  `Document Type: ${contentTypes[contentType]}\n` +
                  `Analysis Date: ${new Date().toLocaleDateString()}\n\n` +
                  `ANALYSIS:\n${result.content}\n\n` +
                  (result.citations ? `LEGAL REFERENCES:\n${result.citations.map(c => `- ${c.title}`).join('\n')}\n\n` : '') +
                  `ORIGINAL DOCUMENT:\n${content}`
                ], { type: 'text/plain' });
                
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `compliance-analysis-${Date.now()}.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="download-button"
            >
              📥 Download Report
            </button>
            
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.content)
                  .then(() => alert('Analysis copied to clipboard!'))
                  .catch(() => alert('Failed to copy to clipboard'));
              }}
              className="copy-button"
            >
              📋 Copy Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceChecker;

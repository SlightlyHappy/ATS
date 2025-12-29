import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DocumentGenerator = () => {
  const [templates, setTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [formFields, setFormFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const response = await axios.get(`${API_BASE_URL}/api/legal/document-templates`);
      if (response.data.success && response.data.templates) {
        setTemplates(response.data.templates || {});
        // Select first template by default
        const templatesObj = response.data.templates || {};
        const firstTemplate = Object.keys(templatesObj)[0];
        if (firstTemplate && templatesObj[firstTemplate]) {
          setSelectedTemplate(firstTemplate);
          initializeFormFields(templatesObj[firstTemplate]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setError('Failed to load document templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const initializeFormFields = (template) => {
    const fields = {};
    if (template && template.fields && Array.isArray(template.fields)) {
      template.fields.forEach(field => {
        fields[field] = getSampleValue(field);
      });
    }
    setFormFields(fields);
  };

  const getSampleValue = (fieldName) => {
    const samples = {
      employee_name: 'Priya Sharma',
      position: 'Senior Software Engineer',
      job_title: 'Senior Software Engineer',
      salary: '₹12,00,000 per annum',
      start_date: new Date().toLocaleDateString('en-IN'),
      company_name: 'TechCorp India Pvt Ltd',
      termination_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('en-IN'),
      reason: 'End of contract period',
      notice_period: '30 days',
      policy_name: 'Remote Work Policy',
      effective_date: new Date().toLocaleDateString('en-IN'),
      scope: 'All full-time employees',
      procedures: 'Approval required from immediate supervisor',
      department: 'Engineering',
      qualifications: 'Bachelor\'s degree in Computer Science or related field, 3+ years experience',
      responsibilities: 'Design and develop software applications, collaborate with cross-functional teams'
    };
    return samples[fieldName] || '';
  };

  const handleTemplateChange = (templateKey) => {
    setSelectedTemplate(templateKey);
    setResult(null);
    setError(null);
    if (templates[templateKey]) {
      initializeFormFields(templates[templateKey]);
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setFormFields(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!selectedTemplate) {
      setError('Please select a template');
      return;
    }

    // Validate required fields
    const template = templates[selectedTemplate];
    const missingFields = template.fields.filter(field => !formFields[field]?.trim());
    
    if (missingFields.length > 0) {
      setError(`Please fill in all required fields: ${missingFields.join(', ')}`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/generate-document`, {
        template_type: selectedTemplate,
        fields: formFields,
        user_role: 'hr_professional'
      });

      if (response.data.success) {
        setResult(response.data.document);
      } else {
        throw new Error(response.data.error || 'Document generation failed');
      }
    } catch (error) {
      console.error('Document generation error:', error);
      setError(error.response?.data?.error || error.message || 'Failed to generate document');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    if (selectedTemplate && templates[selectedTemplate]) {
      initializeFormFields(templates[selectedTemplate]);
    }
    setResult(null);
    setError(null);
  };

  const formatFieldName = (fieldName) => {
    return fieldName
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDocument = (content) => {
    if (!content || typeof content !== 'string') return '';
    
    return content
      .replace(/^\d+\.\s/gm, '• ')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .split('\n')
      .map((line, index) => (
        <div key={index} dangerouslySetInnerHTML={{ __html: line }} />
      ));
  };

  if (loadingTemplates) {
    return (
      <div className="document-generator">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading document templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="document-generator">
      <div className="generator-header">
        <h3>Legal Document Generator</h3>
        <p>Generate HR documents with legal compliance built-in</p>
      </div>

      <form onSubmit={handleGenerate} className="generator-form">
        <div className="form-group">
          <label htmlFor="template">Document Template:</label>
          <select
            id="template"
            value={selectedTemplate}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="template-select"
          >
            <option value="">Select a template</option>
            {templates && typeof templates === 'object' && Object.entries(templates).map(([key, template]) => (
              <option key={key} value={key}>
                {template?.name || key}
              </option>
            ))}
          </select>
          {selectedTemplate && templates[selectedTemplate] && (
            <small className="template-description">
              {templates[selectedTemplate].description}
            </small>
          )}
        </div>

        {selectedTemplate && templates[selectedTemplate] && templates[selectedTemplate].fields && Array.isArray(templates[selectedTemplate].fields) && (
          <div className="form-fields">
            <h4>Document Details</h4>
            <div className="fields-grid">
              {templates[selectedTemplate].fields.map(field => (
                <div key={field} className="field-group">
                  <label htmlFor={field}>
                    {formatFieldName(field)}:
                    <span className="required">*</span>
                  </label>
                  {field.includes('date') ? (
                    <input
                      type="text"
                      id={field}
                      value={formFields[field] || ''}
                      onChange={(e) => handleFieldChange(field, e.target.value)}
                      placeholder="DD/MM/YYYY"
                      required
                    />
                  ) : field === 'salary' ? (
                    <input
                      type="text"
                      id={field}
                      value={formFields[field] || ''}
                      onChange={(e) => handleFieldChange(field, e.target.value)}
                      placeholder="₹0,00,000 per annum"
                      required
                    />
                  ) : field.includes('responsibilities') || field.includes('procedures') || field.includes('qualifications') ? (
                    <textarea
                      id={field}
                      value={formFields[field] || ''}
                      onChange={(e) => handleFieldChange(field, e.target.value)}
                      rows={3}
                      required
                    />
                  ) : (
                    <input
                      type="text"
                      id={field}
                      value={formFields[field] || ''}
                      onChange={(e) => handleFieldChange(field, e.target.value)}
                      required
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading || !selectedTemplate}
            className="generate-button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              '📄 Generate Document'
            )}
          </button>
          <button
            type="button"
            onClick={clearForm}
            className="clear-button"
          >
            🔄 Reset Form
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
        <div className="generation-result">
          <div className="result-header">
            <h4>📋 Generated Document</h4>
            <div className="result-meta">
              <span>Template: {templates[selectedTemplate]?.name}</span>
              {result.metadata && (
                <span>Confidence: {(result.metadata.confidence_score * 100).toFixed(1)}%</span>
              )}
            </div>
          </div>

          <div className="document-content">
            {formatDocument(result.content)}
          </div>

          {result.citations && Array.isArray(result.citations) && result.citations.length > 0 && (
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

          <div className="document-actions">
            <button
              onClick={() => {
                const blob = new Blob([
                  `${templates[selectedTemplate]?.name || 'Legal Document'}\n` +
                  `Generated on: ${new Date().toLocaleDateString()}\n\n` +
                  `${result.content}\n\n` +
                  `--- Document Generation Details ---\n` +
                  `Template: ${selectedTemplate}\n` +
                  `Generated by: HR Legal Assistant\n` +
                  (result.citations && Array.isArray(result.citations) ? `\nLegal References:\n${result.citations.map(c => `- ${c.title}`).join('\n')}` : '')
                ], { type: 'text/plain' });
                
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${selectedTemplate}-${Date.now()}.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="download-button"
            >
              📥 Download Document
            </button>
            
            <button
              onClick={() => {
                navigator.clipboard.writeText(result.content)
                  .then(() => alert('Document copied to clipboard!'))
                  .catch(() => alert('Failed to copy to clipboard'));
              }}
              className="copy-button"
            >
              📋 Copy Document
            </button>

            <button
              onClick={() => window.print()}
              className="print-button"
            >
              🖨️ Print
            </button>
          </div>

          <div className="disclaimer">
            <p><strong>⚠️ Legal Disclaimer:</strong> This document is generated using AI and should be reviewed by a qualified legal professional before use. Laws and regulations may vary and change over time.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentGenerator;

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EmailManager.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Utility function to clean up HTML content for better display
const cleanEmailHTML = (htmlContent) => {
  if (!htmlContent) return '';
  
  // Basic HTML cleanup for email display
  return htmlContent
    // Remove excessive line breaks
    .replace(/\n\s*\n/g, '\n')
    // Ensure proper paragraph spacing
    .replace(/<\/p>\s*<p>/g, '</p><p>')
    // Clean up any malformed HTML
    .replace(/<br\s*\/?>\s*<br\s*\/?>/g, '<br>')
    // Ensure line breaks are properly formatted
    .replace(/\n/g, '<br>')
    .trim();
};

const EmailManager = () => {
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [emailTemplates, setEmailTemplates] = useState({});
  const [selectedTemplate, setSelectedTemplate] = useState('interview_invitation');
  const [intent, setIntent] = useState('');
  const [placeholders, setPlaceholders] = useState({});
  const [generatedEmails, setGeneratedEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState('compose'); // compose, generated
  const [filterScore, setFilterScore] = useState(0);
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [expandedEmail, setExpandedEmail] = useState(null);

  useEffect(() => {
    fetchCandidates();
    fetchEmailTemplates();
    fetchGeneratedEmails();
  }, []);

  const fetchCandidates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/email/candidates`);
      setCandidates(response.data.candidates);
    } catch (error) {
      console.error('Error fetching candidates:', error);
    }
  };

  const fetchEmailTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/email/templates`);
      setEmailTemplates(response.data.templates);
      
      // Initialize placeholders for default template
      if (response.data.templates.interview_invitation) {
        const defaultPlaceholders = {};
        response.data.templates.interview_invitation.placeholders.forEach(placeholder => {
          defaultPlaceholders[placeholder] = '';
        });
        setPlaceholders(defaultPlaceholders);
      }
    } catch (error) {
      console.error('Error fetching email templates:', error);
    }
  };

  const fetchGeneratedEmails = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/email/generated`);
      setGeneratedEmails(response.data.emails);
    } catch (error) {
      console.error('Error fetching generated emails:', error);
    }
  };

  const handleCandidateSelection = (candidateId) => {
    setSelectedCandidates(prev => {
      if (prev.includes(candidateId)) {
        return prev.filter(id => id !== candidateId);
      } else {
        return [...prev, candidateId];
      }
    });
  };

  const handleSelectAll = () => {
    const filteredCandidates = getFilteredAndSortedCandidates();
    if (selectedCandidates.length === filteredCandidates.length) {
      setSelectedCandidates([]);
    } else {
      setSelectedCandidates(filteredCandidates.map(c => c.id));
    }
  };

  const handleTemplateChange = (templateType) => {
    setSelectedTemplate(templateType);
    
    // Reset placeholders for new template
    const template = emailTemplates[templateType];
    if (template && template.placeholders) {
      const newPlaceholders = {};
      template.placeholders.forEach(placeholder => {
        newPlaceholders[placeholder] = placeholders[placeholder] || '';
      });
      setPlaceholders(newPlaceholders);
    } else {
      setPlaceholders({});
    }
  };

  const handlePlaceholderChange = (key, value) => {
    setPlaceholders(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const generateEmails = async () => {
    if (selectedCandidates.length === 0) {
      alert('Please select at least one candidate.');
      return;
    }

    if (!intent.trim()) {
      alert('Please provide the intent of the email.');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/email/generate`, {
        candidate_ids: selectedCandidates,
        template_type: selectedTemplate,
        intent: intent,
        placeholders: placeholders
      });

      await fetchGeneratedEmails();
      setActiveView('generated');
      
      alert(`Successfully generated ${response.data.total_generated} emails!`);
    } catch (error) {
      console.error('Error generating emails:', error);
      alert('Error generating emails. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredAndSortedCandidates = () => {
    let filtered = candidates.filter(candidate => 
      candidate.overall_score >= filterScore && 
      candidate.email && candidate.email.trim() !== ''
    );

    filtered.sort((a, b) => {
      const aVal = a[sortBy] || 0;
      const bVal = b[sortBy] || 0;
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  };

  const exportEmails = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/email/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'generated_emails.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting emails:', error);
      alert('Error exporting emails.');
    }
  };

  const clearGeneratedEmails = async () => {
    if (window.confirm('Are you sure you want to clear all generated emails?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/email/clear`);
        setGeneratedEmails([]);
      } catch (error) {
        console.error('Error clearing emails:', error);
      }
    }
  };

  const deleteEmail = async (emailId) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/email/generated/${emailId}`);
      setGeneratedEmails(prev => prev.filter(email => email.id !== emailId));
    } catch (error) {
      console.error('Error deleting email:', error);
    }
  };

  const openEmailModal = (email) => {
    setExpandedEmail(email);
  };

  const closeEmailModal = () => {
    setExpandedEmail(null);
  };

  const filteredCandidates = getFilteredAndSortedCandidates();

  return (
    <div className="email-manager">
      <div className="email-manager-header">
        <h2>Email Manager</h2>
        <div className="view-selector">
          <button
            className={`view-btn ${activeView === 'compose' ? 'active' : ''}`}
            onClick={() => setActiveView('compose')}
          >
            Compose ({selectedCandidates.length} selected)
          </button>
          <button
            className={`view-btn ${activeView === 'generated' ? 'active' : ''}`}
            onClick={() => setActiveView('generated')}
          >
            Generated Emails ({generatedEmails.length})
          </button>
        </div>
      </div>

      {activeView === 'compose' && (
        <div className="compose-view">
          <div className="compose-layout">
            <div className="candidate-selection">
              <div className="selection-header">
                <h3>Select Candidates</h3>
                <div className="selection-controls">
                  <div className="filter-controls">
                    <label>
                      Min Score:
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={filterScore}
                        onChange={(e) => setFilterScore(Number(e.target.value))}
                      />
                      <span>{filterScore}</span>
                    </label>
                    <label>
                      Sort by:
                      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                        <option value="overall_score">Overall Score</option>
                        <option value="role_fit_score">Role Fit Score</option>
                        <option value="name">Name</option>
                        <option value="processed_at">Date Processed</option>
                      </select>
                    </label>
                    <label>
                      Order:
                      <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                      </select>
                    </label>
                  </div>
                  <button onClick={handleSelectAll} className="select-all-btn">
                    {selectedCandidates.length === filteredCandidates.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
              </div>

              <div className="candidates-table">
                <table>
                  <thead>
                    <tr>
                      <th>Select</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Overall Score</th>
                      <th>Role Fit</th>
                      <th>Phone</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCandidates.map(candidate => (
                      <tr key={candidate.id} className={selectedCandidates.includes(candidate.id) ? 'selected' : ''}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedCandidates.includes(candidate.id)}
                            onChange={() => handleCandidateSelection(candidate.id)}
                          />
                        </td>
                        <td>{candidate.name}</td>
                        <td>{candidate.email}</td>
                        <td>
                          <span className={`score ${candidate.overall_score >= 70 ? 'good' : candidate.overall_score >= 50 ? 'average' : 'poor'}`}>
                            {candidate.overall_score}%
                          </span>
                        </td>
                        <td>
                          <span className={`score ${candidate.role_fit_score >= 70 ? 'good' : candidate.role_fit_score >= 50 ? 'average' : 'poor'}`}>
                            {candidate.role_fit_score}%
                          </span>
                        </td>
                        <td>{candidate.phone || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredCandidates.length === 0 && (
                  <div className="no-candidates">
                    No candidates match your filter criteria.
                  </div>
                )}
              </div>
            </div>

            <div className="email-composition">
              <h3>Email Configuration</h3>
              
              <div className="template-selection">
                <label>
                  Email Template:
                  <select value={selectedTemplate} onChange={(e) => handleTemplateChange(e.target.value)}>
                    {Object.entries(emailTemplates).map(([key, template]) => (
                      <option key={key} value={key}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </label>
                {emailTemplates[selectedTemplate] && (
                  <p className="template-description">
                    {emailTemplates[selectedTemplate].description}
                  </p>
                )}
              </div>

              <div className="intent-input">
                <label>
                  Email Intent/Purpose:
                  <textarea
                    value={intent}
                    onChange={(e) => setIntent(e.target.value)}
                    placeholder="Describe the purpose of this email (e.g., 'Invite for technical interview next week', 'Thank for application but position filled', etc.)"
                    rows="3"
                    required
                  />
                </label>
              </div>

              {emailTemplates[selectedTemplate] && emailTemplates[selectedTemplate].placeholders.length > 0 && (
                <div className="placeholders">
                  <h4>Dynamic Information</h4>
                  <p className="placeholders-note">
                    Fill in the information you want to include. Leave fields empty if not needed.
                  </p>
                  {emailTemplates[selectedTemplate].placeholders.map(placeholder => (
                    <label key={placeholder}>
                      {placeholder.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                      <input
                        type={
                          placeholder.includes('date') ? 'date' : 
                          placeholder.includes('time') ? 'time' : 
                          placeholder.includes('link') || placeholder.includes('url') ? 'url' :
                          'text'
                        }
                        value={placeholders[placeholder] || ''}
                        onChange={(e) => handlePlaceholderChange(placeholder, e.target.value)}
                        placeholder={
                          placeholder.includes('link') ? 'https://calendly.com/your-link or meeting URL' :
                          placeholder.includes('salary') ? 'e.g., $75,000 - $85,000' :
                          placeholder.includes('date') ? 'Select date' :
                          placeholder.includes('time') ? 'Select time' :
                          `Enter ${placeholder.replace(/_/g, ' ')}`
                        }
                      />
                    </label>
                  ))}
                </div>
              )}

              <div className="generation-controls">
                <button
                  onClick={generateEmails}
                  disabled={loading || selectedCandidates.length === 0 || !intent.trim()}
                  className="generate-btn"
                >
                  {loading ? 'Generating...' : `Generate Emails (${selectedCandidates.length} candidates)`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeView === 'generated' && (
        <div className="generated-view">
          <div className="generated-header">
            <h3>Generated Emails ({generatedEmails.length})</h3>
            <div className="generated-controls">
              <button onClick={exportEmails} className="export-btn">
                Export CSV
              </button>
              <button onClick={clearGeneratedEmails} className="clear-btn">
                Clear All
              </button>
            </div>
          </div>

          <div className="generated-emails">
            {generatedEmails.length === 0 ? (
              <div className="no-emails">
                No emails generated yet. Go to the Compose tab to create emails.
              </div>
            ) : (
              generatedEmails.map(email => (
                <div key={email.id} className="email-card" onClick={() => openEmailModal(email)}>
                  <div className="email-header">
                    <div className="email-info">
                      <h4>{email.candidate_name}</h4>
                      <p>{email.candidate_email}</p>
                      <span className="email-template">{emailTemplates[email.template_type]?.name || email.template_type}</span>
                      <span className="email-date">{new Date(email.generated_at).toLocaleString()}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteEmail(email.id);
                      }}
                      className="delete-email-btn"
                      title="Delete email"
                    >
                      ×
                    </button>
                  </div>
                  
                  <div className="email-content-preview">
                    <div className="email-subject-preview">
                      <strong>Subject:</strong> {email.subject}
                    </div>
                    <div className="email-body-preview">
                      <strong>Body Preview:</strong>
                      <div className="email-body-preview-content">
                        {email.body.replace(/<[^>]*>/g, '').substring(0, 150)}...
                      </div>
                    </div>
                    <div className="click-to-expand">
                      Click to view full email
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Email Modal */}
      {expandedEmail && (
        <div className="email-modal-overlay" onClick={closeEmailModal}>
          <div className="email-modal" onClick={(e) => e.stopPropagation()}>
            <div className="email-modal-header">
              <div className="email-modal-info">
                <h2>{expandedEmail.candidate_name}</h2>
                <p className="email-modal-email">{expandedEmail.candidate_email}</p>
                <div className="email-modal-meta">
                  <span className="email-template">{emailTemplates[expandedEmail.template_type]?.name || expandedEmail.template_type}</span>
                  <span className="email-date">{new Date(expandedEmail.generated_at).toLocaleString()}</span>
                </div>
              </div>
              <button onClick={closeEmailModal} className="email-modal-close">
                ×
              </button>
            </div>
            
            <div className="email-modal-content">
              <div className="email-modal-subject">
                <h3>Subject</h3>
                <p>{expandedEmail.subject}</p>
              </div>
              
              <div className="email-modal-body">
                <h3>Email Body</h3>
                <div 
                  className="email-modal-body-content"
                  dangerouslySetInnerHTML={{ __html: cleanEmailHTML(expandedEmail.body) }}
                />
              </div>
              
              <div className="email-modal-footer">
                <div className="email-modal-meta-info">
                  <span className="email-tone">Tone: {expandedEmail.tone}</span>
                  <span className="email-reading-time">Reading time: {expandedEmail.estimated_reading_time}</span>
                </div>
                <div className="email-modal-actions">
                  <button 
                    onClick={() => {
                      deleteEmail(expandedEmail.id);
                      closeEmailModal();
                    }}
                    className="email-modal-delete-btn"
                  >
                    Delete Email
                  </button>
                  <button onClick={closeEmailModal} className="email-modal-close-btn">
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailManager;

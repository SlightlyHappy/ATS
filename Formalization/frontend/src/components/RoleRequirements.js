import React, { useState, useEffect } from 'react';
import './RoleRequirements.css';

const RoleRequirements = ({ roleRequirements, onUpdate }) => {
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    if (roleRequirements && roleRequirements.simple_description) {
      setDescription(roleRequirements.simple_description);
      setCharCount(roleRequirements.simple_description.length);
      window.debugLog('info', 'Job requirements loaded', { 
        length: roleRequirements.simple_description.length 
      });
    }
  }, [roleRequirements]);

  const handleInputChange = (e) => {
    const value = e.target.value;
    setDescription(value);
    setCharCount(value.length);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) {
      window.debugLog('warning', 'Attempted to submit empty job requirements');
      return;
    }

    setIsSubmitting(true);
    setIsSuccess(false);
    
    try {
      const requirements = {
        simple_description: description.trim()
      };
      
      window.debugLog('info', 'Submitting job requirements', { 
        length: description.length,
        preview: description.substring(0, 100) + '...'
      });
      
      await onUpdate(requirements);
      setIsSuccess(true);
      
      // Reset success state after animation
      setTimeout(() => setIsSuccess(false), 2000);
      
      window.debugLog('info', 'Job requirements updated successfully');
    } catch (error) {
      window.debugLog('error', 'Error updating job requirements', error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClear = () => {
    setDescription('');
    setCharCount(0);
    const emptyRequirements = { simple_description: '' };
    onUpdate(emptyRequirements);
    window.debugLog('info', 'Job requirements cleared');
  };

  const getCharCountColor = () => {
    if (charCount === 0) return '#718096';
    if (charCount < 50) return '#e53e3e';
    if (charCount < 200) return '#dd6b20';
    if (charCount < 500) return '#38a169';
    return '#667eea';
  };

  const exampleRequirements = [
    {
      text: "I am looking for someone to be a doctor in my clinic. I want them to be clean, respectful, and have a masters degree.",
      icon: "🏥"
    },
    {
      text: "Need a software engineer who knows React and Python. Must have 3+ years experience and be good with teamwork.",
      icon: "💻"
    },
    {
      text: "Looking for a marketing manager with social media experience. Should be creative, organized, and have a bachelor's degree.",
      icon: "📈"
    },
    {
      text: "Want a chef for my restaurant. Must know Italian cuisine, have 5+ years experience, and be able to work under pressure.",
      icon: "👨‍🍳"
    }
  ];

  return (
    <div className="role-requirements">
      <div className="requirements-header">
        <h2>Define Your Perfect Candidate</h2>
        <p>Describe your ideal hire in simple, natural language and let our AI do the rest</p>
      </div>

      <form onSubmit={handleSubmit} className="requirements-form">
        <div className="form-group">
          <label htmlFor="job_description">
            What kind of person are you looking for? *
          </label>
          <textarea
            id="job_description"
            value={description}
            onChange={handleInputChange}
            placeholder="Describe the job and ideal candidate in your own words... 
            
For example: 'I need a friendly barista who can work mornings, make great coffee, and enjoys talking with customers. Previous experience would be nice but not required.'"
            rows={6}
            required
            className="description-textarea"
          />
          <div className="character-count" style={{ color: getCharCountColor() }}>
            <span className="count-number">{charCount}</span> characters
            {charCount > 0 && (
              <span className="count-status">
                {charCount < 50 && " • Too short, add more details"}
                {charCount >= 50 && charCount < 200 && " • Good start, could use more detail"}
                {charCount >= 200 && charCount < 500 && " • Perfect length! 👌"}
                {charCount >= 500 && " • Very detailed! 🎯"}
              </span>
            )}
          </div>
        </div>

        <div className="examples-section">
          <h4>💡 Example Job Requirements</h4>
          <p style={{ color: '#718096', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Click any example below to use it as a starting point:
          </p>
          <div className="examples-grid">
            {exampleRequirements.map((example, index) => (
              <div 
                key={index} 
                className="example-item"
                onClick={() => {
                  setDescription(example.text);
                  setCharCount(example.text.length);
                }}
              >
                <div className="example-icon">{example.icon}</div>
                <div className="example-text">"{example.text}"</div>
              </div>
            ))}
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className={`submit-btn ${isSubmitting ? 'loading' : ''} ${isSuccess ? 'success' : ''}`}
            disabled={!description.trim() || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <span className="btn-icon">⏳</span>
                Processing...
              </>
            ) : isSuccess ? (
              <>
                <span className="btn-icon">✅</span>
                Updated!
              </>
            ) : (
              <>
                <span className="btn-icon">🚀</span>
                Set Requirements
              </>
            )}
          </button>
          <button 
            type="button" 
            onClick={handleClear}
            className="clear-btn"
            disabled={isSubmitting}
          >
            <span className="btn-icon">🗑️</span>
            Clear All
          </button>
        </div>
      </form>

      {roleRequirements && roleRequirements.simple_description && (
        <div className="current-requirements">
          <h3>📋 Current Job Requirements</h3>
          <div className="requirements-display">
            {roleRequirements.simple_description}
          </div>
          {roleRequirements.updated_at && (
            <div className="updated-at">
              Last updated: {new Date(roleRequirements.updated_at).toLocaleString()}
            </div>
          )}
          <div className="requirements-stats">
            <div className="stat-item">
              <span className="stat-icon">📝</span>
              <span className="stat-label">Characters:</span>
              <span className="stat-value">{roleRequirements.simple_description.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-icon">📖</span>
              <span className="stat-label">Words:</span>
              <span className="stat-value">{roleRequirements.simple_description.split(' ').length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleRequirements;

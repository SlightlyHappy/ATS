import React, { useState, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
  RadialLinearScale,
} from 'chart.js';
import { Bar, Doughnut, Line, Radar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement,
  RadialLinearScale
);

const Dashboard = ({ resumes, roleRequirements, onClearResumes, onExportCSV, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard' or 'detailed-table'

  // Enhanced statistics calculation
  const stats = useMemo(() => {
    if (resumes.length === 0) return { 
      total: 0, 
      processed: 0,
      scores: {},
      demographics: {},
      experience: {},
      education: {},
      hiring: {},
      hasRoleRequirements: false
    };
    
    const successfulResumes = resumes.filter(r => r.status === 'success');
    
    // Score statistics
    const overallScores = successfulResumes.map(r => r.ai_analysis?.scores?.overall_score || 0);
    const technicalScores = successfulResumes.map(r => r.ai_analysis?.scores?.technical_skills_score || 0);
    const experienceScores = successfulResumes.map(r => r.ai_analysis?.scores?.experience_score || 0);
    const roleFitScores = successfulResumes.map(r => r.ai_analysis?.scores?.role_fit_score || 0);
    
    // Demographics
    const locations = successfulResumes.map(r => {
      const location = r.ai_analysis?.basic_info?.location;
      return location?.city && location?.country ? `${location.city}, ${location.country}` : 'Unknown';
    });
    
    const experienceLevels = successfulResumes.map(r => r.ai_analysis?.analysis?.experience_level || 'Unknown');
    
    // Education stats
    const educationCounts = successfulResumes.map(r => r.ai_analysis?.education?.length || 0);
    const certificationCounts = successfulResumes.map(r => r.ai_analysis?.certifications?.length || 0);
    
    // Hiring recommendations
    const hiringDecisions = successfulResumes.map(r => r.ai_analysis?.recommendations?.hiring_decision || 'Unknown');
    
    const calculateAvg = (arr) => arr.length > 0 ? Math.round(arr.reduce((sum, val) => sum + val, 0) / arr.length) : 0;
    const calculateMax = (arr) => arr.length > 0 ? Math.max(...arr) : 0;
    
    return {
      total: resumes.length,
      processed: successfulResumes.length,
      scores: {
        avgOverall: calculateAvg(overallScores),
        maxOverall: calculateMax(overallScores),
        avgTechnical: calculateAvg(technicalScores),
        avgExperience: calculateAvg(experienceScores),
        avgRoleFit: calculateAvg(roleFitScores),
        maxRoleFit: calculateMax(roleFitScores),
      },
      demographics: {
        locations: [...new Set(locations)].length,
        topLocation: locations.sort((a,b) => 
          locations.filter(v => v === a).length - locations.filter(v => v === b).length
        ).pop(),
      },
      experience: {
        levels: experienceLevels.reduce((acc, level) => {
          acc[level] = (acc[level] || 0) + 1;
          return acc;
        }, {}),
        avgEducationDegrees: calculateAvg(educationCounts),
        avgCertifications: calculateAvg(certificationCounts),
      },
      hiring: {
        decisions: hiringDecisions.reduce((acc, decision) => {
          acc[decision] = (acc[decision] || 0) + 1;
          return acc;
        }, {}),
        recommendedCount: hiringDecisions.filter(d => d === 'Strong Hire' || d === 'Hire').length,
      },
      hasRoleRequirements: !!(roleRequirements && roleRequirements.simple_description)
    };
  }, [resumes, roleRequirements]);

  // Enhanced filter and sort resumes
  const filteredAndSortedResumes = useMemo(() => {
    let filtered = resumes.filter(resume => {
      const searchLower = searchTerm.toLowerCase();
      const ai = resume.ai_analysis;
      return (
        (resume.filename?.toLowerCase().includes(searchLower)) ||
        (ai?.basic_info?.name?.toLowerCase().includes(searchLower)) ||
        (ai?.basic_info?.email?.toLowerCase().includes(searchLower)) ||
        (ai?.skills?.some(skill => skill.toLowerCase().includes(searchLower))) ||
        (ai?.analysis?.specialization_focus?.toLowerCase().includes(searchLower)) ||
        (ai?.experience?.some(exp => exp.company?.toLowerCase().includes(searchLower))) ||
        (ai?.experience?.some(exp => exp.job_title?.toLowerCase().includes(searchLower)))
      );
    });

    filtered.sort((a, b) => {
      let aVal, bVal;
      
      switch (sortBy) {
        case 'filename':
          aVal = a.filename || '';
          bVal = b.filename || '';
          break;
        case 'name':
          aVal = a.ai_analysis?.basic_info?.name || '';
          bVal = b.ai_analysis?.basic_info?.name || '';
          break;
        case 'overall_score':
          aVal = a.ai_analysis?.scores?.overall_score || 0;
          bVal = b.ai_analysis?.scores?.overall_score || 0;
          break;
        case 'role_fit_score':
          aVal = a.ai_analysis?.scores?.role_fit_score || 0;
          bVal = b.ai_analysis?.scores?.role_fit_score || 0;
          break;
        case 'technical_skills_score':
          aVal = a.ai_analysis?.scores?.technical_skills_score || 0;
          bVal = b.ai_analysis?.scores?.technical_skills_score || 0;
          break;
        case 'experience_score':
          aVal = a.ai_analysis?.scores?.experience_score || 0;
          bVal = b.ai_analysis?.scores?.experience_score || 0;
          break;
        case 'experience_years':
          aVal = a.ai_analysis?.experience?.reduce((total, exp) => total + (exp.duration_months || 0), 0) / 12 || 0;
          bVal = b.ai_analysis?.experience?.reduce((total, exp) => total + (exp.duration_months || 0), 0) / 12 || 0;
          break;
        case 'hiring_decision':
          const order = { 'Strong Hire': 4, 'Hire': 3, 'Maybe': 2, 'Pass': 1 };
          aVal = order[a.ai_analysis?.recommendations?.hiring_decision] || 0;
          bVal = order[b.ai_analysis?.recommendations?.hiring_decision] || 0;
          break;
        case 'processed_at':
          aVal = new Date(a.processed_at);
          bVal = new Date(b.processed_at);
          break;
        default:
          aVal = 0;
          bVal = 0;
      }
      
      if (typeof aVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      } else {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }
    });

    return filtered;
  }, [resumes, searchTerm, sortBy, sortOrder]);

  // Enhanced Chart data
  const scoreDistributionData = useMemo(() => {
    const ranges = ['90-100', '80-89', '70-79', '60-69', '< 60'];
    const counts = [0, 0, 0, 0, 0];
    
    resumes.forEach(resume => {
      const score = resume.ai_analysis?.scores?.overall_score || 0;
      if (score >= 90) counts[0]++;
      else if (score >= 80) counts[1]++;
      else if (score >= 70) counts[2]++;
      else if (score >= 60) counts[3]++;
      else counts[4]++;
    });

    return {
      labels: ranges,
      datasets: [{
        label: 'Number of Candidates',
        data: counts,
        backgroundColor: [
          '#10b981', // green-500
          '#3b82f6', // blue-500
          '#f59e0b', // amber-500
          '#f97316', // orange-500
          '#ef4444'  // red-500
        ],
        borderWidth: 0,
        borderRadius: 8,
      }]
    };
  }, [resumes]);

  // Skills distribution chart
  const skillsData = useMemo(() => {
    const skillCounts = {};
    resumes.forEach(resume => {
      resume.ai_analysis?.skills?.forEach(skill => {
        const normalizedSkill = skill.toLowerCase().trim();
        skillCounts[normalizedSkill] = (skillCounts[normalizedSkill] || 0) + 1;
      });
    });

    const topSkills = Object.entries(skillCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10);

    return {
      labels: topSkills.map(([skill]) => skill),
      datasets: [{
        data: topSkills.map(([,count]) => count),
        backgroundColor: [
          '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe',
          '#00f2fe', '#43e97b', '#38f9d7', '#ff6b6b', '#4ecdc4'
        ],
        borderWidth: 0,
      }]
    };
  }, [resumes]);

  // Experience level distribution
  const experienceLevelData = useMemo(() => {
    const levels = ['Junior', 'Mid', 'Senior', 'Expert'];
    const counts = levels.map(level => 
      resumes.filter(r => r.ai_analysis?.analysis?.experience_level === level).length
    );

    return {
      labels: levels,
      datasets: [{
        label: 'Candidates',
        data: counts,
        backgroundColor: ['#fbbf24', '#60a5fa', '#34d399', '#f87171'],
        borderWidth: 0,
        borderRadius: 6,
      }]
    };
  }, [resumes]);

  // Hiring decisions chart
  const hiringDecisionData = useMemo(() => {
    const decisions = ['Strong Hire', 'Hire', 'Maybe', 'Pass'];
    const counts = decisions.map(decision => 
      resumes.filter(r => r.ai_analysis?.recommendations?.hiring_decision === decision).length
    );

    return {
      labels: decisions,
      datasets: [{
        data: counts,
        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
        borderWidth: 0,
      }]
    };
  }, [resumes]);

  // Skills radar chart for top candidates
  const topCandidatesRadarData = useMemo(() => {
    const topCandidates = resumes
      .filter(r => r.ai_analysis?.scores?.overall_score >= 70)
      .slice(0, 3)
      .map(r => ({
        name: r.ai_analysis?.basic_info?.name || r.filename,
        scores: r.ai_analysis?.scores || {}
      }));

    if (topCandidates.length === 0) return null;

    const categories = [
      'technical_skills_score',
      'experience_score', 
      'education_score',
      'communication_score',
      'leadership_score',
      'role_fit_score'
    ];

    return {
      labels: categories.map(cat => cat.replace('_score', '').replace('_', ' ')),
      datasets: topCandidates.map((candidate, idx) => ({
        label: candidate.name,
        data: categories.map(cat => candidate.scores[cat] || 0),
        backgroundColor: [`rgba(59, 130, 246, 0.1)`, `rgba(16, 185, 129, 0.1)`, `rgba(245, 158, 11, 0.1)`][idx],
        borderColor: [`rgb(59, 130, 246)`, `rgb(16, 185, 129)`, `rgb(245, 158, 11)`][idx],
        borderWidth: 2,
        pointBackgroundColor: [`rgb(59, 130, 246)`, `rgb(16, 185, 129)`, `rgb(245, 158, 11)`][idx],
      }))
    };
  }, [resumes]);

  // Utility functions
  const getScoreBadgeClass = (score) => {
    if (score >= 85) return 'score-excellent';
    if (score >= 75) return 'score-good';
    if (score >= 65) return 'score-average';
    return 'score-poor';
  };

  const getHiringDecisionBadge = (decision) => {
    const badges = {
      'Strong Hire': 'hiring-strong',
      'Hire': 'hiring-yes',
      'Maybe': 'hiring-maybe',
      'Pass': 'hiring-no'
    };
    return badges[decision] || 'hiring-unknown';
  };

  const formatExperienceYears = (experience) => {
    if (!experience || experience.length === 0) return '0';
    const totalMonths = experience.reduce((total, exp) => total + (exp.duration_months || 0), 0);
    return Math.round(totalMonths / 12 * 10) / 10; // Round to 1 decimal place
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  // Candidate detail modal
  const CandidateDetailModal = ({ candidate, onClose }) => {
    if (!candidate) return null;
    
    const ai = candidate.ai_analysis;
    const basic = ai?.basic_info || {};
    const scores = ai?.scores || {};
    const analysis = ai?.analysis || {};
    const recommendations = ai?.recommendations || {};
    
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content candidate-detail-modal" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h2>{basic.name || candidate.filename}</h2>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          
          <div className="modal-body">
            <div className="candidate-detail-grid">
              {/* Personal Information */}
              <div className="detail-section">
                <h3>Contact Information</h3>
                <div className="detail-items">
                  <div className="detail-item">
                    <span className="label">Email:</span>
                    <span className="value">{basic.email || 'Not provided'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Phone:</span>
                    <span className="value">{basic.phone || 'Not provided'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Location:</span>
                    <span className="value">
                      {basic.location?.city && basic.location?.country 
                        ? `${basic.location.city}, ${basic.location.country}`
                        : 'Not specified'}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="label">LinkedIn:</span>
                    <span className="value">{basic.linkedin || 'Not provided'}</span>
                  </div>
                </div>
              </div>

              {/* Scores */}
              <div className="detail-section">
                <h3>Assessment Scores</h3>
                <div className="scores-grid">
                  <div className="score-item">
                    <span className="score-label">Overall</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.overall_score || 0)}`}>
                      {scores.overall_score || 0}
                    </span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Technical</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.technical_skills_score || 0)}`}>
                      {scores.technical_skills_score || 0}
                    </span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Experience</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.experience_score || 0)}`}>
                      {scores.experience_score || 0}
                    </span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Education</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.education_score || 0)}`}>
                      {scores.education_score || 0}
                    </span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Communication</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.communication_score || 0)}`}>
                      {scores.communication_score || 0}
                    </span>
                  </div>
                  <div className="score-item">
                    <span className="score-label">Leadership</span>
                    <span className={`score-badge ${getScoreBadgeClass(scores.leadership_score || 0)}`}>
                      {scores.leadership_score || 0}
                    </span>
                  </div>
                  {stats.hasRoleRequirements && (
                    <div className="score-item">
                      <span className="score-label">Role Fit</span>
                      <span className={`score-badge ${getScoreBadgeClass(scores.role_fit_score || 0)}`}>
                        {scores.role_fit_score || 0}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Professional Summary */}
              <div className="detail-section full-width">
                <h3>Professional Summary</h3>
                <p className="summary-text">{ai?.summary || 'No summary available'}</p>
              </div>

              {/* Skills */}
              <div className="detail-section">
                <h3>Skills ({ai?.skills?.length || 0})</h3>
                <div className="skills-container">
                  {ai?.skills?.map((skill, idx) => (
                    <span key={idx} className="skill-tag">{skill}</span>
                  ))}
                </div>
              </div>

              {/* Experience */}
              <div className="detail-section">
                <h3>Experience ({ai?.experience?.length || 0} positions)</h3>
                <div className="experience-list">
                  {ai?.experience?.slice(0, 3).map((exp, idx) => (
                    <div key={idx} className="experience-item">
                      <h4>{exp.job_title} at {exp.company}</h4>
                      <p className="experience-duration">
                        {exp.start_date} - {exp.currently_working ? 'Present' : exp.end_date}
                        {exp.duration_months && ` (${Math.round(exp.duration_months/12*10)/10} years)`}
                      </p>
                      <div className="responsibilities">
                        {exp.responsibilities?.slice(0, 2).map((resp, ridx) => (
                          <p key={ridx} className="responsibility">• {truncateText(resp, 80)}</p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analysis */}
              <div className="detail-section full-width">
                <h3>AI Analysis</h3>
                <div className="analysis-grid">
                  <div className="analysis-item">
                    <span className="label">Experience Level:</span>
                    <span className="value">{analysis.experience_level}</span>
                  </div>
                  <div className="analysis-item">
                    <span className="label">Specialization:</span>
                    <span className="value">{analysis.specialization_focus}</span>
                  </div>
                  <div className="analysis-item">
                    <span className="label">Career Trajectory:</span>
                    <span className="value">{truncateText(analysis.career_trajectory, 60)}</span>
                  </div>
                </div>
                
                <div className="strengths-weaknesses">
                  <div className="strength-section">
                    <h4>Strengths</h4>
                    <ul>
                      {analysis.strengths?.slice(0, 3).map((strength, idx) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="weakness-section">
                    <h4>Areas for Development</h4>
                    <ul>
                      {analysis.weaknesses?.slice(0, 3).map((weakness, idx) => (
                        <li key={idx}>{weakness}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Hiring Recommendation */}
              <div className="detail-section full-width">
                <h3>Hiring Recommendation</h3>
                <div className="recommendation-content">
                  <div className="recommendation-header">
                    <span className={`hiring-badge ${getHiringDecisionBadge(recommendations.hiring_decision)}`}>
                      {recommendations.hiring_decision || 'No recommendation'}
                    </span>
                    <span className="confidence">
                      Confidence: {recommendations.decision_confidence || 'Unknown'}
                    </span>
                  </div>
                  <p className="executive-summary">
                    {ai?.executive_summary || 'No executive summary available'}
                  </p>
                  {recommendations.key_decision_factors?.length > 0 && (
                    <div className="decision-factors">
                      <h4>Key Decision Factors:</h4>
                      <ul>
                        {recommendations.key_decision_factors.map((factor, idx) => (
                          <li key={idx}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (resumes.length === 0) {
    return (
      <div className="dashboard">
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <h2 className="empty-state-title">HR Recruitment Dashboard</h2>
          <p className="empty-state-text">
            Upload resume files to begin AI-powered candidate analysis and recruitment insights.
          </p>
          <div className="empty-state-features">
            <div className="feature-item">✅ Automated resume parsing</div>
            <div className="feature-item">🤖 AI-powered candidate scoring</div>
            <div className="feature-item">📈 Professional recruitment analytics</div>
            <div className="feature-item">💼 Role-specific matching</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-title">
            <h1>HR Recruitment Dashboard</h1>
            <p>AI-Powered Candidate Analysis & Insights</p>
          </div>
          <div className="header-controls">
            <div className="view-mode-toggle">
              <button 
                className={`toggle-btn ${viewMode === 'dashboard' ? 'active' : ''}`}
                onClick={() => setViewMode('dashboard')}
              >
                📊 Dashboard
              </button>
              <button 
                className={`toggle-btn ${viewMode === 'detailed-table' ? 'active' : ''}`}
                onClick={() => setViewMode('detailed-table')}
              >
                📋 Detailed View
              </button>
            </div>
            <div className="dashboard-actions">
              <button onClick={onRefresh} className="dashboard-button refresh-button">
                🔄 Refresh
              </button>
              <button onClick={onExportCSV} className="dashboard-button export-button">
                📥 Export CSV
              </button>
              <button 
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear all resume data?')) {
                    onClearResumes();
                  }
                }}
                className="dashboard-button clear-button"
              >
                🗑️ Clear All
              </button>
            </div>
          </div>
        </div>
      </div>

      {viewMode === 'dashboard' && (
        <>
          {/* Key Metrics */}
          <div className="metrics-section">
            <h2 className="section-title">Key Recruitment Metrics</h2>
            <div className="stats-grid">
              <div className="stat-card primary">
                <div className="stat-icon">👥</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.total}</div>
                  <div className="stat-label">Total Candidates</div>
                </div>
              </div>
              <div className="stat-card success">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.processed}</div>
                  <div className="stat-label">Successfully Processed</div>
                </div>
              </div>
              <div className="stat-card info">
                <div className="stat-icon">⭐</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.scores.avgOverall}</div>
                  <div className="stat-label">Average Score</div>
                </div>
              </div>
              <div className="stat-card warning">
                <div className="stat-icon">🏆</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.scores.maxOverall}</div>
                  <div className="stat-label">Top Score</div>
                </div>
              </div>
              <div className="stat-card accent">
                <div className="stat-icon">👍</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.hiring.recommendedCount}</div>
                  <div className="stat-label">Recommended Hires</div>
                </div>
              </div>
              <div className="stat-card neutral">
                <div className="stat-icon">🌍</div>
                <div className="stat-content">
                  <div className="stat-value">{stats.demographics.locations}</div>
                  <div className="stat-label">Unique Locations</div>
                </div>
              </div>
              {stats.hasRoleRequirements && (
                <>
                  <div className="stat-card role-specific">
                    <div className="stat-icon">🎯</div>
                    <div className="stat-content">
                      <div className="stat-value">{stats.scores.avgRoleFit}</div>
                      <div className="stat-label">Avg Role Fit</div>
                    </div>
                  </div>
                  <div className="stat-card role-specific">
                    <div className="stat-icon">🥇</div>
                    <div className="stat-content">
                      <div className="stat-value">{stats.scores.maxRoleFit}</div>
                      <div className="stat-label">Best Role Fit</div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Role Requirements Status */}
          {stats.hasRoleRequirements ? (
            <div className="role-requirements-status active">
              <div className="role-status-header">
                <h3>🎯 Active Role Analysis</h3>
                <span className="role-status-badge">ACTIVE</span>
              </div>
              <p className="role-description">
                AI analysis is comparing candidates against specific role requirements for enhanced matching accuracy.
              </p>
            </div>
          ) : (
            <div className="role-requirements-status inactive">
              <div className="role-status-header">
                <h3>💡 Enhance Your Analysis</h3>
                <span className="role-status-badge inactive">NO ROLE SET</span>
              </div>
              <p className="role-description">
                Set up role requirements to get AI-powered candidate matching scores and role-specific insights.
              </p>
            </div>
          )}

          {/* Charts Grid */}
          <div className="charts-section">
            <h2 className="section-title">Analytics & Insights</h2>
            <div className="charts-grid">
              {/* Score Distribution */}
              <div className="chart-container">
                <h3 className="chart-title">Overall Score Distribution</h3>
                <Bar 
                  data={scoreDistributionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                      padding: {
                        top: 20,
                        right: 20,
                        bottom: 20,
                        left: 20
                      }
                    },
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                      }
                    },
                    scales: {
                      y: { 
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#666' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      },
                      x: {
                        ticks: { color: '#666' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      }
                    },
                  }}
                />
              </div>

              {/* Experience Levels */}
              <div className="chart-container">
                <h3 className="chart-title">Experience Level Distribution</h3>
                <Bar 
                  data={experienceLevelData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                      padding: {
                        top: 20,
                        right: 20,
                        bottom: 20,
                        left: 20
                      }
                    },
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                      }
                    },
                    scales: {
                      y: { 
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#666' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      },
                      x: {
                        ticks: { color: '#666' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                      }
                    },
                  }}
                />
              </div>

              {/* Hiring Decisions */}
              <div className="chart-container">
                <h3 className="chart-title">Hiring Recommendations</h3>
                <Doughnut 
                  data={hiringDecisionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                      padding: {
                        top: 10,
                        right: 10,
                        bottom: 30,
                        left: 10
                      }
                    },
                    plugins: {
                      legend: { 
                        position: 'bottom',
                        labels: { 
                          color: '#666',
                          padding: 15,
                          usePointStyle: true
                        }
                      },
                      tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                      }
                    },
                  }}
                />
              </div>

              {/* Top Skills */}
              {skillsData.labels.length > 0 && (
                <div className="chart-container">
                  <h3 className="chart-title">Most Common Skills</h3>
                  <Doughnut 
                    data={skillsData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      layout: {
                        padding: {
                          top: 10,
                          right: 10,
                          bottom: 30,
                          left: 10
                        }
                      },
                      plugins: {
                        legend: { 
                          position: 'bottom',
                          labels: { 
                            color: '#666',
                            font: { size: 11 },
                            padding: 12,
                            usePointStyle: true
                          }
                        },
                        tooltip: {
                          backgroundColor: 'rgba(0, 0, 0, 0.8)',
                          titleColor: '#fff',
                          bodyColor: '#fff',
                        }
                      },
                    }}
                  />
                </div>
              )}

              {/* Top Candidates Radar */}
              {topCandidatesRadarData && (
                <div className="chart-container wide">
                  <h3 className="chart-title">Top Candidates Skill Comparison</h3>
                  <Radar 
                    data={topCandidatesRadarData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      layout: {
                        padding: {
                          top: 20,
                          right: 20,
                          bottom: 40,
                          left: 20
                        }
                      },
                      plugins: {
                        legend: { 
                          position: 'bottom',
                          labels: { 
                            color: '#666',
                            padding: 15,
                            usePointStyle: true
                          }
                        },
                        tooltip: {
                          backgroundColor: 'rgba(0, 0, 0, 0.8)',
                          titleColor: '#fff',
                          bodyColor: '#fff',
                        }
                      },
                      scales: {
                        r: {
                          beginAtZero: true,
                          max: 100,
                          ticks: { 
                            color: '#666',
                            stepSize: 20,
                            showLabelBackdrop: false
                          },
                          grid: { color: 'rgba(255, 255, 255, 0.1)' },
                          angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                          pointLabels: { 
                            color: '#666',
                            font: { size: 11 }
                          }
                        }
                      }
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Detailed Table View or Summary Table */}
      <div className="candidates-section">
        <div className="candidates-header">
          <h2 className="section-title">
            {viewMode === 'detailed-table' ? 'Detailed Candidate Analysis' : 'Candidate Summary'} 
            ({filteredAndSortedResumes.length})
          </h2>
          <div className="candidates-controls">
            <input
              type="text"
              placeholder="Search candidates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
              className="sort-select"
            >
              <option value="overall_score-desc">Overall Score (High to Low)</option>
              <option value="overall_score-asc">Overall Score (Low to High)</option>
              {stats.hasRoleRequirements && (
                <>
                  <option value="role_fit_score-desc">Role Fit (High to Low)</option>
                  <option value="role_fit_score-asc">Role Fit (Low to High)</option>
                </>
              )}
              <option value="technical_skills_score-desc">Technical Skills (High to Low)</option>
              <option value="experience_score-desc">Experience (High to Low)</option>
              <option value="hiring_decision-desc">Hiring Recommendation</option>
              <option value="name-asc">Name (A-Z)</option>
              <option value="filename-asc">Filename (A-Z)</option>
              <option value="processed_at-desc">Latest First</option>
            </select>
          </div>
        </div>

        {viewMode === 'dashboard' ? (
          /* Summary Cards View */
          <div className="candidates-grid">
            {filteredAndSortedResumes.map((resume, index) => {
              const ai = resume.ai_analysis;
              const basic = ai?.basic_info || {};
              const scores = ai?.scores || {};
              const analysis = ai?.analysis || {};
              const recommendations = ai?.recommendations || {};
              
              return (
                <div 
                  key={resume.id || index} 
                  className="candidate-card"
                  onClick={() => setSelectedCandidate(resume)}
                >
                  <div className="candidate-header">                  <div className="candidate-name">
                    <h3 title={basic.name || resume.filename}>{basic.name || resume.filename}</h3>
                    <p className="candidate-title" title={ai?.experience?.[0]?.job_title || analysis.specialization_focus || 'Professional'}>
                      {ai?.experience?.[0]?.job_title || analysis.specialization_focus || 'Professional'}
                    </p>
                  </div>
                    <div className="candidate-scores">
                      <span className={`score-badge ${getScoreBadgeClass(scores.overall_score || 0)}`}>
                        {scores.overall_score || 0}
                      </span>
                    </div>
                  </div>
                  
                  <div className="candidate-details">
                    <div className="detail-row">
                      <span className="detail-label">Experience:</span>
                      <span className="detail-value">{analysis.experience_level || 'Unknown'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Location:</span>
                      <span className="detail-value" title={basic.location?.city && basic.location?.country 
                          ? `${basic.location.city}, ${basic.location.country}`
                          : 'Not specified'}>
                        {basic.location?.city && basic.location?.country 
                          ? `${basic.location.city}, ${basic.location.country}`
                          : 'Not specified'}
                      </span>
                    </div>
                    {stats.hasRoleRequirements && (
                      <div className="detail-row">
                        <span className="detail-label">Role Fit:</span>
                        <span className={`score-badge small ${getScoreBadgeClass(scores.role_fit_score || 0)}`}>
                          {scores.role_fit_score || 0}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="candidate-skills">
                    {ai?.skills?.slice(0, 4).map((skill, idx) => (
                      <span key={idx} className="skill-tag small" title={skill}>{skill}</span>
                    ))}
                    {ai?.skills?.length > 4 && (
                      <span className="skill-tag small more" title={`${ai.skills.length - 4} more skills`}>+{ai.skills.length - 4}</span>
                    )}
                  </div>

                  <div className="candidate-recommendation">
                    <span className={`hiring-badge small ${getHiringDecisionBadge(recommendations.hiring_decision)}`}>
                      {recommendations.hiring_decision || 'Pending'}
                    </span>
                    <span className="confidence-level" title={`${recommendations.decision_confidence || 'Unknown'} confidence`}>
                      {recommendations.decision_confidence || 'Unknown'} confidence
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Detailed Table View */
          <div className="detailed-table-container">
            <div className="table-wrapper">
              <table className="detailed-table">
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th>Contact</th>
                    <th>Overall</th>
                    <th>Technical</th>
                    <th>Experience</th>
                    {stats.hasRoleRequirements && <th>Role Fit</th>}
                    <th>Education</th>
                    <th>Communication</th>
                    <th>Leadership</th>
                    <th>Recommendation</th>
                    <th>Specialization</th>
                    <th>Years Exp</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAndSortedResumes.map((resume, index) => {
                    const ai = resume.ai_analysis;
                    const basic = ai?.basic_info || {};
                    const scores = ai?.scores || {};
                    const analysis = ai?.analysis || {};
                    const recommendations = ai?.recommendations || {};
                    
                    return (
                      <tr key={resume.id || index}>
                        <td>
                          <div className="candidate-info">
                            <div className="candidate-name" title={basic.name || resume.filename}>{basic.name || resume.filename}</div>
                            <div className="candidate-subtitle" title={ai?.experience?.[0]?.company || 'Unknown Company'}>
                              {ai?.experience?.[0]?.company || 'Unknown Company'}
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="contact-info">
                            {basic.email && <div className="contact-item" title={basic.email}>📧 {basic.email}</div>}
                            {basic.phone && <div className="contact-item" title={basic.phone}>📞 {basic.phone}</div>}
                            {basic.location?.city && (
                              <div className="contact-item" title={`${basic.location.city}, ${basic.location.country}`}>
                                📍 {basic.location.city}, {basic.location.country}
                              </div>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.overall_score || 0)}`}>
                            {scores.overall_score || 0}
                          </span>
                        </td>
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.technical_skills_score || 0)}`}>
                            {scores.technical_skills_score || 0}
                          </span>
                        </td>
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.experience_score || 0)}`}>
                            {scores.experience_score || 0}
                          </span>
                        </td>
                        {stats.hasRoleRequirements && (
                          <td>
                            <span className={`score-badge ${getScoreBadgeClass(scores.role_fit_score || 0)}`}>
                              {scores.role_fit_score || 0}
                            </span>
                          </td>
                        )}
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.education_score || 0)}`}>
                            {scores.education_score || 0}
                          </span>
                        </td>
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.communication_score || 0)}`}>
                            {scores.communication_score || 0}
                          </span>
                        </td>
                        <td>
                          <span className={`score-badge ${getScoreBadgeClass(scores.leadership_score || 0)}`}>
                            {scores.leadership_score || 0}
                          </span>
                        </td>
                        <td>
                          <div className="recommendation-cell">
                            <span className={`hiring-badge ${getHiringDecisionBadge(recommendations.hiring_decision)}`}>
                              {recommendations.hiring_decision || 'Pending'}
                            </span>
                            <div className="confidence">
                              {recommendations.decision_confidence || 'Unknown'}
                            </div>
                          </div>
                        </td>
                        <td>{analysis.specialization_focus && analysis.specialization_focus.length > 20 
                          ? analysis.specialization_focus.substring(0, 20) + '...' 
                          : analysis.specialization_focus || 'Not specified'}</td>
                        <td>{formatExperienceYears(ai?.experience)}</td>
                        <td>
                          <button 
                            className="action-button view-details"
                            onClick={() => setSelectedCandidate(resume)}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {filteredAndSortedResumes.length === 0 && (
          <div className="no-results">
            <p>No candidates match your search criteria.</p>
          </div>
        )}
      </div>

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal 
          candidate={selectedCandidate} 
          onClose={() => setSelectedCandidate(null)} 
        />
      )}
    </div>
  );
};

export default Dashboard;

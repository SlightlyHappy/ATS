import React, { useState, useMemo } from 'react';
import { 
  BarChart3, 
  Award, 
  TrendingUp, 
  Download, 
  RefreshCw, 
  Trash2, 
  Search,
  Star
} from 'lucide-react';
import Card from './Card';
import Button from './Button';
import TrialRestricted from './TrialRestricted';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard = ({ resumes, roleRequirements, onClearResumes, onExportCSV, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortOrder, setSortOrder] = useState('desc');

  // Statistics calculation
  const stats = useMemo(() => {
    if (resumes.length === 0) return { 
      total: 0, 
      processed: 0,
      averageScore: 0,
      topScorers: 0,
      hasRoleRequirements: false
    };
    
    const successfulResumes = resumes.filter(r => r.status === 'success');
    const scores = successfulResumes.map(r => r.ai_analysis?.overall_score || 0);
    const averageScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    const topScorers = scores.filter(score => score >= 8).length;
    
    return {
      total: resumes.length,
      processed: successfulResumes.length,
      averageScore: averageScore.toFixed(1),
      topScorers,
      hasRoleRequirements: roleRequirements && roleRequirements.job_title
    };
  }, [resumes, roleRequirements]);

  // Filter and sort resumes
  const filteredResumes = useMemo(() => {
    let filtered = resumes.filter(resume => {
      if (!resume.parsed_info) return false;
      const name = resume.parsed_info.name || '';
      const email = resume.parsed_info.email || '';
      return name.toLowerCase().includes(searchTerm.toLowerCase()) ||
             email.toLowerCase().includes(searchTerm.toLowerCase());
    });

    filtered.sort((a, b) => {
      const aVal = a.ai_analysis?.[sortBy] || 0;
      const bVal = b.ai_analysis?.[sortBy] || 0;
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

    return filtered;
  }, [resumes, searchTerm, sortBy, sortOrder]);

  // Chart data
  const scoreDistribution = useMemo(() => {
    const ranges = ['0-2', '2-4', '4-6', '6-8', '8-10'];
    const counts = [0, 0, 0, 0, 0];
    
    resumes.forEach(resume => {
      const score = resume.ai_analysis?.overall_score || 0;
      if (score < 2) counts[0]++;
      else if (score < 4) counts[1]++;
      else if (score < 6) counts[2]++;
      else if (score < 8) counts[3]++;
      else counts[4]++;
    });

    return {
      labels: ranges,
      datasets: [{
        label: 'Number of Candidates',
        data: counts,
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(34, 197, 94, 0.8)',
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(34, 197, 94, 1)',
        ],
        borderWidth: 1
      }]
    };
  }, [resumes]);

  const getScoreColor = (score) => {
    if (score >= 8) return 'var(--color-success)';
    if (score >= 6) return 'var(--color-primary)';
    if (score >= 4) return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  if (resumes.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-xl)', textAlign: 'center', padding: 'var(--spacing-2xl)' }}>
        <div style={{ 
          width: '5rem',
          height: '5rem',
          borderRadius: '50%',
          backgroundColor: 'var(--color-surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-secondary)'
        }}>
          <BarChart3 size={32} />
        </div>
        <div>
          <h2 style={{ color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-sm)' }}>
            No Resumes Uploaded
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-lg)' }}>
            Upload some resume files to see analytics and insights here.
          </p>
        </div>
        <Button variant="primary" icon={RefreshCw} onClick={onRefresh}>
          Refresh Data
        </Button>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: 'var(--spacing-xl)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
            Analytics Dashboard
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Comprehensive analysis of {stats.total} resume{stats.total !== 1 ? 's' : ''}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <Button variant="outline" icon={RefreshCw} onClick={onRefresh}>
            Refresh
          </Button>
          <TrialRestricted feature="export">
            <Button variant="outline" icon={Download} onClick={onExportCSV}>
              Export CSV
            </Button>
          </TrialRestricted>
          <Button variant="danger" icon={Trash2} onClick={onClearResumes}>
            Clear All
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--spacing-lg)' }}>
        <Card padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <div style={{ 
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-primary-light)',
              color: 'var(--color-primary)'
            }}>
              <BarChart3 size={24} />
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                {stats.processed}
              </div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                Processed Resumes
              </div>
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <div style={{ 
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-success-light)',
              color: 'var(--color-success)'
            }}>
              <TrendingUp size={24} />
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                {stats.averageScore}
              </div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                Average Score
              </div>
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <div style={{ 
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--color-warning-light)',
              color: 'var(--color-warning)'
            }}>
              <Award size={24} />
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--color-text-primary)' }}>
                {stats.topScorers}
              </div>
              <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                Top Performers (8+)
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 'var(--spacing-lg)' }}>
        <Card title="Score Distribution" subtitle="Distribution of candidate scores across ranges">
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bar 
              data={scoreDistribution}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      stepSize: 1
                    }
                  }
                }
              }}
            />
          </div>
        </Card>
      </div>

      {/* Candidate List */}
      <Card 
        title="Candidate Rankings" 
        subtitle={`${filteredResumes.length} candidate${filteredResumes.length !== 1 ? 's' : ''} found`}
        action={
          <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'center' }}>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
              <input
                type="text"
                placeholder="Search candidates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  paddingLeft: '2.5rem',
                  paddingRight: 'var(--spacing-md)',
                  paddingTop: 'var(--spacing-sm)',
                  paddingBottom: 'var(--spacing-sm)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.875rem',
                  width: '200px'
                }}
              />
            </div>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
              style={{
                padding: 'var(--spacing-sm) var(--spacing-md)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: '0.875rem'
              }}
            >
              <option value="overall_score-desc">Score (High to Low)</option>
              <option value="overall_score-asc">Score (Low to High)</option>
              <option value="technical_skills-desc">Technical Skills</option>
              <option value="experience_match-desc">Experience Match</option>
            </select>
          </div>
        }
      >
        <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
          {filteredResumes.map((resume, index) => (
            <div
              key={resume.id || index}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 'var(--spacing-lg)',
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                transition: 'all var(--transition-fast)',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-border)';
                e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)', flex: 1, minWidth: 0 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  width: '3rem',
                  height: '3rem',
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-primary-light)',
                  color: 'var(--color-primary)',
                  fontWeight: '600',
                  fontSize: '1.125rem'
                }}>
                  {resume.parsed_info?.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: '600', color: 'var(--color-text-primary)', marginBottom: 'var(--spacing-xs)' }}>
                    {resume.parsed_info?.name || 'Unknown Candidate'}
                  </div>
                  <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--spacing-xs)' }}>
                    {resume.parsed_info?.email || 'No email provided'}
                  </div>
                  {resume.ai_analysis?.summary && (
                    <div style={{ color: 'var(--color-text-tertiary)', fontSize: '0.75rem', lineHeight: 1.4 }}>
                      {resume.ai_analysis.summary.substring(0, 100)}...
                    </div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ 
                    fontSize: '1.5rem', 
                    fontWeight: '700', 
                    color: getScoreColor(resume.ai_analysis?.overall_score || 0),
                    marginBottom: 'var(--spacing-xs)'
                  }}>
                    {resume.ai_analysis?.overall_score?.toFixed(1) || 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                    Overall Score
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      size={16}
                      fill={i < Math.round((resume.ai_analysis?.overall_score || 0) / 2) ? 'currentColor' : 'none'}
                      style={{ color: 'var(--color-warning)' }}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;

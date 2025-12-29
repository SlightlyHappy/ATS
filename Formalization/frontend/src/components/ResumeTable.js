import React, { useState, useMemo } from 'react';
import { Download, Filter, Trash2 } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import { useTrial } from '../contexts/TrialContext';
import { useAuth } from '../contexts/AuthContext';
import UpgradePrompt from './UpgradePrompt';

const ResumeTable = ({ resumes, onDelete }) => {
  const [sortBy, setSortBy] = useState('score');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterText, setFilterText] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const { isTrialActive, getExportRestriction } = useTrial();
  const { user } = useAuth();

  // Check export restrictions
  const { canExport, message: exportMessage } = isTrialActive ? getExportRestriction() : { canExport: true };

  const sortedResumes = useMemo(() => {
    const filteredResumes = resumes.filter(resume => 
      resume.name.toLowerCase().includes(filterText.toLowerCase()) ||
      (resume.skills && resume.skills.toLowerCase().includes(filterText.toLowerCase())) ||
      (resume.experience && resume.experience.toLowerCase().includes(filterText.toLowerCase()))
    );

    return [...filteredResumes].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      // Handle numeric sorting
      if (typeof aValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Handle string sorting
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      return 0;
    });
  }, [resumes, sortBy, sortDirection, filterText]);

  const handleExport = async () => {
    if (isTrialActive && !canExport) {
      alert(exportMessage);
      return;
    }

    // Generate CSV from data
    const headers = ['Name', 'Skills', 'Experience', 'Education', 'Score'];
    const csvContent = [
      headers.join(','),
      ...sortedResumes.map(resume => [
        `"${resume.name || ''}"`,
        `"${resume.skills || ''}"`,
        `"${resume.experience || ''}"`,
        `"${resume.education || ''}"`,
        resume.score || 0
      ].join(','))
    ].join('\\n');

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'resume_analysis.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (column) => {
    if (sortBy !== column) return null;
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  return (
    <Card title="Resume Analysis Results" className="w-full">
      <div className="mb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center">
        <div className="flex flex-col sm:flex-row gap-2 sm:items-center mb-4 sm:mb-0">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter size={16} className="mr-1" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
          
          {showFilters && (
            <input
              type="text"
              placeholder="Filter by name, skills, or experience..."
              className="px-3 py-1 border border-gray-300 rounded text-sm"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
            />
          )}
        </div>
        
        <div className="flex gap-2">
          <Button 
            variant="primary" 
            size="sm" 
            onClick={handleExport} 
            disabled={sortedResumes.length === 0 || (isTrialActive && !canExport)}
          >
            <Download size={16} className="mr-1" />
            Export CSV
          </Button>
        </div>
      </div>
      
      {/* Show upgrade prompt when export is restricted */}
      {isTrialActive && !canExport && sortedResumes.length > 0 && (
        <div className="mb-4">
          <UpgradePrompt 
            title="CSV Export Restricted"
            message="CSV export is limited in trial mode. Upgrade to gain full access to all export features."
            actionText="Upgrade for Export"
          />
        </div>
      )}
      
      {sortedResumes.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          No resume data found. Upload resumes to see analysis results here.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700 text-sm">
            <thead>
              <tr>
                <th 
                  onClick={() => handleSort('name')}
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-800"
                >
                  Name {getSortIcon('name')}
                </th>
                <th 
                  onClick={() => handleSort('skills')}
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-800"
                >
                  Skills {getSortIcon('skills')}
                </th>
                <th 
                  onClick={() => handleSort('experience')}
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-800"
                >
                  Experience {getSortIcon('experience')}
                </th>
                <th 
                  onClick={() => handleSort('score')}
                  className="px-6 py-3 text-left cursor-pointer hover:bg-gray-800"
                >
                  Score {getSortIcon('score')}
                </th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {sortedResumes.map((resume, index) => (
                <tr key={index} className="hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap">{resume.name}</td>
                  <td className="px-6 py-4">
                    <div className="truncate max-w-xs">{resume.skills}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="truncate max-w-xs">{resume.experience}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="h-2 w-16 bg-gray-700 rounded-full">
                        <div 
                          className={`h-2 rounded-full ${
                            resume.score >= 80 ? 'bg-green-500' :
                            resume.score >= 60 ? 'bg-blue-500' :
                            resume.score >= 40 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${resume.score}%` }}
                        />
                      </div>
                      <span className="ml-2 text-sm">{resume.score}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => onDelete(index)} 
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

export default ResumeTable;

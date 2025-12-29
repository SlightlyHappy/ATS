'use client';


import React, { useEffect, useState } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { ProtectedRoute, useAuth } from '@/context/AuthContext';
import { Card } from '@/components/ui/Card';

// Types for API responses
interface ResumeAnalysis {
  id: number | string;
  candidate_name: string;
  user_email: string;
  ai_score: number;
  processing_time: number; // ms
  status: string;
  created_at: string;
}

interface AgentScores {
  technical_skills: number;
  experience: number;
  cultural_fit: number;
  legal_compliance: number;
}

const AdminResumesPage: React.FC = () => {
  const { apiRequest } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [recentResumes, setRecentResumes] = useState<ResumeAnalysis[]>([]);
  const [agentScores, setAgentScores] = useState<AgentScores | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Get admin stats (aggregates, agent scores, queue, etc)
        const statsRes = await apiRequest('/api/admin/stats');
        setStats(statsRes.data || statsRes);

        // Get recent resume analyses (limit 10)
        const resumesRes = await apiRequest('/api/resumes?limit=10');
        setRecentResumes(resumesRes.resumes || resumesRes.data || []);

        // Extract agent scores if present
        if (statsRes.data && statsRes.data.agent_scores) {
          setAgentScores(statsRes.data.agent_scores);
        }
      } catch (e) {
        setStats(null);
        setRecentResumes([]);
        setAgentScores(null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [apiRequest]);

  return (
    <ProtectedRoute adminOnly={true}>
      <AdminLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Resume Analysis</h2>
              <p className="text-gray-600 mt-1">Monitor AI-powered resume processing and analysis results</p>
            </div>
          </div>

          {/* Processing Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Resumes</p>
                  <p className="text-2xl font-semibold text-gray-900">{loading ? 'Loading...' : stats?.total_resumes ?? '-'}</p>
                  <p className="text-sm text-blue-600">All uploads</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Processed Today</p>
                  <p className="text-2xl font-semibold text-gray-900">{loading ? 'Loading...' : stats?.processed_today ?? '-'}</p>
                  <p className="text-sm text-green-600">AI analyzed</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
                  <p className="text-2xl font-semibold text-gray-900">{loading ? 'Loading...' : stats?.avg_processing_time ? `${stats.avg_processing_time}s` : '-'}</p>
                  <p className="text-sm text-green-600">{stats?.processing_time_trend ?? ''}</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">AI Score Average</p>
                  <p className="text-2xl font-semibold text-gray-900">{loading ? 'Loading...' : stats?.ai_score_avg ?? '-'}</p>
                  <p className="text-sm text-gray-600">{stats?.score_calibration ?? ''}</p>
                </div>
              </div>
            </Card>
          </div>

          {/* AI Agent Performance */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Agent Performance</h3>
            <div className="space-y-3">
              {agentScores ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Technical Skills Agent</span>
                    <span className="text-sm font-medium">{agentScores.technical_skills}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Experience Agent</span>
                    <span className="text-sm font-medium">{agentScores.experience}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Cultural Fit Agent</span>
                    <span className="text-sm font-medium">{agentScores.cultural_fit}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Legal Compliance Agent</span>
                    <span className="text-sm font-medium">{agentScores.legal_compliance}%</span>
                  </div>
                </>
              ) : (
                <span className="text-gray-500">Loading...</span>
              )}
            </div>
          </Card>

          {/* Recent Resume Analysis */}
          <Card>
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Recent Resume Analysis</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AI Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Processing Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr><td colSpan={6} className="text-center py-6 text-gray-500">Loading...</td></tr>
                  ) : recentResumes.length === 0 ? (
                    <tr><td colSpan={6} className="text-center py-6 text-gray-500">No recent resume analyses found.</td></tr>
                  ) : (
                    recentResumes.map((resume) => (
                      <tr key={resume.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{resume.candidate_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {resume.user_email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            resume.ai_score >= 85 ? 'bg-green-100 text-green-800' :
                            resume.ai_score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {resume.ai_score}/100
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {resume.processing_time ? `${(resume.processing_time / 1000).toFixed(2)}s` : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            resume.status === 'completed' ? 'bg-green-100 text-green-800' :
                            resume.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {resume.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {resume.created_at ? new Date(resume.created_at).toLocaleString() : '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
};

export default AdminResumesPage;

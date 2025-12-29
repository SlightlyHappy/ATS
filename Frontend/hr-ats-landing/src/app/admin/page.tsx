'use client';

import React, { useState, useEffect } from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import { ProtectedRoute, useAuth } from '@/context/AuthContext';

interface AdminStats {
  users: {
    total_users: number;
    trial_users: number;
    premium_users: number;
    enterprise_users: number;
    users_created_today: number;
  };
  resumes: {
    total_resumes: number;
    analyses_completed: number;
    pending_queue: number;
    average_processing_time: number;
  };
  credits: {
    trial_credits_used: number;
    premium_credits_sold: number;
    trial_exhausted_users: number;
  };
  system: {
    railway_db_status: string;
    ai_processing_status: string;
    queue_status: string;
  };
}

const AdminDashboard: React.FC = () => {
  const { apiRequest } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAdminStats = async () => {
      try {
        setLoading(true);
        const response = await apiRequest('/api/admin/stats');
        if (response.success) {
          setStats(response.data);
        } else {
          setError(response.message || 'Failed to load admin statistics');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load admin statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminStats();
  }, [apiRequest]);

  if (loading) {
    return (
      <ProtectedRoute adminOnly={true}>
        <AdminLayout>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </AdminLayout>
      </ProtectedRoute>
    );
  }

  if (error) {
    return (
      <ProtectedRoute adminOnly={true}>
        <AdminLayout>
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        </AdminLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute adminOnly={true}>
      <AdminLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
            <p className="text-gray-600">
              Railway PostgreSQL powered HR ATS system administration
            </p>
          </div>

          {/* System Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Railway Database</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    stats?.system.railway_db_status === 'healthy' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {stats?.system.railway_db_status || 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">AI Processing</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    stats?.system.ai_processing_status === 'online' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {stats?.system.ai_processing_status || 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Queue Status</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    stats?.system.queue_status === 'normal' 
                      ? 'bg-green-100 text-green-800' 
                      : stats?.system.queue_status === 'busy'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {stats?.system.queue_status || 'Unknown'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">User Statistics</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Users</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.users.total_users || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Trial Users</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.users.trial_users || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Premium Users</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.users.premium_users || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">New Today</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.users.users_created_today || 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Statistics</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Resumes</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.resumes.total_resumes || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Completed</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.resumes.analyses_completed || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">In Queue</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.resumes.pending_queue || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Avg Time</span>
                  <span className="text-sm font-medium text-gray-900">{stats?.resumes.average_processing_time || 0}ms</span>
                </div>
              </div>
            </div>
          </div>

          {/* Credit Management Overview */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Credit System Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats?.credits.trial_credits_used || 0}</div>
                <div className="text-sm text-gray-600">Trial Credits Used</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats?.credits.premium_credits_sold || 0}</div>
                <div className="text-sm text-gray-600">Premium Credits Sold</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{stats?.credits.trial_exhausted_users || 0}</div>
                <div className="text-sm text-gray-600">Trial Exhausted Users</div>
              </div>
            </div>
          </div>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
};

export default AdminDashboard;

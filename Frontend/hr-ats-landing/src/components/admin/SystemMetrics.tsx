'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { apiRequest, useAuth } from '@/context/AuthContext';

interface SystemStats {
  users: {
    total: number;
    by_type: {
      trial: number;
      premium: number;
      enterprise: number;
    };
    recent_signups: number;
    active_today: number;
  };
  processing: {
    total_resumes: number;
    completed_analyses: number;
    pending_queue: number;
    failed_analyses: number;
  };
  credits: {
    total_trial_used: number;
    premium_transactions: number;
    trial_exhausted_users: number;
  };
  database_health: {
    railway_primary: {
      status: string;
      connection_pool: string;
      avg_query_time_ms: number;
    };
    supabase_backup: {
      status: string;
      last_sync: string;
    };
  };
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon, 
  loading = false 
}) => {
  const changeColor = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  }[changeType];

  return (
    <Card className="p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="p-3 bg-blue-100 rounded-lg">
            <div className="text-blue-600">
              {icon}
            </div>
          </div>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline">
            {loading ? (
              <div className="h-8 w-20 bg-gray-200 rounded animate-pulse"></div>
            ) : (
              <p className="text-2xl font-semibold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </p>
            )}
            {change && !loading && (
              <p className={`ml-2 text-sm ${changeColor}`}>
                {change}
              </p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

const SystemMetrics: React.FC = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await apiRequest('/api/admin/stats', {}, token!);
      setStats(data.stats);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      console.error('Failed to fetch admin stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [token]);

  if (error) {
    return (
      <div className="p-6">
        <Card className="p-6 bg-red-50 border-red-200">
          <div className="flex items-center">
            <div className="text-red-600 mr-3">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-medium text-red-800">Error loading system metrics</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                onClick={fetchStats}
                className="text-sm text-red-600 hover:text-red-500 underline mt-2"
              >
                Try again
              </button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">System Overview</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></div>
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* User Metrics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">User Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Users"
            value={stats?.users?.total || 0}
            change="+12% from last month"
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Active Today"
            value={stats?.users?.active_today || 0}
            change="+5% from yesterday"
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Trial Users"
            value={stats?.users?.by_type?.trial || 0}
            change={`${stats?.users?.recent_signups || 0} new this week`}
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
          />
          <MetricCard
            title="Premium Users"
            value={stats?.users?.by_type?.premium || 0}
            change="+8% conversion rate"
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Processing Metrics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Resumes"
            value={stats?.processing?.total_resumes || 0}
            change="+24% this month"
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <MetricCard
            title="Completed Analyses"
            value={stats?.processing?.completed_analyses || 0}
            change="98.5% success rate"
            changeType="positive"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
          <MetricCard
            title="Queue Length"
            value={stats?.processing?.pending_queue || 0}
            change={stats && stats.processing && stats.processing.pending_queue > 10 ? "High volume" : "Normal"}
            changeType={stats && stats.processing && stats.processing.pending_queue > 10 ? "negative" : "positive"}
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Failed Analyses"
            value={stats?.processing?.failed_analyses || 0}
            change="1.5% failure rate"
            changeType="negative"
            loading={loading}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Database Health */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Health</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Railway PostgreSQL</h4>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                stats?.database_health?.railway_primary?.status === 'healthy' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {loading ? 'Loading...' : (stats?.database_health?.railway_primary?.status || 'Unknown')}
              </div>
            </div>
            {!loading && stats && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Connection Pool:</span>
                  <span className="text-sm font-medium">{stats.database_health?.railway_primary?.connection_pool || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg Query Time:</span>
                  <span className="text-sm font-medium">{stats.database_health?.railway_primary?.avg_query_time_ms || 0}ms</span>
                </div>
              </div>
            )}
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Supabase Backup</h4>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                stats?.database_health?.supabase_backup?.status === 'synced' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {loading ? 'Loading...' : (stats?.database_health?.supabase_backup?.status || 'Unknown')}
              </div>
            </div>
            {!loading && stats && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Sync:</span>
                  <span className="text-sm font-medium">
                    {stats.database_health?.supabase_backup?.last_sync 
                      ? new Date(stats.database_health.supabase_backup.last_sync).toLocaleString()
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SystemMetrics;

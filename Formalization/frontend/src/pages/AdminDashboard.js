import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  BarChart3, 
  Activity,
  TrendingUp,
  Shield,
  Database,
  RefreshCw,
  Search,
  Trash2,
  RotateCcw,
  Eye
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Card from '../components/Card';
import Button from '../components/Button';
import LoadingSpinner from '../components/LoadingSpinner';
import FullApp from './FullApp';
import TrialApp from './TrialApp';
import axios from 'axios';
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
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  LineElement,
  PointElement
);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AdminDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUserType, setSelectedUserType] = useState('');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [supabaseStatus, setSupabaseStatus] = useState(null);
  const [syncInProgress, setSyncInProgress] = useState(false);

  // Form state for creating/editing users
  const [userForm, setUserForm] = useState({
    email: '',
    name: '',
    password: '',
    access_type: 'trial'
  });

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardStats();
      loadAnalytics();
      loadSystemHealth();
    } else if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'supabase') {
      loadSupabaseStatus();
    }
  }, [activeTab, pagination.page, searchTerm, selectedUserType]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadDashboardStats = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/admin/dashboard-stats`);
      if (response.data.success) {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        limit: pagination.limit.toString(),
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (selectedUserType) params.append('access_type', selectedUserType);

      const response = await axios.get(`${API_BASE_URL}/api/admin/users?${params}`);
      if (response.data.success) {
        setUsers(response.data.users);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/analytics`);
      if (response.data.success) {
        setAnalytics(response.data.analytics);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const loadSystemHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/system-health`);
      if (response.data.success) {
        setSystemHealth(response.data.health);
      }
    } catch (error) {
      console.error('Error loading system health:', error);
    }
  };

  const loadSupabaseStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/admin/supabase-status`);
      if (response.data.success) {
        setSupabaseStatus(response.data.status);
      }
    } catch (error) {
      console.error('Error loading Supabase status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncToSupabase = async (confirmDelete = false) => {
    if (!window.confirm(`Are you sure you want to sync all SQLite users to Supabase?${confirmDelete ? ' This will DELETE SQLite users after successful sync!' : ''}`)) {
      return;
    }

    try {
      setSyncInProgress(true);
      const response = await axios.post(`${API_BASE_URL}/api/admin/sync-users-to-supabase`, {
        confirm_delete_after_sync: confirmDelete
      });
      
      if (response.data.success) {
        alert(`Sync completed! 
✅ Successfully synced: ${response.data.results.synced_successfully}
⚠️  Already existed: ${response.data.results.already_exists}
❌ Failed: ${response.data.results.failed}
${confirmDelete && response.data.results.sqlite_users_deleted ? `🗑️  Deleted ${response.data.results.sqlite_users_deleted} SQLite users` : ''}`);
        
        // Reload status
        loadSupabaseStatus();
        loadUsers(); // Refresh user list
      } else {
        alert('Sync failed: ' + response.data.error);
      }
    } catch (error) {
      alert('Sync error: ' + (error.response?.data?.error || error.message));
    } finally {
      setSyncInProgress(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/api/admin/users`, userForm);
      if (response.data.success) {
        setShowCreateUser(false);
        setUserForm({ email: '', name: '', password: '', access_type: 'trial' });
        loadUsers();
        alert('User created successfully!');
      }
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line no-unused-vars
  const handleUpdateUser = async (userId, updates) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/api/admin/users/${userId}`, updates);
      if (response.data.success) {
        loadUsers();
        alert('User updated successfully!');
      }
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to update user');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        const response = await axios.delete(`${API_BASE_URL}/api/admin/users/${userId}`);
        if (response.data.success) {
          loadUsers();
          alert('User deleted successfully!');
        }
      } catch (error) {
        alert(error.response?.data?.error || 'Failed to delete user');
      }
    }
  };

  const handleResetTrial = async (userId) => {
    if (window.confirm('Are you sure you want to reset this user\'s trial?')) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/admin/users/${userId}/reset-trial`);
        if (response.data.success) {
          loadUsers();
          alert('Trial reset successfully!');
        }
      } catch (error) {
        alert(error.response?.data?.error || 'Failed to reset trial');
      }
    }
  };

  // Chart data preparation
  const userTypeChartData = stats ? {
    labels: Object.keys(stats.users.by_type),
    datasets: [{
      data: Object.values(stats.users.by_type),
      backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
      borderWidth: 0,
    }]
  } : null;

  const userGrowthChartData = analytics?.user_growth ? {
    labels: analytics.user_growth.map(d => d.date),
    datasets: [{
      label: 'New Users',
      data: analytics.user_growth.map(d => d.count),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      tension: 0.4,
    }]
  } : null;

  const resumeProcessingChartData = analytics?.resume_processing ? {
    labels: analytics.resume_processing.map(d => d.date),
    datasets: [{
      label: 'Resumes Processed',
      data: analytics.resume_processing.map(d => d.count),
      backgroundColor: '#10b981',
      borderRadius: 4,
    }]
  } : null;

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <Shield className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">You don't have admin privileges to access this page.</p>
        </Card>
      </div>
    );
  }

  return (
      <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
              <p className="text-gray-600">Manage users, view analytics, and monitor system health</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Button
                  variant={activeTab.includes('app') ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setActiveTab('resume-app')}
                >
                  Resume App
                </Button>
                <Button
                  variant={!activeTab.includes('app') ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setActiveTab('dashboard')}
                >
                  Admin Panel
                </Button>
              </div>
              <Button
                variant="outline"
                icon={RefreshCw}
                onClick={() => {
                  if (activeTab === 'dashboard') {
                    loadDashboardStats();
                    loadAnalytics();
                    loadSystemHealth();
                  } else if (activeTab === 'users') {
                    loadUsers();
                  }
                }}
              >
                Refresh
              </Button>
              <div className="text-sm text-gray-500">
                Welcome, {user.name}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Overview', icon: BarChart3 },
              { id: 'users', label: 'User Management', icon: Users },
              { id: 'analytics', label: 'Analytics', icon: TrendingUp },
              { id: 'system', label: 'System Health', icon: Activity },
              { id: 'supabase', label: 'Supabase Sync', icon: Database },
              { id: 'resume-app', label: 'Resume Analyzer', icon: Database },
              { id: 'trial-app', label: 'Trial Features', icon: Eye }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="large" />
          </div>
        )}

        {/* Dashboard Overview */}
        {activeTab === 'dashboard' && stats && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-8 w-8 text-blue-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.users.total}</p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UserPlus className="h-8 w-8 text-green-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">New Users (30d)</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.users.recent}</p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Database className="h-8 w-8 text-purple-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Resumes</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.system.total_resumes}</p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Activity className="h-8 w-8 text-orange-500" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active Sessions</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.system.active_sessions}</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* User Types Distribution */}
              {userTypeChartData && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Users by Type</h3>
                  <div className="h-64">
                    <Doughnut 
                      data={userTypeChartData}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                          },
                        },
                      }}
                    />
                  </div>
                </Card>
              )}

              {/* Trial Usage Statistics */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trial Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Total Analyzed</span>
                    <span className="font-semibold">{stats.users.trial_stats.total_analyzed}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Average per User</span>
                    <span className="font-semibold">{stats.users.trial_stats.avg_analyzed}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Users at Limit</span>
                    <span className="font-semibold text-red-600">{stats.users.trial_stats.at_limit}</span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Growth Charts */}
            {userGrowthChartData && resumeProcessingChartData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">User Growth (30 days)</h3>
                  <div className="h-64">
                    <Line 
                      data={userGrowthChartData}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          y: {
                            beginAtZero: true,
                          },
                        },
                      }}
                    />
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Resume Processing (30 days)</h3>
                  <div className="h-64">
                    <Bar 
                      data={resumeProcessingChartData}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                          y: {
                            beginAtZero: true,
                          },
                        },
                      }}
                    />
                  </div>
                </Card>
              </div>
            )}
          </div>
        )}

        {/* User Management */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            {/* User Management Header */}
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
                <p className="text-gray-600">Manage user accounts and access levels</p>
              </div>
              <Button
                variant="primary"
                icon={UserPlus}
                onClick={() => setShowCreateUser(true)}
              >
                Create User
              </Button>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <input
                      type="text"
                      placeholder="Search users by email or name..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="w-48">
                  <select
                    value={selectedUserType}
                    onChange={(e) => setSelectedUserType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All User Types</option>
                    <option value="trial">Trial</option>
                    <option value="full">Full Access</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Users Table */}
            <Card>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Access Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Trial Usage
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Login
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{user.name}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.access_type === 'admin' ? 'bg-purple-100 text-purple-800' :
                            user.access_type === 'full' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {user.access_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {user.access_type === 'trial' ? (
                            <div>
                              <div className="text-sm">{user.trial_resumes_analyzed} / {user.trial_limit}</div>
                              <div className="w-24 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-blue-600 h-2 rounded-full" 
                                  style={{ width: `${(user.trial_resumes_analyzed / user.trial_limit) * 100}%` }}
                                ></div>
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-500">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.last_login ? formatDate(user.last_login) : 'Never'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => setSelectedUser(user)}
                              className="text-indigo-600 hover:text-indigo-900"
                              title="View Details"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {user.access_type === 'trial' && (
                              <button
                                onClick={() => handleResetTrial(user.id)}
                                className="text-green-600 hover:text-green-900"
                                title="Reset Trial"
                              >
                                <RotateCcw className="h-4 w-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="text-red-600 hover:text-red-900"
                              title="Delete User"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination.pages > 1 && (
                <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <Button
                      variant="outline"
                      disabled={pagination.page === 1}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      disabled={pagination.page === pagination.pages}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    >
                      Next
                    </Button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Showing page {pagination.page} of {pagination.pages} ({pagination.total} total users)
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                        const page = i + 1;
                        return (
                          <button
                            key={page}
                            onClick={() => setPagination(prev => ({ ...prev, page }))}
                            className={`px-3 py-2 text-sm rounded-md ${
                              pagination.page === page
                                ? 'bg-blue-600 text-white'
                                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {page}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && analytics && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">Analytics</h2>
            
            {/* Top Users */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Users by Resume Analysis</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">User</th>
                      <th className="text-left py-2">Type</th>
                      <th className="text-right py-2">Resumes Analyzed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.top_users.map((user, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2">
                          <div>
                            <div className="font-medium">{user.name}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </td>
                        <td className="py-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.access_type === 'full' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {user.access_type}
                          </span>
                        </td>
                        <td className="py-2 text-right font-semibold">{user.resumes_analyzed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* System Health Tab */}
        {activeTab === 'system' && systemHealth && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Memory Usage */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory Usage</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Used</span>
                    <span>{systemHealth.memory.percent.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full ${
                        systemHealth.memory.percent > 80 ? 'bg-red-500' :
                        systemHealth.memory.percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemHealth.memory.percent}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatBytes(systemHealth.memory.total - systemHealth.memory.available)} / {formatBytes(systemHealth.memory.total)}
                  </div>
                </div>
              </Card>

              {/* Disk Usage */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Disk Usage</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Used</span>
                    <span>{systemHealth.disk.percent.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full ${
                        systemHealth.disk.percent > 80 ? 'bg-red-500' :
                        systemHealth.disk.percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${systemHealth.disk.percent}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatBytes(systemHealth.disk.total - systemHealth.disk.free)} / {formatBytes(systemHealth.disk.total)}
                  </div>
                </div>
              </Card>

              {/* Database Size */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Database</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Size</span>
                    <span>{formatBytes(systemHealth.database.size)}</span>
                  </div>
                </div>
              </Card>

              {/* Storage Stats */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Cache</h3>
                <div className="space-y-2">
                  {Object.entries(systemHealth.storage).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace('_', ' ')}</span>
                      <span>{typeof value === 'number' ? value.toLocaleString() : value}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Supabase Sync Tab */}
        {activeTab === 'supabase' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Supabase Integration</h2>
                <p className="text-gray-600">Manage authentication sync between SQLite and Supabase</p>
              </div>
              <Button
                variant="outline"
                icon={RefreshCw}
                onClick={() => loadSupabaseStatus()}
              >
                Refresh Status
              </Button>
            </div>

            {supabaseStatus && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Supabase Connection Status */}
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Database className={`h-8 w-8 ${supabaseStatus.supabase_available ? 'text-green-500' : 'text-red-500'}`} />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Supabase Status</p>
                      <p className={`text-lg font-bold ${supabaseStatus.supabase_available ? 'text-green-600' : 'text-red-600'}`}>
                        {supabaseStatus.supabase_available ? 'Connected' : 'Disconnected'}
                      </p>
                    </div>
                  </div>
                </Card>

                {/* SQLite Users Count */}
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Users className="h-8 w-8 text-blue-500" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">SQLite Users</p>
                      <p className="text-2xl font-bold text-gray-900">{supabaseStatus.sqlite_users_count}</p>
                    </div>
                  </div>
                </Card>

                {/* Users Needing Sync */}
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <RefreshCw className="h-8 w-8 text-orange-500" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Need Sync</p>
                      <p className="text-2xl font-bold text-gray-900">{supabaseStatus.users_needing_sync}</p>
                    </div>
                  </div>
                </Card>

                {/* Users Already Synced */}
                <Card className="p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Shield className="h-8 w-8 text-green-500" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Already Synced</p>
                      <p className="text-2xl font-bold text-gray-900">{supabaseStatus.users_already_synced}</p>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Sync Actions */}
            {supabaseStatus && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sync Operations</h3>
                
                {supabaseStatus.supabase_available ? (
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-semibold text-blue-900 mb-2">Migration Process</h4>
                      <p className="text-sm text-blue-700 mb-4">
                        This will migrate all SQLite users to Supabase. Users will need to reset their passwords after migration.
                      </p>
                      
                      <div className="flex flex-col sm:flex-row gap-3">
                        <Button
                          variant="primary"
                          onClick={() => handleSyncToSupabase(false)}
                          disabled={syncInProgress || supabaseStatus.users_needing_sync === 0}
                          loading={syncInProgress}
                        >
                          {syncInProgress ? 'Syncing...' : 'Sync to Supabase (Keep SQLite)'}
                        </Button>
                        
                        <Button
                          variant="danger"
                          onClick={() => handleSyncToSupabase(true)}
                          disabled={syncInProgress || supabaseStatus.users_needing_sync === 0}
                          loading={syncInProgress}
                        >
                          Sync & Delete SQLite Users
                        </Button>
                      </div>
                      
                      {supabaseStatus.users_needing_sync === 0 && (
                        <p className="text-sm text-green-600 mt-2">
                          ✅ All users are already synced to Supabase
                        </p>
                      )}
                    </div>

                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Important Notes</h4>
                      <ul className="text-sm text-yellow-700 space-y-1">
                        <li>• Users will receive temporary passwords and must reset them</li>
                        <li>• SQLite serves as backup until Supabase sync is confirmed</li>
                        <li>• "Sync & Delete" permanently removes SQLite users</li>
                        <li>• Always test with a few users before bulk migration</li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="font-semibold text-red-900 mb-2">❌ Supabase Unavailable</h4>
                    <p className="text-sm text-red-700">
                      Supabase is not connected. Check your environment variables and connection settings.
                    </p>
                  </div>
                )}
              </Card>
            )}
          </div>
        )}

        {/* Resume Analyzer Tab - Full App */}
        {activeTab === 'resume-app' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h2 className="text-xl font-semibold text-blue-900 mb-2">Resume Analyzer - Full Features</h2>
              <p className="text-blue-700">You're accessing the full resume analysis application with all premium features enabled.</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm">
              <FullApp />
            </div>
          </div>
        )}

        {/* Trial Features Tab */}
        {activeTab === 'trial-app' && (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <h2 className="text-xl font-semibold text-green-900 mb-2">Trial Features Preview</h2>
              <p className="text-green-700">Experience the trial version of the application to understand the user experience.</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm">
              <TrialApp />
            </div>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New User</h3>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <input
                    type="email"
                    required
                    value={userForm.email}
                    onChange={(e) => setUserForm(prev => ({ ...prev, email: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <input
                    type="text"
                    required
                    value={userForm.name}
                    onChange={(e) => setUserForm(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Password</label>
                  <input
                    type="password"
                    required
                    value={userForm.password}
                    onChange={(e) => setUserForm(prev => ({ ...prev, password: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Access Type</label>
                  <select
                    value={userForm.access_type}
                    onChange={(e) => setUserForm(prev => ({ ...prev, access_type: e.target.value }))}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="trial">Trial</option>
                    <option value="full">Full Access</option>
                  </select>
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateUser(false);
                      setUserForm({ email: '', name: '', password: '', access_type: 'trial' });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={loading}>
                    {loading ? 'Creating...' : 'Create User'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* User Details Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">User Details</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedUser.name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedUser.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Access Type</label>
                  <p className="mt-1">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      selectedUser.access_type === 'admin' ? 'bg-purple-100 text-purple-800' :
                      selectedUser.access_type === 'full' ? 'bg-green-100 text-green-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {selectedUser.access_type}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Created</label>
                  <p className="mt-1 text-sm text-gray-900">{formatDate(selectedUser.created_at)}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Login</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedUser.last_login ? formatDate(selectedUser.last_login) : 'Never'}
                  </p>
                </div>
                {selectedUser.created_by_admin && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Created By</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedUser.created_by_admin}</p>
                  </div>
                )}
                {selectedUser.access_type === 'trial' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Trial Usage</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedUser.trial_resumes_analyzed} / {selectedUser.trial_limit} resumes analyzed
                    </p>
                  </div>
                )}
              </div>
              <div className="flex justify-end pt-4">
                <Button
                  variant="outline"
                  onClick={() => setSelectedUser(null)}
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;

'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { apiRequest, useAuth } from '@/context/AuthContext';

interface User {
  user_id: number;
  email: string;
  name: string;
  access_type: 'trial' | 'premium' | 'enterprise';
  is_admin: boolean;
  created_at: string;
  last_login?: string;
  trial_resumes_analyzed: number;
  trial_legal_queries: number;
  status: string;
}

interface UserListResponse {
  success: boolean;
  users: User[];
  total_count: number;
  has_next: boolean;
}

const UserManagement: React.FC = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);

  const fetchUsers = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      const data: UserListResponse = await apiRequest(
        `/api/admin/users?page=${pageNum}&limit=10&include_credits=true&include_usage=true`,
        {},
        token!
      );
      
      if (data.success) {
        setUsers(data.users);
        setTotalCount(data.total_count);
        setHasNext(data.has_next);
        setPage(pageNum);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
  }, [token]);

  const handleUserAction = async (userId: number, action: string) => {
    try {
      switch (action) {
        case 'reset_credits':
          await apiRequest(`/api/admin/users/${userId}/credits/reset`, { method: 'POST' }, token!);
          break;
        case 'upgrade_premium':
          await apiRequest(`/api/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ access_type: 'premium' })
          }, token!);
          break;
        case 'deactivate':
          await apiRequest(`/api/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ status: 'inactive' })
          }, token!);
          break;
      }
      
      // Refresh users list
      fetchUsers(page);
    } catch (err) {
      console.error(`Failed to ${action}:`, err);
      alert(`Failed to ${action}. Please try again.`);
    }
  };

  const getStatusBadge = (user: User) => {
    if (user.is_admin) {
      return <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">Admin</span>;
    }
    
    const statusColors = {
      trial: 'bg-blue-100 text-blue-800',
      premium: 'bg-green-100 text-green-800',
      enterprise: 'bg-purple-100 text-purple-800'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[user.access_type]}`}>
        {user.access_type.charAt(0).toUpperCase() + user.access_type.slice(1)}
      </span>
    );
  };

  if (loading && users.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
        </div>
        <Card className="p-6">
          <div className="animate-pulse">
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
        </div>
        <Card className="p-6 bg-red-50 border-red-200">
          <div className="text-center">
            <div className="text-red-600 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-red-800 mb-2">Failed to load users</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <Button onClick={() => fetchUsers(page)} size="sm">
              Try Again
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
          <p className="text-gray-600 mt-1">Manage users, credits, and access levels</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Create New User
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{totalCount}</div>
            <div className="text-sm text-gray-600">Total Users</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {users.filter(u => u.access_type === 'trial').length}
            </div>
            <div className="text-sm text-gray-600">Trial Users</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {users.filter(u => u.access_type === 'premium').length}
            </div>
            <div className="text-sm text-gray-600">Premium Users</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {users.filter(u => u.is_admin).length}
            </div>
            <div className="text-sm text-gray-600">Administrators</div>
          </div>
        </Card>
      </div>

      {/* Users Table */}
      <Card>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">All Users</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Joined
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.user_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                        <span className="text-sm font-medium text-white">
                          {user.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(user)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>Resumes: {user.trial_resumes_analyzed}</div>
                    <div className="text-gray-500">Legal: {user.trial_legal_queries}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleUserAction(user.user_id, 'reset_credits')}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Reset Credits
                      </button>
                      {user.access_type === 'trial' && (
                        <button
                          onClick={() => handleUserAction(user.user_id, 'upgrade_premium')}
                          className="text-green-600 hover:text-green-900"
                        >
                          Upgrade
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedUser(user)}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        View
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalCount > 10 && (
          <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, totalCount)} of {totalCount} users
            </div>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchUsers(page - 1)}
                disabled={page === 1}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchUsers(page + 1)}
                disabled={!hasNext}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default UserManagement;

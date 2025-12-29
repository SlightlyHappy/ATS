'use client';

import React from 'react';
import AdminLayout from '@/components/admin/AdminLayout';
import UserManagement from '@/components/admin/UserManagement';
import { ProtectedRoute } from '@/context/AuthContext';

const AdminUsersPage: React.FC = () => {
  return (
    <ProtectedRoute adminOnly={true}>
      <AdminLayout>
        <UserManagement />
      </AdminLayout>
    </ProtectedRoute>
  );
};

export default AdminUsersPage;

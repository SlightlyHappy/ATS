"use client";

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAdmin?: boolean;
  requireUser?: boolean;
  redirectTo?: string;
}

export function ProtectedRoute({ 
  children, 
  requireAdmin = false, 
  requireUser = false,
  redirectTo 
}: ProtectedRouteProps) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        const loginUrl = requireAdmin ? '/login?admin=true' : '/login';
        router.push(redirectTo || loginUrl);
        return;
      }

      if (requireAdmin && !isAdmin) {
        router.push('/user');
        return;
      }

      if (requireUser && isAdmin) {
        router.push('/admin/dashboard');
        return;
      }
    }
  }, [isAuthenticated, isAdmin, isLoading, requireAdmin, requireUser, redirectTo, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (requireAdmin && !isAdmin) {
    return null;
  }

  if (requireUser && isAdmin) {
    return null;
  }

  return <>{children}</>;
}

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Loading spinner component
const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="flex flex-col items-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p className="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>
);

// Protected route wrapper
export const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, loading, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    // Redirect to login page with return path
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !isAdmin()) {
    // Redirect to unauthorized page or dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // Allow admins to access any protected route
  if (isAdmin()) {
    return children;
  }

  return children;
};

// Public route wrapper (redirects to appropriate dashboard if already authenticated)
export const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading, isAdmin, isTrialUser, isFullUser, user } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    // Redirect authenticated users to appropriate dashboard based on access type
    let destination = '/dashboard'; // default
    
    if (user?.is_admin || user?.access_type === 'admin' || isAdmin()) {
      destination = '/admin';
    } else if (user?.access_type === 'trial' || isTrialUser()) {
      destination = '/trial';
    } else if (user?.access_type === 'full' || isFullUser()) {
      destination = '/dashboard';
    }
    
    return <Navigate to={destination} replace />;
  }

  return children;
};

// Trial route wrapper (ensures user has trial or full access, or is admin if allowed)
export const TrialRoute = ({ children, allowAdmin = false }) => {
  const { isAuthenticated, loading, isTrialUser, isFullUser, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isTrialUser() && !isFullUser() && !(allowAdmin && isAdmin())) {
    // User doesn't have trial or full access, and isn't admin when allowed
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

// Full access route wrapper (only for full access users or admins if allowed)
export const FullAccessRoute = ({ children, allowAdmin = false }) => {
  const { isAuthenticated, loading, isFullUser, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isFullUser() && !(allowAdmin && isAdmin())) {
    // Redirect trial users to upgrade page, unless they're admin and admin access is allowed
    return <Navigate to="/upgrade" replace />;
  }

  return children;
};

export default ProtectedRoute;

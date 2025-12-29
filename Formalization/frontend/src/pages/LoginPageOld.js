import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    isAdmin: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Get the intended destination from location state
  const from = location.state?.from?.pathname || '/dashboard';

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await login(formData.email, formData.password, formData.isAdmin);
      
      if (result.success) {
        // Determine redirect destination based on user access type
        let destination;
        
        if (result.user.is_admin || result.user.access_type === 'admin') {
          // Admin users go to admin dashboard
          destination = '/admin';
        } else if (result.user.access_type === 'trial') {
          // Trial users go to trial app
          destination = '/trial';
        } else if (result.user.access_type === 'full') {
          // Full users go to full dashboard
          destination = '/dashboard';
        } else {
          // Default fallback
          destination = '/dashboard';
        }
        
        // If there was an intended destination and it's appropriate for the user, use it
        if (location.state?.from?.pathname && location.state.from.pathname !== '/login') {
          const intendedPath = location.state.from.pathname;
          
          // Check if the intended path is appropriate for the user's access level
          if (result.user.is_admin || result.user.access_type === 'admin') {
            // Admin can go anywhere
            destination = intendedPath;
          } else if (result.user.access_type === 'trial' && intendedPath === '/trial') {
            destination = intendedPath;
          } else if (result.user.access_type === 'full' && (intendedPath === '/dashboard' || intendedPath === '/full')) {
            destination = intendedPath;
          }
        }
        
        // Navigate to the determined destination
        navigate(destination, { replace: true });
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <div className="flex justify-center">
            <div className="bg-blue-600 text-white p-3 rounded-full">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Bear Systems
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Resume Screening Platform
          </p>
          <p className="mt-1 text-center text-xs text-gray-500">
            Sign in to your account
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                {formData.isAdmin ? 'Username' : 'Email address'}
              </label>
              <input
                id="email"
                name="email"
                type={formData.isAdmin ? 'text' : 'email'}
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder={formData.isAdmin ? 'Username' : 'Email address'}
                value={formData.email}
                onChange={handleInputChange}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
              />
            </div>
          </div>

          {/* Admin Login Toggle */}
          <div className="flex items-center">
            <input
              id="isAdmin"
              name="isAdmin"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              checked={formData.isAdmin}
              onChange={handleInputChange}
            />
            <label htmlFor="isAdmin" className="ml-2 block text-sm text-gray-900">
              Admin Login
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          {/* Navigation Links */}
          <div className="text-center space-y-2">
            <Link
              to="/"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              ← Back to Home
            </Link>
            
            {!formData.isAdmin && (
              <div className="text-xs text-gray-500">
                <p>Need an account? Contact your administrator</p>
                <p className="mt-1">or email: support@bearsystems.co.in</p>
              </div>
            )}
          </div>
        </form>

        {/* Demo Credentials (for development) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <h3 className="text-sm font-medium text-yellow-800">Demo Credentials</h3>
            <div className="mt-2 text-xs text-yellow-700">
              <p><strong>Admin:</strong> admin / your_admin_password</p>
              <p><strong>User:</strong> Contact admin to create account</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;

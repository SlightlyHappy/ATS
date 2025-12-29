import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Eye, EyeOff, Building2, User, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

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
  const [showPassword, setShowPassword] = useState(false);

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
          destination = from;
        }
        
        // Navigate to the determined destination
        navigate(destination, { replace: true });
      } else {
        setError(result.error || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-2xl shadow-lg">
              <Building2 className="w-10 h-10" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            Bear Systems
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            AI-Powered Resume Screening Platform
          </p>
          <div className="mt-4 flex items-center justify-center space-x-4 text-xs text-gray-500">
            <span className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              Secure
            </span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
              AI-Powered
            </span>
            <span className="flex items-center">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
              Enterprise Ready
            </span>
          </div>
        </div>

        {/* Login Form */}
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl border border-gray-100">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Login Type Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, isAdmin: false }))}
                className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-all ${
                  !formData.isAdmin
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <User className="w-4 h-4 mr-2" />
                User Login
              </button>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, isAdmin: true }))}
                className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-all ${
                  formData.isAdmin
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Shield className="w-4 h-4 mr-2" />
                Admin Login
              </button>
            </div>

            {/* Email/Username Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                {formData.isAdmin ? 'Username' : 'Email Address'}
              </label>
              <input
                id="email"
                name="email"
                type={formData.isAdmin ? 'text' : 'email'}
                autoComplete={formData.isAdmin ? 'username' : 'email'}
                required
                value={formData.email}
                onChange={handleInputChange}
                className="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:z-10 transition-colors"
                placeholder={formData.isAdmin ? 'Enter username' : 'Enter email address'}
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="appearance-none relative block w-full px-4 py-3 pr-12 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:z-10 transition-colors"
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-500" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-500" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
              >
                {loading ? (
                  <div className="flex items-center">
                    <LoadingSpinner size="small" className="mr-2" />
                    <span>Signing in...</span>
                  </div>
                ) : (
                  <>
                    {formData.isAdmin ? (
                      <span className="flex items-center">
                        <Shield className="w-4 h-4 mr-2" />
                        Sign in as Admin
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <User className="w-4 h-4 mr-2" />
                        Sign in to Account
                      </span>
                    )}
                  </>
                )}
              </button>
            </div>

            {/* Additional Info */}
            <div className="text-center">
              <div className="text-sm text-gray-600">
                {formData.isAdmin ? (
                  <p>Admin access required for user management and system administration.</p>
                ) : (
                  <div className="space-y-2">
                    <p>New to Bear Systems? Contact your administrator for access.</p>
                    <div className="flex justify-center items-center space-x-4 text-xs">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Trial Available</span>
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">Enterprise Ready</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Back to Public */}
            <div className="text-center">
              <Link
                to="/"
                className="font-medium text-blue-600 hover:text-blue-500 text-sm transition-colors"
              >
                ← Back to Home
              </Link>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500">
          <p>© 2025 Bear Systems. All rights reserved.</p>
          <p className="mt-1">Powered by AI • Secured by Design • Built for Scale</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

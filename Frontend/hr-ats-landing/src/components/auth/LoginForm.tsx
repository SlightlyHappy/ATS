'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

interface LoginFormProps {
  onLogin: (credentials: LoginCredentials, isAdmin: boolean) => Promise<void>;
  loading?: boolean;
}

interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, loading = false }) => {
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await onLogin(credentials, isAdminLogin);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-auto flex justify-center">
            <img
              className="h-12 w-auto"
              src="/images/logo/logo_dark.png"
              alt="HR ATS"
            />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            AI-Powered Resume Analysis System
          </p>
        </div>

        <Card className="p-8">
          {/* Login Type Toggle */}
          <div className="flex justify-center mb-6">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                type="button"
                onClick={() => setIsAdminLogin(false)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  !isAdminLogin
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                User Login
              </button>
              <button
                type="button"
                onClick={() => setIsAdminLogin(true)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isAdminLogin
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Admin Login
              </button>
            </div>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Authentication Error
                    </h3>
                    <div className="mt-2 text-sm text-red-700">{error}</div>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label htmlFor={isAdminLogin ? "username" : "email"} className="sr-only">
                {isAdminLogin ? 'Username' : 'Email address'}
              </label>
              <input
                id={isAdminLogin ? "username" : "email"}
                name={isAdminLogin ? "username" : "email"}
                type={isAdminLogin ? "text" : "email"}
                autoComplete={isAdminLogin ? "username" : "email"}
                required
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder={isAdminLogin ? 'Admin username' : 'Email address'}
                value={isAdminLogin ? credentials.username : credentials.email}
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
                autoComplete="current-password"
                required
                className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={credentials.password}
                onChange={handleInputChange}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  Forgot your password?
                </a>
              </div>
            </div>

            <div>
              <Button
                type="submit"
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Signing in...
                  </div>
                ) : (
                  `Sign in ${isAdminLogin ? 'as Admin' : ''}`
                )}
              </Button>
            </div>

            {!isAdminLogin && (
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  New to HR ATS?{' '}
                  <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                    Contact admin for account creation
                  </a>
                </p>
              </div>
            )}
          </form>
        </Card>

        {/* System Status */}
        <div className="text-center">
          <div className="inline-flex items-center text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
            System Status: Operational
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AppLogo } from '@/components/shared/app-logo';
import { Eye, EyeOff, Lock, Mail, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

export default function AdminLoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  // Role detection function - Updated for v1.76
  const determineUserRoleAndRedirect = async (token: string) => {
    try {
      // Test admin access by calling admin dashboard endpoint
      const adminResponse = await fetch(`${API_BASE_URL}/api/admin/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (adminResponse.ok) {
        // User has admin access
        router.push('/admin/dashboard');
      } else if (adminResponse.status === 403) {
        // User is authenticated but not admin - redirect to user dashboard
        router.push('/user/dashboard');
      } else {
        // Some other error - stay on login
        toast.error('Unable to determine user permissions. Please try again.');
      }
    } catch (error) {
      console.error('Role detection error:', error);
      // If we can't determine role, default to user dashboard
      router.push('/user/dashboard');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('Starting login request...');
      // Create AbortController for timeout handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.log('Request timeout after 10 seconds');
        controller.abort();
      }, 10000); // 10 second timeout

      console.log('Making fetch request to:', `${API_BASE_URL}/api/auth/login`);
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      console.log('Response received:', response.status, response.statusText);
      
      const data = await response.json();
      console.log('Response data:', data);

      if (response.ok && data.access_token) {
        // Store authentication data - Updated for v1.76 (simplified response)
        localStorage.setItem('auth_token', data.access_token);
        console.log('Token stored successfully');
        
        toast.success('Login successful!');
        
        // Skip role detection for now - just go to admin dashboard
        console.log('Redirecting to admin dashboard...');
        router.push('/admin/dashboard');
      } else {
        console.log('Login failed:', data);
        setError(data.detail || data.message || 'Login failed');
        toast.error('Login failed');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      if (error.name === 'AbortError') {
        setError('Request timed out. Please check your connection and try again.');
        toast.error('Request timed out. Please try again.');
      } else {
        setError('Network error. Please try again.');
        toast.error('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    if (error) setError(''); // Clear error when user starts typing
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-background/90 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5" />
      
      <div className="relative w-full max-w-md">
        {/* Back to Home Link */}
        <div className="mb-8">
          <Link 
            href="/" 
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← Back to Home
          </Link>
        </div>

        <Card className="border-2 shadow-2xl bg-card/95 backdrop-blur-sm">
          <CardHeader className="space-y-4 text-center">
            <div className="flex justify-center">
              <AppLogo />
            </div>
            <div>
              <CardTitle className="text-2xl font-headline">Admin Login</CardTitle>
              <CardDescription className="text-base">
                Access the Bear Systems HRT admin panel
              </CardDescription>
            </div>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="Enter your email address"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="pl-10"
                    required
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="pl-10 pr-10"
                    required
                    disabled={loading}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1 h-8 w-8 p-0"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading || !formData.email || !formData.password}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                    <span>Signing in...</span>
                  </div>
                ) : (
                  'Sign In'
                )}
              </Button>

              <div className="text-center">
                <p className="text-sm text-muted-foreground">
                  Need access? Contact your system administrator
                </p>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Additional Info */}
        <div className="mt-8 text-center">
          <p className="text-xs text-muted-foreground">
            This is a secure admin portal. All activities are logged and monitored.
          </p>
        </div>
      </div>
    </div>
  );
}

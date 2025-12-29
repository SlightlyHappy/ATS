'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Icons } from '@/components/icons';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // Determine if input is email or username
      const isEmail = emailOrUsername.includes('@');
      const endpoint = isEmail 
        ? 'https://hrtoolsbackend-production.up.railway.app/api/auth/user-login'
        : 'https://hrtoolsbackend-production.up.railway.app/api/auth/admin-login';
      
      const requestBody = isEmail 
        ? { email: emailOrUsername, password }
        : { username: emailOrUsername, password };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Login failed. Please check your credentials.');
      }
      
      // As per frontendguide.md, the token is named "token" in the response.
      if (data.token) {
        const tokenKey = isEmail ? 'auth_token' : 'admin_auth_token';
        localStorage.setItem(tokenKey, data.token);
        toast({
          title: "Login Successful",
          description: "Welcome back! Redirecting to your dashboard...",
        });
        
        const redirectPath = isEmail ? '/dashboard' : '/admin';
        router.push(redirectPath);
      } else {
        throw new Error('Authentication failed: No token provided.');
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center">
            <Icons.logo className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-3xl font-bold tracking-tight">HR Intel Pro</CardTitle>
          <CardDescription>Welcome back! Log in with your email or username.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Login Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="emailOrUsername">Email or Username</Label>
              <Input 
                id="emailOrUsername" 
                type="text" 
                placeholder="name@example.com or username" 
                autoComplete="username"
                required 
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link href="/forgot-password">
                  <Button variant="link" className="px-0 text-sm">Forgot password?</Button>
                </Link>
              </div>
              <Input 
                id="password" 
                type="password" 
                autoComplete="current-password"
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full text-lg font-semibold py-6" disabled={isLoading}>
              {isLoading ? 'Logging In...' : 'Log In'}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            Don't have an account?{' '}
            <Link href="/register">
               <Button variant="link" className="px-1">Sign up</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

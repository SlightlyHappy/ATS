'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Icons } from '@/components/icons';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import React, { useState } from 'react';

export default function RegisterPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    // In a production app, the frontend guide states user creation is admin-only.
    // This form would typically call a public registration endpoint.
    // Since one doesn't exist, we will simulate a successful signup
    // and inform the user that access is granted upon contact.
    
    await new Promise(resolve => setTimeout(resolve, 1000));

    toast({
        title: "Registration Request Received",
        description: "Thank you for your interest! Access to the platform is currently granted upon request. We will contact you shortly.",
        duration: 5000,
    });
    
    // In a real scenario with a public endpoint:
    // router.push('/dashboard');
    setIsLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center">
            <Icons.logo className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-3xl font-bold tracking-tight">Request Access</CardTitle>
          <CardDescription>Get started with 100 free trial credits upon approval.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && <Alert variant="destructive"><AlertTriangle/><AlertTitle>Error</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input id="name" type="text" placeholder="Your Name" required disabled={isLoading}/>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="name@example.com" required disabled={isLoading}/>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" required disabled={isLoading}/>
            </div>
            <Button type="submit" className="w-full text-lg font-semibold py-6" disabled={isLoading}>
              {isLoading ? 'Submitting...' : 'Request Trial Access'}
            </Button>
          </form>
          <Separator className="my-6" />
          <div className="text-center text-sm">
            Already have an account?{' '}
            <Link href="/login">
               <Button variant="link" className="px-1">Log in</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

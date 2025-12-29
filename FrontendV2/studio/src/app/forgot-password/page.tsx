'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Icons } from '@/components/icons';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft } from 'lucide-react';

export default function ForgotPasswordPage() {
  const { toast } = useToast();

  const handleResetRequest = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, you'd handle the password reset link submission here.
    toast({
      title: "Password Reset Link Sent",
      description: "If an account exists with that email, a reset link has been sent.",
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex items-center justify-center">
            <Icons.logo className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-3xl font-bold tracking-tight">Forgot Password?</CardTitle>
          <CardDescription>No problem. Enter your email and we'll send a reset link.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleResetRequest} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="name@example.com" required />
            </div>
            <Button type="submit" className="w-full text-lg font-semibold py-6">
              Send Reset Link
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Link href="/login">
              <Button variant="ghost">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Log In
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { Eye, EyeOff, AlertCircle } from "lucide-react";

const loginSchema = z.object({
  email: z.string().min(1, {
    message: "Email or username is required.",
  }).refine((value) => {
    // Allow either email format or username (no @ symbol)
    const isEmail = value.includes('@');
    if (isEmail) {
      return z.string().email().safeParse(value).success;
    }
    // Username validation: at least 3 characters, alphanumeric and underscore
    return /^[a-zA-Z0-9_]{3,}$/.test(value);
  }, {
    message: "Please enter a valid email address or username (3+ characters, letters, numbers, underscore only).",
  }),
  password: z.string().min(1, "Password is required"),
  isAdmin: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof loginSchema>;

function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, isAdmin } = useAuth();
  
  const redirectTo = searchParams.get('redirect') || null;
  const isAdminLogin = searchParams.get('admin') === 'true';

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      isAdmin: isAdminLogin,
    },
  });

  useEffect(() => {
    // Redirect if already authenticated
    if (isAuthenticated) {
      if (redirectTo) {
        router.push(redirectTo);
      } else if (isAdmin) {
        router.push('/admin/dashboard');
      } else {
        router.push('/user');
      }
    }
  }, [isAuthenticated, isAdmin, router, redirectTo]);

  const onSubmit = async (data: LoginFormData) => {
    console.log('🔐 Login Form: Starting login submission...', {
      email: data.email.substring(0, 3) + '***', // Mask email for security
      hasPassword: !!data.password,
      passwordLength: data.password.length,
      isAdmin: data.isAdmin,
      timestamp: new Date().toISOString()
    });

    try {
      setIsLoading(true);
      setError(null);
      
      console.log('🔄 Login Form: Setting loading state and calling auth.login...');
      console.log('📤 Login Form: Auth context login parameters:', {
        email: data.email.substring(0, 3) + '***',
        isAdmin: data.isAdmin
      });
      
      await login(data.email, data.password, data.isAdmin);
      
      console.log('✅ Login Form: Auth login completed successfully');
      console.log('🔄 Login Form: Redirect will be handled by useEffect hook');
      
      // Redirect will be handled by useEffect
    } catch (error) {
      console.log('❌ Login Form: Login failed with error:', error);
      
      const errorMessage = error instanceof Error ? error.message : "Login failed. Please try again.";
      console.log('❌ Login Form: Setting error message:', errorMessage);
      
      setError(errorMessage);
    } finally {
      console.log('🔄 Login Form: Resetting loading state...');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-3 sm:p-4 md:p-6">
      <Card className="w-full max-w-sm sm:max-w-md mx-auto shadow-lg">
        <CardHeader className="space-y-2 pb-4">
          <CardTitle className="text-xl sm:text-2xl font-bold text-center">
            {isAdminLogin ? 'Admin Login' : 'Login'}
          </CardTitle>
          <CardDescription className="text-center text-sm sm:text-base">
            Enter your email or username and password to access your account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-4 sm:px-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email or Username</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        type="text"
                        placeholder="admin@example.com or admin"
                        disabled={isLoading}
                        className="w-full"
                        autoComplete="username"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          {...field}
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          disabled={isLoading}
                          className="w-full pr-10"
                          autoComplete="current-password"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowPassword(!showPassword)}
                          disabled={isLoading}
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                          <span className="sr-only">
                            {showPassword ? "Hide password" : "Show password"}
                          </span>
                        </Button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="isAdmin"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isLoading}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="text-sm font-normal">
                        Admin access
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        Check this if you are logging in as an administrator
                      </p>
                    </div>
                  </FormItem>
                )}
              />

              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
                size="default"
              >
                {isLoading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </Button>
            </form>
          </Form>

          <div className="text-center text-sm">
            Don't have an account?{" "}
            <Link href="/signup" className="underline hover:text-primary transition-colors">
              Sign up
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen p-3 sm:p-4 md:p-6">
        <Card className="w-full max-w-sm sm:max-w-md mx-auto shadow-lg">
          <CardHeader className="space-y-2 pb-4">
            <CardTitle className="text-xl sm:text-2xl font-bold text-center">
              Loading...
            </CardTitle>
            <CardDescription className="text-center text-sm sm:text-base">
              Please wait while we load the login form.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-transparent" />
          </CardContent>
        </Card>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
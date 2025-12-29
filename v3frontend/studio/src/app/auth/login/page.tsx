
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Shield } from "lucide-react";
import { useState, useEffect, Suspense } from "react";
import { useAuth } from "@/contexts/AuthContext";

const formSchema = z.object({
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
  password: z.string().min(1, {
    message: "Password is required.",
  }),
  isAdmin: z.boolean().default(false),
});

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const { login, isAuthenticated, isAdmin } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Check if admin login is requested
  const adminLogin = searchParams.get('admin') === 'true';
  const redirectTo = searchParams.get('redirect');

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
      isAdmin: adminLogin,
    },
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const targetUrl = redirectTo || (isAdmin ? '/admin/dashboard' : '/user');
      router.push(targetUrl);
    }
  }, [isAuthenticated, isAdmin, redirectTo, router]);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsSubmitting(true);
    try {
      await login(values.email, values.password, values.isAdmin);
      
      toast({
        title: "Login Successful",
        description: `Welcome back${values.isAdmin ? ', Admin' : ''}!`,
      });

      // Redirect to appropriate dashboard or requested page
      const targetUrl = redirectTo || (values.isAdmin ? '/admin/dashboard' : '/user');
      router.push(targetUrl);
    } catch (error) {
      toast({
        title: "Login Failed",
        description: error instanceof Error ? error.message : "Invalid credentials. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="mx-auto max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl flex items-center gap-2">
          {form.watch('isAdmin') && <Shield className="h-5 w-5 text-blue-600" />}
          {form.watch('isAdmin') ? 'Admin Login' : 'Login'}
        </CardTitle>
        <CardDescription>
          {form.watch('isAdmin') 
            ? 'Enter your admin credentials to access the admin panel'
            : 'Enter your email or username below to login to your account'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email or Username</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="admin or user@example.com" 
                      autoComplete="username"
                      {...field} 
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
                  <div className="flex items-center">
                    <FormLabel>Password</FormLabel>
                    <Link href="#" className="ml-auto inline-block text-sm underline">
                      Forgot your password?
                    </Link>
                  </div>
                  <FormControl>
                    <Input 
                      type="password" 
                      autoComplete="current-password"
                      {...field} 
                    />
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
                    />
                  </FormControl>
                  <div className="space-y-1 leading-none">
                    <FormLabel className="text-sm font-medium">
                      Login as Administrator
                    </FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Check this box to access admin features
                    </p>
                  </div>
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {form.watch('isAdmin') ? 'Login as Admin' : 'Login'}
            </Button>
          </form>
        </Form>
        <div className="mt-4 text-center text-sm">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="underline">
            Sign up
          </Link>
        </div>
        {!form.watch('isAdmin') && (
          <div className="mt-2 text-center text-sm">
            <Link 
              href="/login?admin=true" 
              className="text-blue-600 hover:underline flex items-center justify-center gap-1"
            >
              <Shield className="h-3 w-3" />
              Admin Login
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <Card className="mx-auto max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Loading...</CardTitle>
          <CardDescription>Please wait while we load the login form.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    }>
      <LoginForm />
    </Suspense>
  );
}

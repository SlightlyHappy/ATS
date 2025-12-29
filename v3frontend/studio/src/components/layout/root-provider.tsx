"use client"
import { usePathname } from 'next/navigation'
import MainLayout from './main-layout'
import { ThemeProvider } from '@/components/theme-provider'
import { AuthProvider } from '@/contexts/AuthContext'
import { LoadingProvider } from '@/components/loading/loading-provider'
import { ToastProvider } from '@/components/toast/toast-provider'
import { RouteErrorWrapper } from '@/components/error-boundary/route-error-boundary'
import AuthLayout from '@/app/auth/layout';

export default function RootProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  let content: React.ReactNode;
  
  const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/signup');
  const isLandingPage = pathname === '/';
  const isAdminPage = pathname.startsWith('/admin');
  const isUserPage = pathname.startsWith('/user');

  if (isAuthPage) {
    content = (
      <RouteErrorWrapper level="page">
        <AuthLayout>{children}</AuthLayout>
      </RouteErrorWrapper>
    );
  } else if (isLandingPage) {
    content = (
      <RouteErrorWrapper level="page">
        <div className="min-h-screen bg-background">{children}</div>
      </RouteErrorWrapper>
    );
  } else if (isAdminPage || isUserPage) {
    // The admin and user layouts will handle their own authentication checks
    content = (
      <RouteErrorWrapper level="page">
        {children}
      </RouteErrorWrapper>
    );
  } else {
    // Legacy routes or other pages - use MainLayout without role specification
    content = (
      <RouteErrorWrapper level="page">
        <MainLayout>{children}</MainLayout>
      </RouteErrorWrapper>
    );
  }
  
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <LoadingProvider>
        <ToastProvider>
          <AuthProvider>
            {content}
          </AuthProvider>
        </ToastProvider>
      </LoadingProvider>
    </ThemeProvider>
  )
}

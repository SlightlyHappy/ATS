"use client"
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import MainLayout from '@/components/layout/main-layout'
import { RouteErrorBoundary } from '@/components/error-boundary/route-error-boundary'
import { UserErrorBoundary } from '@/components/user/user-error-boundary'
import { DashboardSkeleton } from '@/components/ui/skeleton'

export default function UserLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login')
        return
      }
      
      if (isAdmin) {
        router.push('/admin/dashboard')
        return
      }
    }
  }, [isAuthenticated, isAdmin, isLoading, router])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <DashboardSkeleton />
      </div>
    )
  }

  if (!isAuthenticated || isAdmin) {
    return null
  }

  return (
    <UserErrorBoundary>
      <RouteErrorBoundary level="critical">
        <MainLayout isAdmin={false}>{children}</MainLayout>
      </RouteErrorBoundary>
    </UserErrorBoundary>
  )
}

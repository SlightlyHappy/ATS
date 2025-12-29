"use client";

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import EnhancedDashboardWrapper from '@/components/user/enhanced-dashboard-wrapper'
import { DashboardSkeleton } from '@/components/ui/skeleton'

export default function UserDashboard() {
  const { user, isAuthenticated, isAdmin, isLoading } = useAuth()
  const router = useRouter()

  // Debug logging
  console.log('🔍 User Dashboard Page: Current state', {
    isLoading,
    isAuthenticated,
    isAdmin,
    userEmail: user?.email,
    userAccessType: user?.access_type,
    timestamp: new Date().toISOString()
  })

  useEffect(() => {
    console.log('🔄 User Dashboard Page: useEffect triggered', {
      isLoading,
      isAuthenticated,
      isAdmin,
      userEmail: user?.email
    })

    if (!isLoading) {
      if (!isAuthenticated) {
        console.log('🔄 User Dashboard: Not authenticated, redirecting to login...')
        router.push('/login')
        return
      }
      
      if (isAdmin) {
        console.log('🔄 User Dashboard: Admin user detected, redirecting to admin dashboard...')
        console.log('🔄 Admin user details:', {
          email: user?.email,
          name: user?.name,
          access_type: user?.access_type
        })
        router.push('/admin/dashboard')
        return
      }

      console.log('✅ User Dashboard: Regular user confirmed, showing dashboard')
    }
  }, [isAuthenticated, isAdmin, isLoading, router, user])

  // Show loading while checking auth state
  if (isLoading) {
    console.log('⏳ User Dashboard: Showing loading state')
    return (
      <div className="flex items-center justify-center min-h-screen">
        <DashboardSkeleton />
      </div>
    )
  }

  // Don't render anything while redirecting admin users or unauthenticated users
  if (!isAuthenticated || isAdmin) {
    console.log('🚫 User Dashboard: Blocking render for admin/unauthenticated user', {
      isAuthenticated,
      isAdmin,
      userEmail: user?.email
    })
    return null
  }

  console.log('✅ User Dashboard: Rendering dashboard for regular user')
  return <EnhancedDashboardWrapper />
}

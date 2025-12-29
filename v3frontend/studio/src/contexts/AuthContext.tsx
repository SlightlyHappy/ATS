import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { AuthService } from '../services/auth.service'

export interface User {
  user_id: string
  email: string
  name: string
  access_type: 'admin' | 'user'
  is_trial: boolean
  trial_info?: {
    resume_limit: number
    legal_limit: number
    used_resumes: number
    used_legal: number
  }
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isAdmin: boolean
  isLoading: boolean
  login: (email: string, password: string, isAdmin?: boolean) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const pathname = usePathname()

  const isAuthenticated = !!user
  const isAdmin = user?.access_type === 'admin'
  
  // Define public routes that don't need authentication
  const isPublicRoute = pathname === '/' || pathname.startsWith('/login') || pathname.startsWith('/signup')

  const login = async (email: string, password: string, isAdmin = false) => {
    try {
      setIsLoading(true)
      console.log('🔐 Starting login process...')
      
      const response = await AuthService.login(email, password, isAdmin)
      console.log('✅ Login API call completed')
      
      // Immediately verify the session was established by checking current user
      console.log('🔍 Verifying session after login...')
      try {
        // Add a longer delay to ensure cookie processing
        await new Promise(resolve => setTimeout(resolve, 300))
        
        const sessionCheck = await AuthService.getCurrentUser()
        console.log('✅ Session verified:', sessionCheck.user?.name)
        setUser(sessionCheck.user)
        
        // Additional verification - make sure we have the right user type
        if (isAdmin && sessionCheck.user?.access_type !== 'admin') {
          throw new Error('Admin login succeeded but user is not an admin')
        }
        
      } catch (sessionError) {
        console.error('❌ Session verification failed after login:', sessionError)
        // If session check fails, the login didn't properly set cookies
        throw new Error('Login succeeded but session was not established. Please try again.')
      }
    } catch (error) {
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await AuthService.logout()
      setUser(null)
    } catch (error) {
      console.error('Logout error:', error)
      // Force logout on client side even if server call fails
      setUser(null)
    }
  }

  const checkAuth = async () => {
    // Skip auth check for public routes
    if (isPublicRoute) {
      setIsLoading(false)
      return
    }
    
    try {
      setIsLoading(true)
      const response = await AuthService.getCurrentUser()
      setUser(response.user)
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Check authentication status on app load, but only for protected routes
    if (!isPublicRoute) {
      checkAuth()
    } else {
      // For public routes, just set loading to false
      setIsLoading(false)
    }
  }, [pathname, isPublicRoute])

  const value: AuthState = {
    user,
    isAuthenticated,
    isAdmin,
    isLoading,
    login,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

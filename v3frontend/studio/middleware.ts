import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Get session tokens from cookies
  const adminToken = request.cookies.get('admin_session_token')
  const userToken = request.cookies.get('user_session_token')
  
  // Public routes that don't require authentication
  const publicRoutes = ['/', '/login', '/signup', '/api/auth/admin-login', '/api/auth/user-login', '/api/auth/health']
  const isPublicRoute = publicRoutes.some(route => pathname === route || pathname.startsWith('/api/auth/'))
  
  if (isPublicRoute) {
    return NextResponse.next()
  }
  
  // Admin routes protection
  if (pathname.startsWith('/admin')) {
    if (!adminToken) {
      const loginUrl = new URL('/login?admin=true', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
    return NextResponse.next()
  }
  
  // User routes protection
  if (pathname.startsWith('/user')) {
    if (!userToken) {
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
    return NextResponse.next()
  }
  
  // Legacy routes - redirect to appropriate new routes
  if (pathname === '/dashboard') {
    if (adminToken) {
      return NextResponse.redirect(new URL('/admin/dashboard', request.url))
    } else if (userToken) {
      return NextResponse.redirect(new URL('/user', request.url))
    } else {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  
  if (pathname === '/resumes') {
    if (adminToken) {
      return NextResponse.redirect(new URL('/admin/resumes', request.url))
    } else {
      return NextResponse.redirect(new URL('/login?admin=true', request.url))
    }
  }
  
  if (pathname === '/users') {
    if (adminToken) {
      return NextResponse.redirect(new URL('/admin/users', request.url))
    } else {
      return NextResponse.redirect(new URL('/login?admin=true', request.url))
    }
  }
  
  if (pathname === '/settings') {
    if (adminToken) {
      return NextResponse.redirect(new URL('/admin/settings', request.url))
    } else if (userToken) {
      return NextResponse.redirect(new URL('/user/profile', request.url))
    } else {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  
  if (pathname === '/profile') {
    if (userToken) {
      return NextResponse.redirect(new URL('/user/profile', request.url))
    } else {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  
  if (pathname === '/submit-resume') {
    if (userToken) {
      return NextResponse.redirect(new URL('/user/submit', request.url))
    } else {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }
  
  // Default: require some form of authentication for all other routes
  if (!adminToken && !userToken) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (favicon, robots, manifest, etc.)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.).*)',
  ],
}

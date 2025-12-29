import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    console.log('🔄 Proxying refresh token to backend...')

    const response = await fetch(`${BACKEND_URL}/api/auth/refresh-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('🔄 Refresh token backend response status:', response.status)
    console.log('🔄 Refresh token backend response:', data)

    // Create the response
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward all cookies from the backend
    const cookieHeaders = response.headers.getSetCookie()
    if (cookieHeaders && cookieHeaders.length > 0) {
      cookieHeaders.forEach(cookie => {
        nextResponse.headers.append('Set-Cookie', cookie)
      })
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Refresh token proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to refresh token',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

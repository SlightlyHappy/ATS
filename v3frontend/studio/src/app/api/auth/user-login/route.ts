import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    console.log('🔐 Proxying user login to backend...')

    const response = await fetch(`${BACKEND_URL}/api/auth/user-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('user-agent') || '',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    
    console.log('🔐 User login backend response status:', response.status)
    console.log('🔐 User login backend response:', data)

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
    console.error('❌ User login proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to process login',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

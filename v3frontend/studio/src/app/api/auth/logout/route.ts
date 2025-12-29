import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    console.log('👋 Proxying logout to backend...')

    const response = await fetch(`${BACKEND_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    console.log('🔐 Logout backend response status:', response.status)

    let data;
    try {
      const responseText = await response.text();
      if (responseText) {
        data = JSON.parse(responseText);
      } else {
        data = { success: true, message: "Logged out successfully" };
      }
    } catch (parseError) {
      data = { success: true, message: "Logged out successfully" };
    }
    
    console.log('🔐 Logout backend response:', data)

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
    console.error('❌ Logout proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to process logout',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

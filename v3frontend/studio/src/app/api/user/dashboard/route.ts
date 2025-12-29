import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(request: NextRequest) {
  try {
    console.log('📊 Proxying user dashboard to backend...')

    const response = await fetch(`${BACKEND_URL}/api/user/dashboard`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('📊 User dashboard backend response status:', response.status)
    console.log('📊 User dashboard backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ User dashboard proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch dashboard data',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

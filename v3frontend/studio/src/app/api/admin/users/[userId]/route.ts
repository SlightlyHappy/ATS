import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params

    console.log('👤 Proxying admin user details GET to backend for ID:', userId)

    const response = await fetch(`${BACKEND_URL}/api/admin/users/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('👤 Admin user details backend response status:', response.status)
    console.log('👤 Admin user details backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Admin user details proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch user details',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

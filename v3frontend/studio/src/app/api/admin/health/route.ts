import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(request: NextRequest) {
  try {
    console.log('🏥 Proxying admin health check to backend...')

    const response = await fetch(`${BACKEND_URL}/api/admin/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('🏥 Admin health backend response status:', response.status)
    console.log('🏥 Admin health backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })

    return nextResponse
  } catch (error) {
    console.error('❌ Admin health proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to check health',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

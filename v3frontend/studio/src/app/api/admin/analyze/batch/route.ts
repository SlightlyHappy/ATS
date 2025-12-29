import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    console.log('🧠 Proxying admin batch analyze to backend...')
    console.log('🔗 Backend URL (redirected):', `${BACKEND_URL}/api/admin/analyze/batch`)

    // Redirect to the correct backend endpoint: /api/admin/analyze/batch
    const response = await fetch(`${BACKEND_URL}/api/admin/analyze/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    
    console.log('🧠 Admin batch analyze backend response status:', response.status)
    console.log('🧠 Admin batch analyze backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Admin batch analyze proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to start batch analysis',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

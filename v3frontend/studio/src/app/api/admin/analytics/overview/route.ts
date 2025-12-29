import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(request: NextRequest) {
  try {
    // Forward query parameters
    const url = new URL(`${BACKEND_URL}/api/admin/analytics/overview`)
    const searchParams = new URL(request.url).searchParams
    searchParams.forEach((value, key) => {
      url.searchParams.set(key, value)
    })

    console.log('📊 Proxying admin analytics overview to:', url.toString())

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('📊 Admin analytics overview backend response status:', response.status)
    console.log('📊 Admin analytics overview backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Admin analytics overview proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch analytics overview',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

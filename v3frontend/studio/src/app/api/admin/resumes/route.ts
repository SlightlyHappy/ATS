import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(request: NextRequest) {
  try {
    // Forward the request to the backend
    const url = new URL(`${BACKEND_URL}/api/admin/resumes`)
    
    // Copy query parameters
    const searchParams = new URL(request.url).searchParams
    searchParams.forEach((value, key) => {
      url.searchParams.set(key, value)
    })

    console.log('📡 Proxying admin resumes GET to:', url.toString())

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward cookies from the original request
        'Cookie': request.headers.get('cookie') || '',
        // Forward other relevant headers
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    const data = await response.json()
    
    console.log('📊 Backend response status:', response.status)
    console.log('📊 Backend response type:', typeof data)
    console.log('📊 Backend response keys:', Object.keys(data || {}))
    console.log('📊 Backend response:', JSON.stringify(data, null, 2))

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Admin resumes proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch resumes',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

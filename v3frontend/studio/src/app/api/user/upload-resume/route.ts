import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    // Get the form data from the request
    const formData = await request.formData()
    
    console.log('📤 Proxying user resume upload to backend...')
    console.log('📋 Form data fields:', Array.from(formData.keys()))

    const response = await fetch(`${BACKEND_URL}/api/user/upload-resume`, {
      method: 'POST',
      headers: {
        // Don't set Content-Type for FormData - let fetch set it with boundary
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
      body: formData, // Forward the FormData directly
    })

    const data = await response.json()
    
    console.log('📊 User upload backend response status:', response.status)
    console.log('📊 User upload backend response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ User resume upload proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to upload resume',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

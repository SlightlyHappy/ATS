import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    console.log('⚖️ Proxying admin HR legal query to backend...')
    console.log('🔗 Backend URL:', `${BACKEND_URL}/api/admin/hr-legal/query`)
    console.log('🍪 Request cookies:', request.headers.get('cookie'))

    const response = await fetch(`${BACKEND_URL}/api/admin/hr-legal/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
      body: JSON.stringify(body),
    })

    console.log('⚖️ HR legal query backend response status:', response.status)
    console.log('⚖️ HR legal query backend response headers:', Object.fromEntries(response.headers.entries()))

    // Special handling for 400 errors to get more details
    if (response.status === 400) {
      console.error('🚨 400 Bad Request - Request might have invalid format')
      console.error('🚨 Request body was:', JSON.stringify(body))
    }

    let data;
    try {
      const responseText = await response.text();
      console.log('⚖️ HR legal query backend raw response:', responseText);
      
      // For 400 errors, log the exact error message
      if (response.status === 400) {
        console.error('🚨 400 Error details:', responseText)
      }
      
      if (responseText) {
        data = JSON.parse(responseText);
      } else {
        data = { success: true, message: "Legal query submitted" };
      }
    } catch (parseError) {
      console.error('❌ Failed to parse JSON response:', parseError);
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid response from backend',
          message: 'Backend returned invalid JSON'
        },
        { status: 500 }
      );
    }
    
    console.log('⚖️ HR legal query backend parsed response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse

  } catch (error) {
    console.error('❌ Admin HR legal query proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to submit legal query',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

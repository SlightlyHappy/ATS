import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    console.log('⚖️ Proxying admin legal queries GET to backend...')
    console.log('🔗 Backend URL:', `${BACKEND_URL}/api/admin/legal-queries?${searchParams}`)
    console.log('🍪 Request cookies:', request.headers.get('cookie'))

    const response = await fetch(`${BACKEND_URL}/api/admin/legal-queries?${searchParams}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    console.log('⚖️ Legal queries backend response status:', response.status)
    console.log('⚖️ Legal queries backend response headers:', Object.fromEntries(response.headers.entries()))

    let data;
    try {
      const responseText = await response.text();
      console.log('⚖️ Legal queries backend raw response:', responseText);
      if (responseText) {
        data = JSON.parse(responseText);
      } else {
        data = { success: true, data: [], message: "No legal queries found" };
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
    
    console.log('⚖️ Legal queries backend parsed response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse

  } catch (error) {
    console.error('❌ Admin legal queries proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch legal queries',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

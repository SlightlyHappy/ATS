import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params

    console.log('🧠 Proxying admin resume analyze to backend for ID:', id)
    console.log('🔗 Backend URL:', `${BACKEND_URL}/api/admin/resumes/${id}/analyze`)
    console.log('🍪 Request cookies:', request.headers.get('cookie'))

    // Get request body if any
    let requestBody = null;
    try {
      const body = await request.text();
      if (body) {
        requestBody = body;
      }
    } catch (e) {
      // No body, that's fine
    }

    const response = await fetch(`${BACKEND_URL}/api/admin/resumes/${id}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
      body: requestBody || JSON.stringify({ 
        analysis_type: "comprehensive", 
        priority: "high" 
      }),
    })

    console.log('📊 Analyze backend response status:', response.status)
    console.log('📊 Analyze backend response headers:', Object.fromEntries(response.headers.entries()))

    let data;
    try {
      const responseText = await response.text();
      console.log('📊 Analyze backend raw response:', responseText);
      if (responseText) {
        data = JSON.parse(responseText);
      } else {
        data = { success: true, message: "Analysis started" };
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
    
    console.log('📊 Analyze backend parsed response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse
  } catch (error) {
    console.error('❌ Admin resume analyze proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to analyze resume',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

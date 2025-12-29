import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export async function DELETE(
  request: NextRequest,
  { params }: { params: { queryId: string } }
) {
  try {
    const { queryId } = params
    
    console.log('⚖️ Proxying admin legal query DELETE to backend for ID:', queryId)
    console.log('🔗 Backend URL:', `${BACKEND_URL}/api/admin/legal-queries/${queryId}`)
    console.log('🍪 Request cookies:', request.headers.get('cookie'))

    const response = await fetch(`${BACKEND_URL}/api/admin/legal-queries/${queryId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
        'Authorization': request.headers.get('authorization') || '',
        'User-Agent': request.headers.get('user-agent') || '',
      },
    })

    console.log('⚖️ Legal query delete backend response status:', response.status)
    console.log('⚖️ Legal query delete backend response headers:', Object.fromEntries(response.headers.entries()))

    let data;
    try {
      const responseText = await response.text();
      console.log('⚖️ Legal query delete backend raw response:', responseText);
      if (responseText) {
        data = JSON.parse(responseText);
      } else {
        data = { success: true, message: "Legal query deleted" };
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
    
    console.log('⚖️ Legal query delete backend parsed response:', data)

    // Return the response with proper headers
    const nextResponse = NextResponse.json(data, { status: response.status })
    
    // Forward any set-cookie headers from backend
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      nextResponse.headers.set('set-cookie', setCookieHeader)
    }

    return nextResponse

  } catch (error) {
    console.error('❌ Admin legal query delete proxy error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to delete legal query',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

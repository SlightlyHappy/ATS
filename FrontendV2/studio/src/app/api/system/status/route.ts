import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'https://hrtoolsbackend-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    console.log('System status API route called');
    console.log('Auth header:', authHeader ? 'Present' : 'Missing');
    console.log('Backend URL:', `${BACKEND_API_URL}/health`);
    
    const response = await fetch(`${BACKEND_API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    console.log('Backend response status:', response.status);
    console.log('Backend response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.log('Backend error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status}, body: ${errorText}`);
    }

    const data = await response.json();
    console.log('Backend health response:', data);
    
    // Transform the basic health response into the expected SystemStatus format
    const transformedData = {
      success: true,
      system_status: {
        basic_health: {
          supabase: { status: data.status === 'healthy' ? 'healthy' : 'degraded' },
          ai_basic: { status: data.status === 'healthy' ? 'healthy' : 'degraded' }
        },
        enhanced_ai_status: {
          agentic_system: data.status === 'healthy' ? 'operational' : 'degraded',
          '4_agent_analysis': data.status === 'healthy' ? 'ready' : 'busy'
        }
      }
    };
    
    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Error fetching system status:', error);
    console.error('Backend URL:', `${BACKEND_API_URL}/health`);
    console.error('Auth header present:', !!request.headers.get('authorization'));
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch system status',
        message: error instanceof Error ? error.message : 'Unknown error',
        backend_url: `${BACKEND_API_URL}/health`
      },
      { status: 500 }
    );
  }
}

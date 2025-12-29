import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'https://hrtoolsbackend-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    console.log('Railway performance API route called');
    console.log('Auth header:', authHeader ? 'Present' : 'Missing');
    console.log('Backend URL:', `${BACKEND_API_URL}/api/railway/performance`);
    
    const response = await fetch(`${BACKEND_API_URL}/api/railway/performance`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    console.log('Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.log('Backend error response:', errorText);
      throw new Error(`Backend responded with status: ${response.status}, body: ${errorText}`);
    }

    const data = await response.json();
    console.log('Backend railway performance response:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching railway performance:', error);
    console.error('Backend URL:', `${BACKEND_API_URL}/api/railway/performance`);
    console.error('Auth header present:', !!request.headers.get('authorization'));
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch railway performance',
        message: error instanceof Error ? error.message : 'Unknown error',
        backend_url: `${BACKEND_API_URL}/api/railway/performance`
      },
      { status: 500 }
    );
  }
}

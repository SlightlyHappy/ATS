import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'https://hrtoolsbackend-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    
    const response = await fetch(`${BACKEND_API_URL}/api/payments/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching payment history:', error);
    console.error('Backend URL:', `${BACKEND_API_URL}/api/payments/history`);
    console.error('Auth header present:', !!request.headers.get('authorization'));
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch payment history',
        message: error instanceof Error ? error.message : 'Unknown error',
        backend_url: `${BACKEND_API_URL}/api/payments/history`
      },
      { status: 500 }
    );
  }
}

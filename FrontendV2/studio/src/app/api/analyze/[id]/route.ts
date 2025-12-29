import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'https://hrtoolsbackend-production.up.railway.app';

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const authHeader = request.headers.get('authorization');
    const body = await request.json();
    const resumeId = params.id;
    
    const response = await fetch(`${BACKEND_API_URL}/api/analyze/${resumeId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error analyzing resume:', error);
    console.error('Backend URL:', `${BACKEND_API_URL}/api/analyze/${params.id}`);
    console.error('Auth header present:', !!request.headers.get('authorization'));
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to analyze resume',
        message: error instanceof Error ? error.message : 'Unknown error',
        backend_url: `${BACKEND_API_URL}/api/analyze/${params.id}`
      },
      { status: 500 }
    );
  }
}

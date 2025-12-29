import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'https://hrtoolsbackend-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    const response = await fetch(`${BACKEND_API_URL}/api/admin/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    // Handle authentication errors specifically
    if (response.status === 401) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'authentication_required',
          message: 'Please log in to access admin stats'
        },
        { status: 401 }
      );
    }

    if (response.status === 403) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'insufficient_permissions',
          message: 'Admin permissions required to access this resource'
        },
        { status: 403 }
      );
    }

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch admin stats',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

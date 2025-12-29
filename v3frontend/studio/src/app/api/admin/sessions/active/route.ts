import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('👥 STUB: Admin active sessions requested')

    // Return stub response - session management not in backend docs
    return NextResponse.json({
      success: true,
      data: {
        message: "Session management not yet implemented in backend",
        active_sessions: [],
        total_count: 0
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin active sessions stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature not implemented',
        message: 'Session management is not yet available in the backend'
      },
      { status: 501 }
    )
  }
}

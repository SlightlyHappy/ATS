import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('🏥 STUB: Admin system health requested')

    // Return stub response - backend has /admin/health instead
    return NextResponse.json({
      success: true,
      service: "admin_system_routes",
      status: "healthy",
      data: {
        message: "This endpoint maps to /admin/health",
        redirect_to: "/api/admin/health",
        system_status: "operational"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin system health stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature mapping required',
        message: 'Use /api/admin/health instead'
      },
      { status: 501 }
    )
  }
}

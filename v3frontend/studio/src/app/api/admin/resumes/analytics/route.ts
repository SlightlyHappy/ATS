import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('📊 STUB: Admin resumes analytics requested')

    // Return stub response - this specific analytics endpoint not in backend docs
    // Backend has /admin/analytics/overview instead
    return NextResponse.json({
      success: true,
      data: {
        message: "This endpoint maps to /admin/analytics/overview",
        redirect_to: "/api/admin/analytics/overview",
        analytics: {
          total_resumes: 0,
          processed_resumes: 0,
          pending_resumes: 0,
          avg_processing_time: 0
        }
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin resumes analytics stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature mapping required',
        message: 'Use /api/admin/analytics/overview instead'
      },
      { status: 501 }
    )
  }
}

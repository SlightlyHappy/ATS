import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    console.log('⚖️ STUB: User legal query submission requested')

    // Return stub response - legal functionality not in backend docs
    return NextResponse.json({
      success: true,
      data: {
        query_id: "stub-user-legal-query-001",
        status: "feature_not_available",
        message: "Legal query submission feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ User legal query submission stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature not implemented',
        message: 'Legal functionality is not yet available in the backend'
      },
      { status: 501 }
    )
  }
}

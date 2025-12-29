import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('⚖️ STUB: User legal queries requested')

    // Return stub response - legal functionality not in backend docs
    return NextResponse.json({
      success: true,
      data: {
        queries: [],
        pagination: {
          page: 1,
          limit: 10,
          total: 0,
          total_pages: 0
        },
        message: "Legal query feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ User legal queries stub error:', error)
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

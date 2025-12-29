import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params

    console.log('🔄 STUB: Admin user trial reset requested for ID:', userId)

    // Return stub response - this functionality not implemented in backend yet
    return NextResponse.json({
      success: true,
      data: {
        user_id: userId,
        message: "Trial reset feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin user trial reset stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature not implemented',
        message: 'Trial reset is not yet available in the backend'
      },
      { status: 501 }
    )
  }
}

import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    console.log('💳 STUB: User credits requested')

    // Return stub response - user credit management not in backend docs
    return NextResponse.json({
      success: true,
      data: {
        balance: 0,
        history: [],
        message: "Credit management feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ User credits stub error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: 'Feature not implemented',
        message: 'Credit management is not yet available in the backend'
      },
      { status: 501 }
    )
  }
}

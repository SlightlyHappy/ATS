import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params

    console.log('💳 STUB: Admin user credits requested for ID:', userId)

    // Return stub response - this functionality not implemented in backend yet
    return NextResponse.json({
      success: true,
      data: {
        user_id: userId,
        credits: 0,
        message: "Credit management feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin user credits stub error:', error)
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

export async function POST(
  request: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const { userId } = params

    console.log('💳 STUB: Admin user credits update requested for ID:', userId)

    // Return stub response - this functionality not implemented in backend yet
    return NextResponse.json({
      success: true,
      data: {
        user_id: userId,
        message: "Credit update feature not yet implemented in backend"
      },
      stub: true
    }, { status: 200 })

  } catch (error) {
    console.error('❌ Admin user credits update stub error:', error)
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

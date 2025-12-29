"use client"

import React, { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, CreditCard, Home, Receipt, ArrowRight } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import Link from 'next/link'

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { toast } = useToast()
  
  const [paymentDetails, setPaymentDetails] = useState({
    orderId: '',
    paymentId: '',
    amount: '',
    credits: '',
    packageName: ''
  })

  useEffect(() => {
    // Extract payment details from URL parameters
    const orderId = searchParams.get('order_id') || ''
    const paymentId = searchParams.get('payment_id') || ''
    const amount = searchParams.get('amount') || ''
    const credits = searchParams.get('credits') || ''
    const packageName = searchParams.get('package') || ''

    setPaymentDetails({
      orderId,
      paymentId,
      amount,
      credits,
      packageName
    })

    // Show success toast
    if (credits) {
      toast({
        title: "Payment Successful! 🎉",
        description: `${credits} credits have been added to your account.`,
        duration: 5000,
      })
    }

    // Auto-redirect to billing page after 10 seconds
    const timer = setTimeout(() => {
      router.push('/user/billing')
    }, 10000)

    return () => clearTimeout(timer)
  }, [searchParams, router, toast])

  const formatDate = () => {
    return new Date().toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full space-y-6">
        {/* Success Icon */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Payment Successful!
          </h1>
          <p className="text-gray-600">
            Your payment has been processed successfully and credits have been added to your account.
          </p>
        </div>

        {/* Payment Details Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5" />
              Payment Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {paymentDetails.packageName && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Package:</span>
                <Badge variant="secondary">{paymentDetails.packageName}</Badge>
              </div>
            )}
            
            {paymentDetails.credits && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Credits Added:</span>
                <span className="font-semibold text-green-600">
                  +{paymentDetails.credits} Credits
                </span>
              </div>
            )}
            
            {paymentDetails.amount && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Amount Paid:</span>
                <span className="font-semibold">₹{paymentDetails.amount}</span>
              </div>
            )}
            
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Payment Date:</span>
              <span className="font-medium">{formatDate()}</span>
            </div>
            
            {paymentDetails.orderId && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Order ID:</span>
                <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                  {paymentDetails.orderId}
                </span>
              </div>
            )}
            
            {paymentDetails.paymentId && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Payment ID:</span>
                <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                  {paymentDetails.paymentId}
                </span>
              </div>
            )}

            <div className="pt-4 border-t">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span>Payment verified and processed successfully</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps Card */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-3">What's Next?</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-semibold text-blue-600">1</span>
                </div>
                <div>
                  <p className="font-medium">Start Analyzing Resumes</p>
                  <p className="text-sm text-muted-foreground">
                    Use your credits to get detailed insights on candidate resumes.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-semibold text-blue-600">2</span>
                </div>
                <div>
                  <p className="font-medium">Access Legal Assistance</p>
                  <p className="text-sm text-muted-foreground">
                    Get AI-powered help with HR legal queries and policies.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-semibold text-blue-600">3</span>
                </div>
                <div>
                  <p className="font-medium">Track Your Usage</p>
                  <p className="text-sm text-muted-foreground">
                    Monitor your credit balance and transaction history.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Button variant="outline" asChild>
            <Link href="/user/billing">
              <CreditCard className="w-4 h-4 mr-2" />
              View Billing
            </Link>
          </Button>
          
          <Button asChild>
            <Link href="/user/submit">
              <ArrowRight className="w-4 h-4 mr-2" />
              Submit Resume
            </Link>
          </Button>
        </div>

        <div className="text-center">
          <Button variant="ghost" asChild>
            <Link href="/user">
              <Home className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Link>
          </Button>
        </div>

        {/* Auto-redirect Notice */}
        <div className="text-center text-sm text-muted-foreground">
          <p>You will be automatically redirected to the billing page in 10 seconds.</p>
        </div>
      </div>
    </div>
  )
}

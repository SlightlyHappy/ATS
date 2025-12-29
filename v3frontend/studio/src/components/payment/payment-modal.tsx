"use client"

import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { PaymentService, PaymentPackage, CreateOrderResponse } from '@/services/payment.service'
import { Loader2, CreditCard, Shield, CheckCircle, AlertCircle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PaymentModalProps {
  isOpen: boolean
  onCloseAction: () => void
  packageId: string
  onSuccessAction: (result: { credits: number; orderId: string }) => void
  onErrorAction: (error: string) => void
}

declare global {
  interface Window {
    Razorpay: any
  }
}

export function PaymentModal({ 
  isOpen, 
  onCloseAction, 
  packageId, 
  onSuccessAction, 
  onErrorAction 
}: PaymentModalProps) {
  const [selectedPackage, setSelectedPackage] = useState<PaymentPackage | null>(null)
  const [orderData, setOrderData] = useState<CreateOrderResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<'loading' | 'confirm' | 'processing' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)
  const [scriptLoaded, setScriptLoaded] = useState(false)

  // Load Razorpay script
  useEffect(() => {
    const loadRazorpayScript = () => {
      return new Promise((resolve, reject) => {
        if (window.Razorpay) {
          setScriptLoaded(true)
          resolve(true)
          return
        }

        const script = document.createElement('script')
        script.src = 'https://checkout.razorpay.com/v1/checkout.js'
        script.onload = () => {
          setScriptLoaded(true)
          resolve(true)
        }
        script.onerror = () => reject(new Error('Failed to load Razorpay script'))
        document.body.appendChild(script)
      })
    }

    if (isOpen) {
      loadRazorpayScript().catch((err) => {
        console.error('❌ Failed to load Razorpay script:', err)
        setError('Failed to load payment system. Please try again.')
        setStep('error')
      })
    }
  }, [isOpen])

  // Load package details when modal opens
  useEffect(() => {
    if (isOpen && packageId) {
      loadPackageDetails()
    }
  }, [isOpen, packageId])

  const loadPackageDetails = async () => {
    try {
      setLoading(true)
      setStep('loading')
      setError(null)

      console.log('💳 PaymentModal: Loading package details for:', packageId)
      
      const result = await PaymentService.getPackages()
      if (result.success) {
        const pkg = result.packages.find(p => p.id === packageId)
        if (pkg) {
          setSelectedPackage(pkg)
          setStep('confirm')
          console.log('✅ PaymentModal: Package loaded:', pkg.name)
        } else {
          throw new Error('Package not found')
        }
      } else {
        throw new Error(result.error || 'Failed to load package details')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load package details'
      console.error('❌ PaymentModal: Error loading package:', errorMessage)
      setError(errorMessage)
      setStep('error')
    } finally {
      setLoading(false)
    }
  }

  const handlePayment = async () => {
    if (!selectedPackage || !scriptLoaded) return

    try {
      setLoading(true)
      setStep('processing')
      setError(null)

      console.log('💳 PaymentModal: Creating payment order...')
      
      // Create order
      const orderResponse = await PaymentService.createOrder({
        payment_type: selectedPackage.id,
        package_id: selectedPackage.id
      })

      setOrderData(orderResponse)
      console.log('✅ PaymentModal: Order created:', orderResponse.order_id)

      // Configure Razorpay options
      const options = {
        key: orderResponse.razorpay_key,
        amount: orderResponse.amount,
        currency: orderResponse.currency,
        name: 'HR ATS System',
        description: `${selectedPackage.name} - ${selectedPackage.credits} Credits`,
        order_id: orderResponse.order_id,
        handler: async (response: any) => {
          console.log('💳 PaymentModal: Payment successful, verifying...')
          await handlePaymentSuccess(response)
        },
        prefill: {
          name: 'HR User',
          email: 'user@example.com', // This should come from user context
        },
        theme: {
          color: '#3b82f6'
        },
        modal: {
          ondismiss: () => {
            console.log('💳 PaymentModal: Payment dismissed by user')
            setStep('confirm')
            setLoading(false)
          }
        }
      }

      console.log('💳 PaymentModal: Opening Razorpay checkout...')
      const razorpay = new window.Razorpay(options)
      razorpay.open()

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Payment initialization failed'
      console.error('❌ PaymentModal: Payment error:', errorMessage)
      setError(errorMessage)
      setStep('error')
      setLoading(false)
      onErrorAction(errorMessage)
    }
  }

  const handlePaymentSuccess = async (razorpayResponse: any) => {
    try {
      console.log('✅ PaymentModal: Verifying payment...', razorpayResponse.razorpay_payment_id)
      
      const verificationResult = await PaymentService.verifyPayment({
        razorpay_order_id: razorpayResponse.razorpay_order_id,
        razorpay_payment_id: razorpayResponse.razorpay_payment_id,
        razorpay_signature: razorpayResponse.razorpay_signature
      })

      console.log('✅ PaymentModal: Payment verified successfully')
      setStep('success')
      setLoading(false)

      // Call success callback
      onSuccessAction({
        credits: verificationResult.credits_added,
        orderId: verificationResult.order_id
      })

      // Auto-close after 3 seconds
      setTimeout(() => {
        onCloseAction()
      }, 3000)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Payment verification failed'
      console.error('❌ PaymentModal: Verification error:', errorMessage)
      setError(errorMessage)
      setStep('error')
      setLoading(false)
      onErrorAction(errorMessage)
    }
  }

  const handleClose = () => {
    if (!loading && step !== 'processing') {
      onCloseAction()
      // Reset state
      setTimeout(() => {
        setStep('loading')
        setSelectedPackage(null)
        setOrderData(null)
        setError(null)
      }, 200)
    }
  }

  const renderContent = () => {
    switch (step) {
      case 'loading':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Loading package details...</p>
          </div>
        )

      case 'confirm':
        if (!selectedPackage) return null
        
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  {selectedPackage.name}
                  <Badge variant="secondary">{selectedPackage.credits} Credits</Badge>
                </CardTitle>
                <CardDescription>{selectedPackage.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-2xl font-bold mb-4">
                  <span>Total Amount:</span>
                  <span>₹{selectedPackage.price}</span>
                </div>
                
                <div className="space-y-2 mb-4">
                  {selectedPackage.features.map((feature, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>

                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Your payment is secured by RazorPay with 256-bit SSL encryption. 
                    Credits will be added instantly upon successful payment.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button variant="outline" onClick={handleClose} className="flex-1">
                Cancel
              </Button>
              <Button 
                onClick={handlePayment} 
                disabled={loading || !scriptLoaded}
                className="flex-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    Pay ₹{selectedPackage.price}
                  </>
                )}
              </Button>
            </div>
          </div>
        )

      case 'processing':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
            <p className="text-lg font-medium mb-2">Processing Payment...</p>
            <p className="text-muted-foreground text-center">
              Please complete the payment in the RazorPay window.<br />
              Do not close this dialog until payment is complete.
            </p>
          </div>
        )

      case 'success':
        return (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
            <h3 className="text-xl font-bold mb-2">Payment Successful!</h3>
            <p className="text-muted-foreground mb-4">
              Your credits have been added to your account.
            </p>
            {selectedPackage && (
              <Badge variant="secondary" className="text-lg px-4 py-2">
                +{selectedPackage.credits} Credits Added
              </Badge>
            )}
            <p className="text-sm text-muted-foreground mt-4">
              This dialog will close automatically...
            </p>
          </div>
        )

      case 'error':
        return (
          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            
            <div className="flex gap-3">
              <Button variant="outline" onClick={handleClose} className="flex-1">
                Close
              </Button>
              <Button onClick={loadPackageDetails} className="flex-1">
                Try Again
              </Button>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className={cn(
        "sm:max-w-md",
        (step === 'confirm' || step === 'error') && "sm:max-w-lg"
      )}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            Complete Payment
            {!loading && step !== 'processing' && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleClose}
                className="h-auto p-1"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </DialogTitle>
          <DialogDescription>
            {step === 'confirm' && 'Review your purchase and complete the payment'}
            {step === 'processing' && 'Payment is being processed'}
            {step === 'success' && 'Your payment has been processed successfully'}
            {step === 'error' && 'There was an issue processing your payment'}
          </DialogDescription>
        </DialogHeader>
        
        {renderContent()}
      </DialogContent>
    </Dialog>
  )
}

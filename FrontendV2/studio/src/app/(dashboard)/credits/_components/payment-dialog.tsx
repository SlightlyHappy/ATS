
'use client';
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { IndianRupee, Zap, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

declare global {
  interface Window {
    Razorpay: any;
  }
}

const paymentPackages = [
  { id: 'queue_skip', name: 'Instant Queue Skip', price: 40, credits: 'Instant Processing', description: "Jump the queue for one analysis." },
  { id: 'credit_package_10', name: '10 Premium Credits', price: 300, credits: '10 Credits', description: "For enhanced AI processing." },
  { id: 'credit_package_25', name: '25 Premium Credits', price: 650, credits: '25 Credits', description: "Our best value package." },
];

type PaymentDialogProps = {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onPaymentSuccess: () => void;
  onPaymentError: (errorMsg: string) => void;
};

export function PaymentDialog({ isOpen, onOpenChange, onPaymentSuccess, onPaymentError }: PaymentDialogProps) {
  const [selectedPackage, setSelectedPackage] = useState(paymentPackages[1].id);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initiatePayment = async () => {
    setIsLoading(true);
    setError(null);

    const token = localStorage.getItem('auth_token');
    if (!token) {
        onPaymentError('You are not logged in. Please log in to make a purchase.');
        setIsLoading(false);
        return;
    }

    try {
      // Step 1: Create Order
      const orderResponse = await fetch('/api/payment/create-order', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ payment_type: selectedPackage, return_url: window.location.href })
      });
      const orderData = await orderResponse.json();

      if (!orderResponse.ok || !orderData.success) {
        throw new Error(orderData.message || 'Failed to create payment order.');
      }

      // Step 2: Open Razorpay Checkout
      const options = {
        key: orderData.razorpay_key,
        amount: orderData.amount,
        currency: orderData.currency,
        name: "HR Intel Pro",
        description: `Purchase of ${selectedPackage}`,
        order_id: orderData.order_id,
        handler: async (response: any) => {
          // Step 3: Verify Payment
          try {
            const verifyResponse = await fetch('/api/payment/verify', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                payment_id: response.razorpay_payment_id,
                order_id: response.razorpay_order_id,
                signature: response.razorpay_signature
              })
            });

            const verifyData = await verifyResponse.json();
            if (!verifyResponse.ok || !verifyData.success) {
              throw new Error(verifyData.message || 'Payment verification failed.');
            }
            
            onPaymentSuccess();

          } catch (verifyError: any) {
            onPaymentError(verifyError.message);
          }
        },
        prefill: {
          // You can prefill user data here if available
          // name: "John Doe",
          // email: "john.doe@example.com"
        },
        theme: {
          color: "#2563eb"
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response: any) {
          onPaymentError(`Payment failed: ${response.error.description}`);
      });
      rzp.open();

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2"><IndianRupee /> Purchase Credits</DialogTitle>
          <DialogDescription>
            Choose a package to top up your account and unlock premium features.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
            {error && (
                <Alert variant="destructive" className="mb-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}
            <RadioGroup value={selectedPackage} onValueChange={setSelectedPackage} className="space-y-3">
                {paymentPackages.map((pkg) => (
                    <Label
                        key={pkg.id}
                        htmlFor={pkg.id}
                        className="flex items-center justify-between cursor-pointer rounded-lg border p-4 [&:has([data-state=checked])]:border-primary"
                    >
                        <div className="space-y-1">
                            <p className="font-bold">{pkg.name}</p>
                            <p className="text-sm text-muted-foreground">{pkg.description}</p>
                            <div className="flex items-center gap-2 text-primary font-semibold">
                                <Zap className="h-4 w-4"/>
                                <span>{pkg.credits}</span>
                            </div>
                        </div>
                        <div className="text-right">
                           <p className="text-xl font-bold">₹{pkg.price}</p>
                           <RadioGroupItem value={pkg.id} id={pkg.id} className="mt-2 ml-auto"/>
                        </div>
                    </Label>
                ))}
            </RadioGroup>
        </div>
        <DialogFooter>
          <Button onClick={initiatePayment} className="w-full" disabled={isLoading}>
            {isLoading ? 'Processing...' : `Pay ₹${paymentPackages.find(p => p.id === selectedPackage)?.price}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

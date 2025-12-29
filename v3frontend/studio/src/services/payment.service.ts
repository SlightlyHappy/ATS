/**
 * @file Payment service for RazorPay integration
 * Implements backend v1.3 payment endpoints
 */

import { apiClient } from './api';

interface PaymentPackage {
  id: string;
  name: string;
  price: number;
  credits: number;
  description: string;
  features: string[];
  duration: string;
}

interface CreateOrderRequest {
  payment_type: string;
  package_id?: string;
}

interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  razorpay_key: string;
}

interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

interface VerifyPaymentResponse {
  credits_added: number;
  processing_tier: string;
  order_id: string;
}

class PaymentServiceClass {
  
  /**
   * Get available payment packages
   */
  async getPackages(): Promise<{ success: boolean; packages: PaymentPackage[]; error?: string }> {
    try {
      console.log('💰 PaymentService: Fetching payment packages...');
      
      const response = await apiClient.getPaymentPackages();
      
      if (response.success && response.data?.packages) {
        console.log('✅ Payment packages loaded:', response.data.packages.length);
        return {
          success: true,
          packages: response.data.packages
        };
      }
      
      throw new Error(response.error || 'Failed to load packages');
    } catch (error) {
      console.error('❌ PaymentService.getPackages error:', error);
      return {
        success: false,
        packages: [],
        error: error instanceof Error ? error.message : 'Failed to load payment packages'
      };
    }
  }

  /**
   * Create RazorPay order
   */
  async createOrder(request: CreateOrderRequest): Promise<CreateOrderResponse> {
    try {
      console.log('💳 PaymentService: Creating order...', request);
      
      const response = await apiClient.createPaymentOrder(request);
      
      if (response.success && response.data) {
        console.log('✅ Order created successfully:', response.data.order_id);
        return response.data;
      }
      
      throw new Error(response.error || 'Failed to create order');
    } catch (error) {
      console.error('❌ PaymentService.createOrder error:', error);
      throw error;
    }
  }

  /**
   * Verify completed payment
   */
  async verifyPayment(request: VerifyPaymentRequest): Promise<VerifyPaymentResponse> {
    try {
      console.log('✅ PaymentService: Verifying payment...', {
        order_id: request.razorpay_order_id,
        payment_id: request.razorpay_payment_id
      });
      
      const response = await apiClient.verifyPayment(request);
      
      if (response.success && response.data) {
        console.log('✅ Payment verified successfully:', {
          credits_added: response.data.credits_added,
          processing_tier: response.data.processing_tier
        });
        return response.data;
      }
      
      throw new Error(response.error || 'Payment verification failed');
    } catch (error) {
      console.error('❌ PaymentService.verifyPayment error:', error);
      throw error;
    }
  }

  /**
   * Initialize RazorPay checkout
   */
  async initiateRazorPayCheckout(orderData: CreateOrderResponse, onSuccess: (response: any) => void, onError: (error: any) => void) {
    try {
      // Load RazorPay script if not already loaded
      if (!window.Razorpay) {
        await this.loadRazorPayScript();
      }

      const options = {
        key: orderData.razorpay_key,
        amount: orderData.amount,
        currency: orderData.currency,
        name: 'HR ATS Platform',
        description: 'Resume Analysis Credits',
        order_id: orderData.order_id,
        handler: async (response: any) => {
          try {
            const verificationResult = await this.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature
            });
            onSuccess(verificationResult);
          } catch (error) {
            onError(error);
          }
        },
        modal: {
          ondismiss: () => {
            console.log('Payment modal dismissed');
          }
        },
        theme: {
          color: '#3B82F6'
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error('❌ RazorPay checkout error:', error);
      onError(error);
    }
  }

  /**
   * Load RazorPay script dynamically
   */
  private loadRazorPayScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (document.getElementById('razorpay-script')) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.id = 'razorpay-script';
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load RazorPay script'));
      document.head.appendChild(script);
    });
  }
}

// Extend window type for RazorPay
declare global {
  interface Window {
    Razorpay: any;
  }
}

export const PaymentService = new PaymentServiceClass();
export type { PaymentPackage, CreateOrderRequest, CreateOrderResponse, VerifyPaymentRequest, VerifyPaymentResponse };

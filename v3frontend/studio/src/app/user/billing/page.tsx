"use client"

import React from 'react'
import PageHeader from '@/components/page-header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Clock, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function BillingPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <PageHeader 
        title="Billing & Credits" 
        description="Manage your account billing and credits"
      />

      <div className="max-w-2xl mx-auto">
        <Card className="text-center">
          <CardHeader className="pb-4">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
            <CardTitle className="text-2xl">Payment System Coming Soon</CardTitle>
            <CardDescription className="text-lg">
              We're working hard to bring you a seamless payment experience
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <p className="text-gray-600">
                Our billing and credit system is currently under development. 
                For now, enjoy unlimited access to all features.
              </p>
              <p className="text-sm text-gray-500">
                We'll notify you when the payment system becomes available.
              </p>
            </div>
            
            <div className="flex justify-center space-x-4">
              <Link href="/user">
                <Button variant="outline" className="flex items-center gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back to Dashboard
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

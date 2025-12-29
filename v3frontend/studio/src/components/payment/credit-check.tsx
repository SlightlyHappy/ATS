"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CreditBalance } from '@/components/payment/credit-balance'
import { EnhancedUserService } from '@/services/enhanced-user.service'
import { Coins, AlertTriangle, Lock, Unlock } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CreditCheckProps {
  requiredCredits: number
  onCreditCheckCompleteAction: (hasEnoughCredits: boolean) => void
  onTopUpAction: () => void
}

export function CreditCheck({ 
  requiredCredits, 
  onCreditCheckCompleteAction, 
  onTopUpAction 
}: CreditCheckProps) {
  const [credits, setCredits] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCredits()
  }, [])

  useEffect(() => {
    if (credits !== null) {
      onCreditCheckCompleteAction(credits >= requiredCredits)
    }
  }, [credits, requiredCredits, onCreditCheckCompleteAction])

  const loadCredits = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await EnhancedUserService.getCredits()
      
      if (result.success && result.data) {
        setCredits(result.data.balance)
      } else {
        throw new Error(result.error || 'Failed to load credits')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load credits'
      setError(errorMessage)
      setCredits(0)
    } finally {
      setLoading(false)
    }
  }

  const hasEnoughCredits = credits !== null && credits >= requiredCredits
  const creditsShortfall = credits !== null ? Math.max(0, requiredCredits - credits) : 0

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            <span className="ml-2 text-muted-foreground">Checking credit balance...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button 
                variant="link" 
                className="p-0 ml-2" 
                onClick={loadCredits}
              >
                Try again
              </Button>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Coins className="w-5 h-5 text-yellow-500" />
          Credit Requirement
        </CardTitle>
        <CardDescription>
          Resume analysis requires credits from your account
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
          <div>
            <p className="font-medium">Required for this analysis:</p>
            <p className="text-sm text-muted-foreground">Advanced resume analysis with AI insights</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">{requiredCredits}</div>
            <div className="text-sm text-muted-foreground">credits</div>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium">Your current balance:</p>
            <p className="text-sm text-muted-foreground">Available credits in your account</p>
          </div>
          <div className="text-right">
            <div className={cn(
              "text-2xl font-bold",
              hasEnoughCredits ? "text-green-600" : "text-red-600"
            )}>
              {credits}
            </div>
            <div className="text-sm text-muted-foreground">credits</div>
          </div>
        </div>

        {hasEnoughCredits ? (
          <Alert>
            <Unlock className="h-4 w-4" />
            <AlertDescription className="text-green-700">
              ✅ You have sufficient credits to proceed with the analysis.
              <br />
              <strong>{credits - requiredCredits} credits</strong> will remain after this analysis.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert variant="destructive">
            <Lock className="h-4 w-4" />
            <AlertDescription>
              ❌ Insufficient credits for analysis.
              <br />
              You need <strong>{creditsShortfall} more credits</strong> to proceed.
            </AlertDescription>
          </Alert>
        )}

        {!hasEnoughCredits && (
          <div className="space-y-3">
            <Button 
              onClick={onTopUpAction} 
              className="w-full"
              size="lg"
            >
              <Coins className="w-4 h-4 mr-2" />
              Top Up Credits
            </Button>
            
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Credits are instantly added to your account after payment
              </p>
            </div>
          </div>
        )}

        <div className="pt-4 border-t">
          <CreditBalance 
            compact={true} 
            onTopUpAction={onTopUpAction}
            showTopUpButton={false}
          />
        </div>
      </CardContent>
    </Card>
  )
}

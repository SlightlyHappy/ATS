"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Coins, Plus, RefreshCw, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { EnhancedUserService } from '@/services/enhanced-user.service'

interface CreditBalanceProps {
  onTopUpAction?: () => void
  showTopUpButton?: boolean
  className?: string
  compact?: boolean
}

interface CreditInfo {
  balance: number
  lastUpdated: string
  recentTransactions?: {
    amount: number
    type: 'credit' | 'debit'
    description: string
    timestamp: string
  }[]
}

export function CreditBalance({ 
  onTopUpAction, 
  showTopUpButton = true, 
  className,
  compact = false
}: CreditBalanceProps) {
  const { user } = useAuth()
  const [creditInfo, setCreditInfo] = useState<CreditInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      loadCreditBalance()
    }
  }, [user])

  const loadCreditBalance = async () => {
    try {
      setLoading(true)
      setError(null)

      console.log('💰 CreditBalance: Loading credit information...')
      
      // Try to get credit information from user service
      const result = await EnhancedUserService.getCredits()
      
      if (result.success && result.data) {
        setCreditInfo({
          balance: result.data.balance || 0,
          lastUpdated: new Date().toISOString(),
          recentTransactions: result.data.history?.slice(0, 5).map((tx: any) => ({
            amount: tx.amount || 0,
            type: tx.type || 'credit',
            description: tx.description || 'Credit transaction',
            timestamp: tx.timestamp || new Date().toISOString()
          }))
        })
        console.log('✅ CreditBalance: Loaded credit info:', result.data.balance)
      } else {
        throw new Error(result.error || 'Failed to load credit information')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load credit balance'
      console.error('❌ CreditBalance: Error loading credits:', errorMessage)
      setError(errorMessage)
      
      // Set default credit info in case of error
      setCreditInfo({
        balance: 0,
        lastUpdated: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadCreditBalance()
  }

  const formatLastUpdated = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / (1000 * 60))
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
      return date.toLocaleDateString()
    } catch {
      return 'Unknown'
    }
  }

  const getCreditColor = (balance: number) => {
    if (balance >= 50) return 'text-green-600'
    if (balance >= 20) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getCreditBadgeVariant = (balance: number): "default" | "secondary" | "destructive" | "outline" => {
    if (balance >= 50) return 'default'
    if (balance >= 20) return 'secondary'
    return 'destructive'
  }

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <div className="flex items-center gap-1">
          <Coins className="w-4 h-4 text-yellow-500" />
          <span className={cn("font-semibold", getCreditColor(creditInfo?.balance || 0))}>
            {loading ? '...' : creditInfo?.balance || 0}
          </span>
          <span className="text-xs text-muted-foreground">credits</span>
        </div>
        
        {showTopUpButton && onTopUpAction && (
          <Button 
            size="sm" 
            variant="outline" 
            onClick={onTopUpAction}
            className="h-7 px-2"
          >
            <Plus className="w-3 h-3" />
          </Button>
        )}
        
        <Button 
          size="sm" 
          variant="ghost" 
          onClick={handleRefresh}
          disabled={loading}
          className="h-7 px-2"
        >
          <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
        </Button>
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-yellow-500" />
            Credit Balance
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </Button>
        </CardTitle>
        <CardDescription>
          Your current credit balance and usage information
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-baseline gap-2">
              <span className={cn(
                "text-3xl font-bold",
                getCreditColor(creditInfo?.balance || 0)
              )}>
                {loading ? '---' : creditInfo?.balance || 0}
              </span>
              <span className="text-muted-foreground">credits</span>
            </div>
            {creditInfo && (
              <p className="text-sm text-muted-foreground mt-1">
                Last updated {formatLastUpdated(creditInfo.lastUpdated)}
              </p>
            )}
          </div>
          
          <Badge variant={getCreditBadgeVariant(creditInfo?.balance || 0)}>
            {(creditInfo?.balance || 0) >= 50 ? 'Healthy' : 
             (creditInfo?.balance || 0) >= 20 ? 'Low' : 'Critical'}
          </Badge>
        </div>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}

        {(creditInfo?.balance || 0) <= 10 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <div className="flex items-start gap-2">
              <TrendingUp className="w-4 h-4 text-yellow-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-yellow-800">Low Credit Balance</p>
                <p className="text-yellow-700">
                  Consider topping up your credits to continue using all features.
                </p>
              </div>
            </div>
          </div>
        )}

        {showTopUpButton && onTopUpAction && (
          <Button 
            onClick={onTopUpAction} 
            className="w-full"
            variant={(creditInfo?.balance || 0) <= 10 ? "default" : "outline"}
          >
            <Plus className="w-4 h-4 mr-2" />
            Top Up Credits
          </Button>
        )}

        {creditInfo?.recentTransactions && creditInfo.recentTransactions.length > 0 && (
          <div className="pt-2 border-t">
            <h4 className="text-sm font-medium mb-2">Recent Activity</h4>
            <div className="space-y-1">
              {creditInfo.recentTransactions.slice(0, 3).map((transaction, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {transaction.description}
                  </span>
                  <span className={cn(
                    "font-medium",
                    transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                  )}>
                    {transaction.type === 'credit' ? '+' : '-'}{transaction.amount}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

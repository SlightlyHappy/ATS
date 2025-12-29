"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { 
  History, 
  RefreshCw, 
  Download, 
  CreditCard, 
  TrendingUp, 
  TrendingDown,
  Calendar
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { EnhancedUserService } from '@/services/enhanced-user.service'

interface PaymentTransaction {
  id: string
  type: 'credit' | 'debit' | 'purchase' | 'refund'
  amount: number
  credits: number
  description: string
  status: 'completed' | 'pending' | 'failed'
  timestamp: string
  orderId?: string
  packageName?: string
}

interface PaymentHistoryProps {
  className?: string
  limit?: number
  showHeader?: boolean
}

export function PaymentHistory({ 
  className, 
  limit = 10, 
  showHeader = true 
}: PaymentHistoryProps) {
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPaymentHistory()
  }, [])

  const loadPaymentHistory = async () => {
    try {
      setLoading(true)
      setError(null)

      console.log('📋 PaymentHistory: Loading payment history...')
      
      // Get credit history from enhanced user service
      const result = await EnhancedUserService.getCredits()
      
      if (result.success && result.data?.history) {
        // Transform the history data to match our interface
        const transformedTransactions = result.data.history.map((item: any, index: number) => ({
          id: item.id || `tx_${index}`,
          type: item.type || 'credit',
          amount: Math.abs(item.amount || 0),
          credits: item.credits || 0,
          description: item.description || 'Credit transaction',
          status: item.status || 'completed',
          timestamp: item.timestamp || new Date().toISOString(),
          orderId: item.order_id,
          packageName: item.package_name
        })) as PaymentTransaction[]

        setTransactions(transformedTransactions.slice(0, limit))
        console.log('✅ PaymentHistory: Loaded', transformedTransactions.length, 'transactions')
      } else {
        // Set empty array if no history available
        setTransactions([])
        console.log('ℹ️ PaymentHistory: No transaction history available')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load payment history'
      console.error('❌ PaymentHistory: Error loading history:', errorMessage)
      setError(errorMessage)
      setTransactions([])
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadPaymentHistory()
  }

  const handleExport = () => {
    if (transactions.length === 0) return

    const csvContent = [
      ['Date', 'Type', 'Description', 'Amount', 'Credits', 'Status'].join(','),
      ...transactions.map(tx => [
        new Date(tx.timestamp).toLocaleDateString(),
        tx.type,
        `"${tx.description}"`,
        tx.amount,
        tx.credits,
        tx.status
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `payment-history-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    } catch {
      return 'Invalid Date'
    }
  }

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return '--:--'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'credit':
      case 'purchase':
        return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'debit':
        return <TrendingDown className="w-4 h-4 text-red-600" />
      case 'refund':
        return <TrendingUp className="w-4 h-4 text-blue-600" />
      default:
        return <CreditCard className="w-4 h-4 text-gray-600" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'credit':
      case 'purchase':
        return 'text-green-600'
      case 'debit':
        return 'text-red-600'
      case 'refund':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="text-xs">Completed</Badge>
      case 'pending':
        return <Badge variant="secondary" className="text-xs">Pending</Badge>
      case 'failed':
        return <Badge variant="destructive" className="text-xs">Failed</Badge>
      default:
        return <Badge variant="outline" className="text-xs">{status}</Badge>
    }
  }

  return (
    <Card className={className}>
      {showHeader && (
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5" />
              Payment History
            </div>
            <div className="flex items-center gap-2">
              {transactions.length > 0 && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleExport}
                  disabled={loading}
                >
                  <Download className="w-4 h-4" />
                </Button>
              )}
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Your recent credit purchases and transactions
          </CardDescription>
        </CardHeader>
      )}
      
      <CardContent className={showHeader ? "" : "pt-6"}>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading transactions...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600 mb-2">{error}</p>
            <Button variant="outline" onClick={handleRefresh}>
              Try Again
            </Button>
          </div>
        ) : transactions.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground">No transactions found</p>
            <p className="text-sm text-muted-foreground">
              Your payment history will appear here once you make a purchase.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Credits</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">{formatDate(transaction.timestamp)}</div>
                        <div className="text-muted-foreground">{formatTime(transaction.timestamp)}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(transaction.type)}
                        <span className={cn("capitalize text-sm font-medium", getTypeColor(transaction.type))}>
                          {transaction.type}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">{transaction.description}</div>
                        {transaction.orderId && (
                          <div className="text-xs text-muted-foreground">
                            Order: {transaction.orderId}
                          </div>
                        )}
                        {transaction.packageName && (
                          <div className="text-xs text-muted-foreground">
                            Package: {transaction.packageName}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={cn("font-semibold", getTypeColor(transaction.type))}>
                        {transaction.type === 'debit' ? '-' : '+'}₹{transaction.amount}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={cn("font-semibold", getTypeColor(transaction.type))}>
                        {transaction.type === 'debit' ? '-' : '+'}
                        {transaction.credits}
                      </span>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(transaction.status)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {transactions.length >= limit && (
              <div className="text-center pt-4">
                <p className="text-sm text-muted-foreground">
                  Showing last {limit} transactions. 
                  <Button variant="link" className="p-0 ml-1 h-auto" onClick={handleExport}>
                    Export all
                  </Button>
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

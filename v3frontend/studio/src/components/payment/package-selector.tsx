"use client"

import React, { useState, useEffect } from 'react'
import { PricingCard } from './pricing-card'
import { PaymentService, PaymentPackage } from '@/services/payment.service'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, Loader2 } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface PackageSelectorProps {
  onPackageSelectAction: (packageId: string) => void
  selectedPackageId?: string
  isProcessing?: boolean
  className?: string
}

export function PackageSelector({ 
  onPackageSelectAction, 
  selectedPackageId, 
  isProcessing = false,
  className 
}: PackageSelectorProps) {
  const [packages, setPackages] = useState<PaymentPackage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPackages()
  }, [])

  const loadPackages = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('📦 PackageSelector: Loading payment packages...')
      const result = await PaymentService.getPackages()
      
      if (result.success && result.packages) {
        setPackages(result.packages)
        console.log('✅ PackageSelector: Loaded', result.packages.length, 'packages')
      } else {
        throw new Error(result.error || 'Failed to load packages')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load payment packages'
      console.error('❌ PackageSelector: Error loading packages:', errorMessage)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handlePackageSelect = (packageId: string) => {
    if (!isProcessing) {
      console.log('📦 PackageSelector: Package selected:', packageId)
      onPackageSelectAction(packageId)
    }
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Loading payment packages...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="ml-2">
              {error}
              <button 
                onClick={loadPackages}
                className="ml-2 underline hover:no-underline"
              >
                Try again
              </button>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (packages.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="py-8 text-center">
          <p className="text-muted-foreground">No payment packages available at the moment.</p>
        </CardContent>
      </Card>
    )
  }

  // Determine popular package (usually the middle-tier or most credits per rupee)
  const getPopularPackage = (pkgs: PaymentPackage[]) => {
    if (pkgs.length === 0) return null
    
    // Calculate value (credits per rupee) and find the best value
    const packagesWithValue = pkgs.map(pkg => ({
      ...pkg,
      value: pkg.credits / pkg.price
    }))
    
    // Sort by value and pick a middle-high value package as popular
    packagesWithValue.sort((a, b) => b.value - a.value)
    
    // If we have 3+ packages, pick the second best value as "popular"
    // If we have fewer, pick the best value
    return packagesWithValue.length >= 3 ? packagesWithValue[1] : packagesWithValue[0]
  }

  const popularPackage = getPopularPackage(packages)

  return (
    <div className={className}>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold tracking-tight mb-2">
          Choose Your Credit Package
        </h2>
        <p className="text-muted-foreground text-lg">
          Select the perfect plan for your hiring needs. All packages include full feature access.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {packages.map((pkg) => (
          <PricingCard
            key={pkg.id}
            package={pkg}
            isPopular={popularPackage?.id === pkg.id}
            onSelectAction={handlePackageSelect}
            isLoading={isProcessing && selectedPackageId === pkg.id}
            disabled={isProcessing}
          />
        ))}
      </div>
      
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground">
          All payments are processed securely through RazorPay. 
          Credits are added instantly upon successful payment.
        </p>
      </div>
    </div>
  )
}

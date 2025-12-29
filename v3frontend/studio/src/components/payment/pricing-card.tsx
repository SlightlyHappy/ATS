"use client"

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Zap, Star, Crown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PaymentPackage } from '@/services/payment.service'

interface PricingCardProps {
  package: PaymentPackage
  isPopular?: boolean
  onSelectAction: (packageId: string) => void
  isLoading?: boolean
  disabled?: boolean
  className?: string
}

const packageIcons = {
  basic: Zap,
  standard: Star,
  premium: Crown,
  enterprise: Crown
}

const getPackageColor = (packageName: string) => {
  const name = packageName.toLowerCase()
  if (name.includes('premium') || name.includes('enterprise')) return 'from-purple-500 to-pink-500'
  if (name.includes('standard') || name.includes('pro')) return 'from-blue-500 to-cyan-500'
  return 'from-green-500 to-emerald-500'
}

const getPackageIcon = (packageName: string) => {
  const name = packageName.toLowerCase()
  if (name.includes('premium') || name.includes('enterprise')) return Crown
  if (name.includes('standard') || name.includes('pro')) return Star
  return Zap
}

export function PricingCard({ 
  package: pkg, 
  isPopular = false, 
  onSelectAction, 
  isLoading = false, 
  disabled = false,
  className 
}: PricingCardProps) {
  const Icon = getPackageIcon(pkg.name)
  const gradientColor = getPackageColor(pkg.name)
  
  const handleSelect = () => {
    if (!disabled && !isLoading) {
      onSelectAction(pkg.id)
    }
  }

  return (
    <Card 
      className={cn(
        "relative transition-all duration-300 hover:shadow-lg cursor-pointer group",
        isPopular && "ring-2 ring-primary shadow-xl scale-105",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      onClick={handleSelect}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 text-sm font-semibold">
            Most Popular
          </Badge>
        </div>
      )}
      
      <CardHeader className="text-center pb-4">
        <div className={cn(
          "w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4 bg-gradient-to-r",
          gradientColor
        )}>
          <Icon className="w-8 h-8 text-white" />
        </div>
        
        <CardTitle className="text-2xl font-bold">{pkg.name}</CardTitle>
        <CardDescription className="text-sm text-muted-foreground mt-2">
          {pkg.description}
        </CardDescription>
        
        <div className="mt-4">
          <span className="text-4xl font-bold">₹{pkg.price}</span>
          <span className="text-muted-foreground ml-2">
            {pkg.duration}
          </span>
        </div>
        
        <div className="mt-2">
          <Badge variant="secondary" className="text-sm font-medium">
            {pkg.credits} Credits
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-3 mb-6">
          {pkg.features.map((feature, index) => (
            <div key={index} className="flex items-start gap-3">
              <Check className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-muted-foreground leading-relaxed">
                {feature}
              </span>
            </div>
          ))}
        </div>
        
        <Button 
          className={cn(
            "w-full font-semibold py-3 transition-all duration-200",
            isPopular && "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600",
            !isPopular && "hover:scale-[1.02]"
          )}
          disabled={disabled || isLoading}
          onClick={(e) => {
            e.stopPropagation()
            handleSelect()
          }}
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing...
            </div>
          ) : (
            "Choose Plan"
          )}
        </Button>
        
        <p className="text-xs text-center text-muted-foreground mt-3">
          Instant activation • Secure payment • 24/7 support
        </p>
      </CardContent>
    </Card>
  )
}

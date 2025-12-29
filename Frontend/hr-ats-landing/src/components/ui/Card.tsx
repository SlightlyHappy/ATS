'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export const Card: React.FC<CardProps> = ({ children, className, onClick }) => {
  return (
    <div 
      className={cn("bg-white rounded-xl shadow-lg border border-gray-200", className)}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export const CardHeader: React.FC<CardProps> = ({ children, className }) => {
  return (
    <div className={cn("p-6 pb-4", className)}>
      {children}
    </div>
  )
}

export const CardContent: React.FC<CardProps> = ({ children, className }) => {
  return (
    <div className={cn("p-6 pt-0", className)}>
      {children}
    </div>
  )
}

export const CardTitle: React.FC<CardProps> = ({ children, className }) => {
  return (
    <h3 className={cn("text-xl font-semibold text-gray-900", className)}>
      {children}
    </h3>
  )
}

export const CardDescription: React.FC<CardProps> = ({ children, className }) => {
  return (
    <p className={cn("text-gray-600 mt-2", className)}>
      {children}
    </p>
  )
}

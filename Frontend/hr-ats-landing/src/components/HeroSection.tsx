'use client'

import React from 'react'
import { Button } from '@/components/ui/Button'
import { ArrowRight, Play, TrendingUp, Users, DollarSign } from 'lucide-react'
import Image from 'next/image'

export const HeroSection: React.FC = () => {
  return (
    <section className="bg-gradient-to-br from-blue-50 via-white to-purple-50 py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Content */}
        <div className="text-center">
          {/* Badge with Logo */}
          <div className="flex items-center justify-center mb-8">
            <div className="inline-flex items-center px-6 py-3 rounded-full bg-white shadow-lg border border-gray-200">
              <Image
                src="/images/logo/logo_dark.png"
                alt="BearSystems Logo"
                width={24}
                height={24}
                className="w-6 h-6 mr-3"
              />
              <span className="text-gray-800 font-medium">A proud product of BearSystems.co.in</span>
              <span className="mx-2 text-gray-400">•</span>
              <span className="text-blue-600 font-medium">Empowering Businesses</span>
            </div>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6">
            <span className="text-blue-600">AI-Powered</span> HR Revolution
          </h1>
          
          <h2 className="text-xl md:text-2xl lg:text-3xl font-semibold text-gray-700 mb-4">
            Turn ₹5,00,000 HR Costs into ₹50,000 AI Magic
          </h2>
          
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-4xl mx-auto">
            Indian HR consultancies are saving <span className="font-semibold text-blue-600">90% on screening costs</span> while finding better candidates in <span className="font-semibold">1/10th the time</span>
          </p>

          <p className="text-md md:text-lg text-gray-500 mb-12 max-w-3xl mx-auto">
            Powered by 4 specialized AI agents and India's most advanced bias-free hiring model
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button size="lg" className="px-8 py-4 text-lg">
              Get Started Now
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button variant="outline" size="lg" className="px-8 py-4 text-lg">
              <Play className="w-5 h-5 mr-2" />
              Calculate My Savings
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">95%</div>
              <div className="text-gray-700 font-medium">Faster Screening</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-green-600 mb-2">60%</div>
              <div className="text-gray-700 font-medium">Better Hire Quality</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-purple-600 mb-2">₹2.5Cr+</div>
              <div className="text-gray-700 font-medium">Saved by Clients</div>
            </div>
          </div>
        </div>

        {/* Contact Info for Priority Access */}
        <div className="mt-20 text-center">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Don't have an account yet?
            </h3>
            <p className="text-gray-600 mb-6">
              We're onboarding select HR consultancies and companies. Contact us to get priority access to our AI hiring platform.
            </p>
            <div className="flex items-center justify-center space-x-2 text-blue-600 font-medium">
              <span>📧</span>
              <a href="mailto:admin@bearsystems.co.in" className="hover:underline">
                admin@bearsystems.co.in
              </a>
            </div>
            <p className="text-sm text-gray-500 mt-2">Response within 24 hours</p>
          </div>
        </div>
      </div>
    </section>
  )
}

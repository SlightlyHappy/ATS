'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Menu, X, Calculator, Users, LogIn } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="flex items-center space-x-3">
                <Image
                  src="/images/logo/logo_dark.png"
                  alt="BearSystems Logo"
                  width={40}
                  height={40}
                  className="w-10 h-10"
                />
                <div>
                  <div className="font-bold text-gray-900 text-lg">HR ATS</div>
                  <div className="text-xs text-gray-500">by BearSystems</div>
                </div>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors">
              Features
            </a>
            <a href="#calculator" className="text-gray-700 hover:text-blue-600 transition-colors flex items-center">
              <Calculator className="w-4 h-4 mr-1" />
              Calculator
            </a>
            <a href="#about" className="text-gray-700 hover:text-blue-600 transition-colors">
              About Us
            </a>
            <Link href="/login">
              <Button variant="outline" size="sm">
                <LogIn className="w-4 h-4 mr-2" />
                Sign In
              </Button>
            </Link>
            <Link href="/login">
              <Button size="sm">
                Get Started
              </Button>
            </Link>
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:text-gray-900"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-4">
              <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors">
                Features
              </a>
              <a href="#calculator" className="text-gray-700 hover:text-blue-600 transition-colors flex items-center">
                <Calculator className="w-4 h-4 mr-1" />
                Calculator
              </a>
              <a href="#about" className="text-gray-700 hover:text-blue-600 transition-colors">
                About Us
              </a>
              <div className="flex flex-col space-y-2 pt-2">
                <Link href="/login">
                  <Button variant="outline" size="sm">
                    <LogIn className="w-4 h-4 mr-2" />
                    Sign In
                  </Button>
                </Link>
                <Link href="/login">
                  <Button size="sm">
                    Get Started
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

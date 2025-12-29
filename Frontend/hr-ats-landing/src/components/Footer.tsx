'use client'

import React from 'react'
import { Button } from '@/components/ui/Button'
import { 
  Mail, 
  ExternalLink, 
  Calculator, 
  LogIn, 
  Users, 
  Heart,
  Linkedin
} from 'lucide-react'
import Image from 'next/image'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="py-16">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Company Info */}
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <Image
                  src="/images/logo/logo_light.png"
                  alt="BearSystems Logo"
                  width={48}
                  height={48}
                  className="w-12 h-12"
                />
                <div>
                  <div className="font-bold text-xl text-white">HR ATS by BearSystems</div>
                </div>
              </div>
              <p className="text-gray-300 mb-6 leading-relaxed">
                Revolutionizing HR operations with AI-powered resume screening and hiring intelligence. 
                Built specifically for the Indian market with local expertise and compliance.
              </p>
              <div className="flex items-center space-x-2 text-blue-400 mb-4">
                <Mail className="w-4 h-4" />
                <a href="mailto:admin@bearsystems.co.in" className="hover:underline">
                  admin@bearsystems.co.in
                </a>
              </div>
              <div className="flex items-center space-x-2 text-gray-300 mb-4">
                <span>🇮🇳</span>
                <span>India</span>
              </div>
              <a 
                href="https://bearsystems.co.in" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
              >
                Visit BearSystems.co.in
                <ExternalLink className="w-4 h-4 ml-1" />
              </a>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-lg font-semibold mb-6">Quick Links</h3>
              <ul className="space-y-4">
                <li>
                  <a href="#" className="flex items-center text-gray-300 hover:text-white transition-colors">
                    <LogIn className="w-4 h-4 mr-2" />
                    Login
                  </a>
                </li>
                <li>
                  <a href="#calculator" className="flex items-center text-gray-300 hover:text-white transition-colors">
                    <Calculator className="w-4 h-4 mr-2" />
                    ROI Calculator
                  </a>
                </li>
                <li>
                  <a href="#" className="flex items-center text-gray-300 hover:text-white transition-colors">
                    <Users className="w-4 h-4 mr-2" />
                    Request Demo
                  </a>
                </li>
                <li>
                  <a href="#" className="flex items-center text-gray-300 hover:text-white transition-colors">
                    <Users className="w-4 h-4 mr-2" />
                    Partnership
                  </a>
                </li>
              </ul>
            </div>

            {/* Get Started */}
            <div>
              <h3 className="text-lg font-semibold mb-6">Get Started</h3>
              <p className="text-gray-300 mb-6">
                Ready to revolutionize your HR operations?
              </p>
              <div className="space-y-4">
                <Button className="w-full" size="lg">
                  Contact for Access
                </Button>
                <p className="text-sm text-gray-400 text-center">
                  Response within 24 hours
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-800 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <span>© 2025 BearSystems. All rights reserved.</span>
              <span>|</span>
              <span className="flex items-center">
                Made with <Heart className="w-4 h-4 text-red-500 mx-1" /> for Indian HR professionals
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-400">Follow us:</span>
              <a 
                href="https://www.linkedin.com/company/bearsystems-rrk-pvt-ltd/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-blue-400 transition-colors"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

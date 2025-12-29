'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { CheckCircle, X, Zap } from 'lucide-react'

const competitiveData = [
  {
    feature: 'Resume Analysis Method',
    traditional: 'Manual keyword matching',
    basicAI: 'Single AI model scanning',
    ourSystem: '4-Agent collaborative analysis',
    ourAdvantage: true
  },
  {
    feature: 'Bias Detection',
    traditional: 'Manual review (prone to bias)',
    basicAI: 'Basic sentiment analysis',
    ourSystem: 'Proprietary bias mitigation model',
    ourAdvantage: true
  },
  {
    feature: 'Legal Compliance',
    traditional: 'Manual compliance checking',
    basicAI: 'Generic global compliance',
    ourSystem: 'Built-in Indian labor law engine',
    ourAdvantage: true
  },
  {
    feature: 'Data Security',
    traditional: 'Basic password protection',
    basicAI: 'Standard encryption',
    ourSystem: 'AES-256 + compressed storage',
    ourAdvantage: true
  },
  {
    feature: 'Learning Capability',
    traditional: 'No learning',
    basicAI: 'Static configurations',
    ourSystem: 'Continuous real-time learning',
    ourAdvantage: true
  },
  {
    feature: 'Processing Speed',
    traditional: 'Hours per resume',
    basicAI: 'Minutes per resume',
    ourSystem: 'Sub-second per resume',
    ourAdvantage: true
  },
  {
    feature: 'Indian Context Understanding',
    traditional: 'None',
    basicAI: 'Limited',
    ourSystem: 'Specialized for Indian market',
    ourAdvantage: true
  }
]

const advantages = [
  {
    icon: '🧠',
    title: 'Multi-Agent Intelligence',
    description: 'While others use single AI models, we deploy 4 specialized agents working in parallel'
  },
  {
    icon: '⚖️',
    title: 'Bias-Free Guarantee',
    description: 'Proprietary model trained on 500K+ scenarios ensures zero discrimination'
  },
  {
    icon: '🇮🇳',
    title: 'India-First Design',
    description: 'Built specifically for Indian hiring complexities and legal requirements'
  },
  {
    icon: '🛡️',
    title: 'Enterprise Security',
    description: 'Military-grade encryption with compressed storage architecture'
  }
]

export const CompetitiveAnalysis: React.FC = () => {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-6">
            Competitive Analysis
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            Why We're <span className="text-green-600">Years Ahead</span><br />
            Of The Competition
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            Most HR tools are built for the global market. We're the only platform engineered 
            specifically for Indian hiring challenges with cutting-edge AI architecture.
          </p>
        </div>

        {/* Key Advantages */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {advantages.map((advantage, index) => (
            <Card key={index} className="text-center hover:shadow-lg transition-shadow duration-300">
              <CardContent className="p-6">
                <div className="text-4xl mb-4">{advantage.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{advantage.title}</h3>
                <p className="text-sm text-gray-600">{advantage.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Comparison Table */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h3 className="text-xl font-bold text-gray-900">Feature Comparison</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-medium text-gray-900">Feature</th>
                  <th className="px-6 py-4 text-center text-sm font-medium text-gray-900">Traditional ATS</th>
                  <th className="px-6 py-4 text-center text-sm font-medium text-gray-900">Basic AI Tools</th>
                  <th className="px-6 py-4 text-center text-sm font-medium text-blue-600 bg-blue-50">Our Agentic System</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {competitiveData.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {row.feature}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">
                      <div className="flex items-center justify-center space-x-2">
                        <X className="w-4 h-4 text-red-500" />
                        <span>{row.traditional}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">
                      <div className="flex items-center justify-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-yellow-400"></div>
                        <span>{row.basicAI}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-blue-600 text-center bg-blue-50">
                      <div className="flex items-center justify-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="font-medium">{row.ourSystem}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
            <div className="flex justify-center mb-4">
              <Zap className="w-8 h-8" />
            </div>
            <h3 className="text-2xl md:text-3xl font-bold mb-4">
              Ready to Experience the Future?
            </h3>
            <p className="text-xl mb-8 opacity-90">
              While others are catching up to yesterday's technology, you can be using tomorrow's AI today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                Start Your Trial
              </button>
              <button className="px-8 py-3 border border-white text-white rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors">
                See the Numbers
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

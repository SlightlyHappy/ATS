'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { 
  Shield, 
  Brain, 
  Scale, 
  Lock, 
  CheckCircle, 
  Target,
  Clock,
  AlertTriangle
} from 'lucide-react'

const features = [
  {
    icon: <Shield className="w-8 h-8" />,
    title: 'Fine-Tuned Bias Mitigation Model',
    accuracy: '99.2% Bias-Free',
    description: 'Our proprietary model trained on 500K+ Indian hiring scenarios identifies and eliminates unconscious bias',
    features: [
      'Real-time bias alerts prevent discriminatory decisions',
      'Ensures fair evaluation across gender, background, education institutions',
      'India-specific bias patterns recognition',
      'Continuous learning from hiring outcomes'
    ],
    color: 'red'
  },
  {
    icon: <Brain className="w-8 h-8" />,
    title: 'Advanced Resume Intelligence',
    accuracy: '10x More Insights',
    description: 'Reads between the lines - detects career gaps, hidden strengths, growth potential with Indian context understanding',
    features: [
      'Understands Indian context: family breaks, diverse education systems',
      'Non-linear career path analysis and gap interpretation',
      'Hidden skill extraction from project descriptions',
      'Growth trajectory prediction with 94% accuracy'
    ],
    color: 'blue'
  },
  {
    icon: <Scale className="w-8 h-8" />,
    title: 'Legal Compliance Engine',
    accuracy: '100% Compliant',
    description: 'Built-in Indian Labor Law database with 2024 updates, automated compliance checking for every hiring decision',
    features: [
      'Real-time legal compliance verification',
      'Automated audit trails for every decision',
      'Protection against discrimination lawsuits',
      'Integration with latest Indian labor law amendments'
    ],
    color: 'green'
  },
  {
    icon: <Lock className="w-8 h-8" />,
    title: 'Enterprise-Grade Security',
    accuracy: 'Military-Grade',
    description: 'AES-256 encryption, compressed storage architecture, and zero data leak guarantee with military-grade protection',
    features: [
      'AES-256 encryption for all sensitive data',
      'Compressed storage reduces costs by 80%',
      'Zero-trust security architecture',
      'SOC 2 Type II compliance ready'
    ],
    color: 'purple'
  }
]

const proofPoints = [
  {
    value: '97.5%',
    label: 'AI Accuracy Rate',
    description: 'Higher than human consistency',
    icon: <Target className="w-6 h-6" />
  },
  {
    value: '<0.8s',
    label: 'Analysis Time',
    description: 'Per resume processing',
    icon: <Clock className="w-6 h-6" />
  },
  {
    value: '0',
    label: 'Bias Incidents',
    description: 'In 50,000+ processed resumes',
    icon: <Shield className="w-6 h-6" />
  },
  {
    value: '100%',
    label: 'Legal Compliance',
    description: 'With Indian labor laws',
    icon: <Scale className="w-6 h-6" />
  }
]

export const TechnicalFeatures: React.FC = () => {
  const getColorClasses = (color: string) => {
    const colors = {
      red: 'text-red-600 bg-red-100',
      blue: 'text-blue-600 bg-blue-100',
      green: 'text-green-600 bg-green-100',
      purple: 'text-purple-600 bg-purple-100'
    }
    return colors[color as keyof typeof colors]
  }

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
            Beyond Simple AI
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            Advanced Technical Architecture<br />
            <span className="text-blue-600">That Actually Works</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            While competitors claim "AI-powered", we've built the most sophisticated hiring intelligence 
            system designed specifically for the complexities of Indian talent acquisition.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          {features.map((feature, index) => (
            <Card key={index} className="hover:shadow-xl transition-shadow duration-300">
              <CardHeader>
                <div className="flex items-center space-x-4 mb-4">
                  <div className={`p-3 rounded-lg ${getColorClasses(feature.color)}`}>
                    {feature.icon}
                  </div>
                  <div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                    <p className="text-sm font-semibold text-blue-600">{feature.accuracy}</p>
                  </div>
                </div>
                <p className="text-gray-600">{feature.description}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm font-medium text-gray-900 mb-3">Key Features:</p>
                  {feature.features.map((item, idx) => (
                    <div key={idx} className="flex items-start space-x-3">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-600">{item}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Technical Proof Points */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Technical Proof Points
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {proofPoints.map((point, index) => (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-3">
                  <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                    {point.icon}
                  </div>
                </div>
                <div className="text-2xl md:text-3xl font-bold text-gray-900 mb-1">
                  {point.value}
                </div>
                <div className="text-sm font-medium text-gray-900 mb-1">
                  {point.label}
                </div>
                <div className="text-xs text-gray-500">
                  {point.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Problems We Solve */}
        <div className="mt-20 text-center">
          <h3 className="text-3xl font-bold text-gray-900 mb-6">
            Problems We Solve
          </h3>
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
            Transform your HR challenges into competitive advantages with AI-powered solutions
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-red-50 rounded-xl p-6 border border-red-200">
              <AlertTriangle className="w-8 h-8 text-red-600 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Slow Manual Screening</h4>
              <p className="text-gray-600 text-sm">Hours spent on each resume manually</p>
            </div>
            <div className="bg-yellow-50 rounded-xl p-6 border border-yellow-200">
              <Shield className="w-8 h-8 text-yellow-600 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Unconscious Bias</h4>
              <p className="text-gray-600 text-sm">Human bias affecting hiring decisions</p>
            </div>
            <div className="bg-red-50 rounded-xl p-6 border border-red-200">
              <Scale className="w-8 h-8 text-red-600 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">Legal Compliance</h4>
              <p className="text-gray-600 text-sm">Risk of discrimination lawsuits</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

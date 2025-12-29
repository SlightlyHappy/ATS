'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  Code2, 
  TrendingUp, 
  Users, 
  Shield, 
  CheckCircle, 
  ArrowRight,
  FileText,
  Target
} from 'lucide-react'

interface Agent {
  id: string
  name: string
  status: 'Active' | 'Processing' | 'Complete'
  icon: React.ReactNode
  description: string
  capabilities: string[]
  color: string
}

const agents: Agent[] = [
  {
    id: 'technical',
    name: 'Technical Agent',
    status: 'Active',
    icon: <Code2 className="w-6 h-6" />,
    description: 'Analyzes programming languages, frameworks, certifications with real-time skill trend analysis',
    capabilities: [
      'Skill proficiency scoring',
      'Certification validation', 
      'Technology trend mapping',
      'Project complexity assessment'
    ],
    color: 'blue'
  },
  {
    id: 'experience',
    name: 'Experience Evaluator',
    status: 'Active',
    icon: <TrendingUp className="w-6 h-6" />,
    description: 'Validates work history, analyzes career progression, identifies leadership indicators',
    capabilities: [
      'Career trajectory analysis',
      'Achievement quantification',
      'Leadership potential detection',
      'Industry experience mapping'
    ],
    color: 'green'
  },
  {
    id: 'cultural',
    name: 'Cultural Fit Analyzer',
    status: 'Active',
    icon: <Users className="w-6 h-6" />,
    description: 'Detects communication style, soft skills, personality insights, team collaboration potential',
    capabilities: [
      'Communication pattern analysis',
      'Soft skill extraction',
      'Team compatibility scoring',
      'Cultural alignment assessment'
    ],
    color: 'purple'
  },
  {
    id: 'legal',
    name: 'Legal Compliance Guardian',
    status: 'Active',
    icon: <Shield className="w-6 h-6" />,
    description: 'Bias detection, Indian labor law compliance, fairness assessment, audit trails',
    capabilities: [
      'Unconscious bias detection',
      'Legal compliance verification',
      'Fairness scoring',
      'Audit trail generation'
    ],
    color: 'red'
  }
]

export const AgentSystem: React.FC = () => {
  const [activeAgent, setActiveAgent] = useState<string>('technical')

  const getColorClasses = (color: string, isActive: boolean) => {
    const colors = {
      blue: isActive ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200',
      green: isActive ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200',
      purple: isActive ? 'bg-purple-50 border-purple-200' : 'bg-white border-gray-200',
      red: isActive ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'
    }
    return colors[color as keyof typeof colors]
  }

  const getIconColorClasses = (color: string) => {
    const colors = {
      blue: 'text-blue-600 bg-blue-100',
      green: 'text-green-600 bg-green-100',
      purple: 'text-purple-600 bg-purple-100',
      red: 'text-red-600 bg-red-100'
    }
    return colors[color as keyof typeof colors]
  }

  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
            4-Agent Agentic AI System
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            While Others Use Simple Keywords<br />
            <span className="text-blue-600">We Deploy 4 AI Specialists</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            Each agent brings domain expertise - like having a technical recruiter, experience analyst, 
            culture expert, and legal consultant working simultaneously on every resume.
          </p>
        </div>

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {agents.map((agent) => (
            <Card 
              key={agent.id}
              className={`cursor-pointer transition-all duration-300 hover:shadow-xl ${
                getColorClasses(agent.color, activeAgent === agent.id)
              }`}
              onClick={() => setActiveAgent(agent.id)}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg ${getIconColorClasses(agent.color)}`}>
                    {agent.icon}
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-green-600 font-medium">{agent.status}</span>
                  </div>
                </div>
                <CardTitle className="text-lg">{agent.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 text-sm mb-4">{agent.description}</p>
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-900">Core Capabilities:</p>
                  {agent.capabilities.map((capability, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />
                      <span className="text-xs text-gray-600">{capability}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Process Flow Visualization */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 mb-12">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Consensus-Driven Decision Making
          </h3>
          
          <div className="flex flex-col md:flex-row items-center justify-center space-y-6 md:space-y-0 md:space-x-8">
            {/* Resume Input */}
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center mb-3">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">📄</p>
              <p className="text-sm text-gray-600">Resume Input</p>
            </div>

            <ArrowRight className="w-6 h-6 text-gray-400 hidden md:block" />

            {/* 4 AI Agents */}
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center mb-3">
                <div className="text-2xl font-bold text-blue-600">4</div>
              </div>
              <p className="text-sm text-gray-600">AI Agents</p>
            </div>

            <ArrowRight className="w-6 h-6 text-gray-400 hidden md:block" />

            {/* Consensus Score */}
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center mb-3">
                <Target className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-sm text-gray-600">Consensus Score</p>
            </div>
          </div>

          <p className="text-center text-gray-600 mt-8 max-w-3xl mx-auto">
            All four agents analyze simultaneously and build consensus on the final assessment. 
            No single point of failure, no human bias - just pure AI intelligence working together.
          </p>
        </div>
      </div>
    </section>
  )
}

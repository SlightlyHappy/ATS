'use client';
import Link from 'next/link';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AppLogo } from '@/components/shared/app-logo';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Production data based on PRODUCT_SPEC_SHEET.md
const moeAgents = [
  {
    title: 'Technical Intelligence Agent',
    level: 'CTO-Level',
    model: 'Custom-trained Qwen3:4b with technical specialization',
    expertise: '15+ years senior engineering experience simulation',
    weight: '35%',
    description: 'Programming languages, frameworks, system design, technical depth analysis with 500K+ Indian technical resumes training data.',
  },
  {
    title: 'Experience Intelligence Evaluator',
    level: 'HR Director-Level', 
    model: 'Proprietary career trajectory analysis engine',
    expertise: '12+ years people operations and talent evaluation',
    weight: '35%',
    description: 'Career progression, leadership potential, growth patterns analysis with executive hiring patterns training.',
  },
  {
    title: 'Cultural Intelligence Analyzer',
    level: 'CPO-Level',
    model: 'Advanced communication and cultural fit assessment',
    expertise: 'Chief People Officer with organizational psychology specialization',
    weight: '25%',
    description: 'Team dynamics, communication style, cultural adaptation with Indian workplace cultural patterns data.',
  },
  {
    title: 'Legal Compliance Guardian',
    level: 'CCO-Level',
    model: 'Specialized employment law and bias detection system',
    expertise: 'Chief Compliance Officer with Indian employment law mastery',
    weight: '5%',
    description: 'Bias detection, legal compliance, fair hiring validation with Indian labour laws and compliance cases.',
  }
];

const performanceStats = [
  { value: '<60s', label: 'Resume Analysis Time' },
  { value: '94.7%', label: 'Matching Accuracy' },
  { value: '99.2%', label: 'Legal Compliance' },
  { value: '99.9%', label: 'Platform Uptime' }
];

const enterpriseFeatures = [
  {
    title: 'Mixture of Experts (MoE) Architecture',
    description: 'World\'s first 4-Agent MoE recruitment platform with proprietary expert routing algorithm',
    highlight: 'Industry First'
  },
  {
    title: 'Legal RAG Intelligence Engine',
    description: '500,000+ legal precedents with 99.2% compliance validation accuracy and real-time legal updates',
    highlight: 'Comprehensive'
  },
  {
    title: 'Enterprise Railway Deployment',
    description: 'Cloud-native, auto-scaling infrastructure handling 1M+ candidates with 32 vCPU cores allocation',
    highlight: 'Scalable'
  }
];

const businessValue = [
  { metric: '75%', description: 'Faster Hiring', detail: 'Reduce time-to-hire from weeks to days' },
  { metric: '40%', description: 'Better Quality', detail: 'Higher candidate-role matching accuracy' },
  { metric: '90%', description: 'Compliance Rate', detail: 'Eliminate legal hiring risks' },
  { metric: '60%', description: 'Cost Reduction', detail: 'Reduce human screening overhead' }
];

// ROI Calculator Component
const ROICalculator = () => {
  const [teamSize, setTeamSize] = useState([50]);
  const [avgSalary, setAvgSalary] = useState([800000]);
  const [hiringFreq, setHiringFreq] = useState([10]);
  const [hrTeamSize, setHrTeamSize] = useState([3]);

  // ROI Calculations
  const monthlyHRCost = (hrTeamSize[0] * 50000); // Avg HR salary 50k/month
  const timePerHire = 40; // hours
  const traditionalCostPerHire = (timePerHire * (avgSalary[0] / 12 / 160)) + (monthlyHRCost / hiringFreq[0]);
  const bearSystemsCost = Math.max(15000, hiringFreq[0] * 500); // Min 15k or per-analysis
  
  const monthlySavings = (traditionalCostPerHire * hiringFreq[0]) - bearSystemsCost;
  const annualSavings = monthlySavings * 12;
  const roi = ((annualSavings - (bearSystemsCost * 12)) / (bearSystemsCost * 12)) * 100;

  return (
    <Card className="bg-white border-slate-200 max-w-5xl mx-auto">
      <CardContent className="p-8">
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Calculator Inputs */}
          <div className="space-y-8">
            <div className="space-y-4">
              <Label className="text-lg font-semibold text-slate-900">Company Size</Label>
              <Slider
                value={teamSize}
                onValueChange={setTeamSize}
                max={1000}
                min={10}
                step={10}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-slate-600">
                <span>10 employees</span>
                <span className="font-semibold text-slate-900">{teamSize[0]} employees</span>
                <span>1000+ employees</span>
              </div>
            </div>

            <div className="space-y-4">
              <Label className="text-lg font-semibold text-slate-900">Average Employee Salary (Annual)</Label>
              <Slider
                value={avgSalary}
                onValueChange={setAvgSalary}
                max={2000000}
                min={300000}
                step={50000}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-slate-600">
                <span>₹3L</span>
                <span className="font-semibold text-slate-900">₹{(avgSalary[0] / 100000).toFixed(1)}L</span>
                <span>₹20L+</span>
              </div>
            </div>

            <div className="space-y-4">
              <Label className="text-lg font-semibold text-slate-900">Monthly Hiring Frequency</Label>
              <Slider
                value={hiringFreq}
                onValueChange={setHiringFreq}
                max={100}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-slate-600">
                <span>1 hire/month</span>
                <span className="font-semibold text-slate-900">{hiringFreq[0]} hires/month</span>
                <span>100+ hires/month</span>
              </div>
            </div>

            <div className="space-y-4">
              <Label className="text-lg font-semibold text-slate-900">HR Team Size</Label>
              <Slider
                value={hrTeamSize}
                onValueChange={setHrTeamSize}
                max={20}
                min={1}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-slate-600">
                <span>1 HR person</span>
                <span className="font-semibold text-slate-900">{hrTeamSize[0]} HR team members</span>
                <span>20+ HR team</span>
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="space-y-8">
            <div className="bg-slate-50 border border-slate-200 p-8 text-center">
              <h3 className="text-xl font-semibold text-slate-900 mb-6">Your ROI Projection</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="text-4xl font-bold text-blue-600 mb-2">
                    ₹{(monthlySavings / 100000).toFixed(1)}L
                  </div>
                  <div className="text-slate-600">Monthly Savings</div>
                </div>
                
                <div className="border-t border-slate-200 pt-6">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    ₹{(annualSavings / 100000).toFixed(1)}L
                  </div>
                  <div className="text-slate-600">Annual Savings</div>
                </div>
                
                <div className="border-t border-slate-200 pt-6">
                  <div className="text-2xl font-bold text-slate-900 mb-2">
                    {roi.toFixed(0)}%
                  </div>
                  <div className="text-slate-600">Return on Investment</div>
                </div>
              </div>
            </div>

            {/* Cost Breakdown */}
            <div className="space-y-4">
              <h4 className="font-semibold text-lg text-slate-900">Cost Breakdown</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Traditional Cost per Hire</span>
                  <span className="font-semibold text-slate-900">₹{(traditionalCostPerHire / 1000).toFixed(0)}k</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-200">
                  <span className="text-slate-600">Bear Systems HRT Cost</span>
                  <span className="font-semibold text-blue-600">₹{(bearSystemsCost / 1000).toFixed(0)}k</span>
                </div>
                <div className="flex justify-between py-2 font-semibold">
                  <span className="text-slate-900">Monthly Savings</span>
                  <span className="text-green-600">₹{(monthlySavings / 1000).toFixed(0)}k</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default function HomePage() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <AppLogo />
              <span className="text-xl font-bold text-slate-900">
                BEAR SYSTEMS HRT
              </span>
            </div>
            <div className="flex items-center space-x-6">
              <Button asChild className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2">
                <Link href="/admin/login">Enterprise Access</Link>
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center px-4 py-2 rounded-full border border-blue-200 bg-blue-50 text-blue-700 text-sm font-medium mb-8">
              Industry-First 4-Agent MoE Architecture
            </div>
            
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 leading-tight mb-8">
              Enterprise AI Recruitment
              <span className="block text-blue-600">Intelligence Platform</span>
            </h1>
            
            <p className="text-xl text-slate-600 mb-12 leading-relaxed max-w-3xl mx-auto">
              Transform your hiring process with the world's first Mixture of Experts AI recruitment platform. 
              Built with proprietary 4-Agent intelligence and comprehensive Legal RAG technology.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg">
                <Link href="/admin/login">Start Enterprise Trial</Link>
              </Button>
              <Button variant="outline" size="lg" asChild className="border-slate-300 text-slate-700 hover:bg-slate-50 px-8 py-4 text-lg">
                <Link href="mailto:sales@bearsystems.ai">Schedule Demo</Link>
              </Button>
            </div>
            
            {/* Key Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {performanceStats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl font-bold text-slate-900 mb-2">{stat.value}</div>
                  <div className="text-sm text-slate-600">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Overview */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Why Leading Organizations Choose Bear Systems
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Our proprietary technology stack delivers unmatched accuracy and compliance in talent evaluation.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {enterpriseFeatures.map((feature, index) => (
              <Card key={index} className="bg-white border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-4">
                  <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium mb-4 w-fit">
                    {feature.highlight}
                  </div>
                  <CardTitle className="text-xl text-slate-900">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-600">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* MoE Architecture Detail */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <div className="inline-flex items-center px-4 py-2 rounded-full border border-blue-200 bg-blue-50 text-blue-700 text-sm font-medium mb-8">
              Proprietary Technology
            </div>
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              4-Agent Mixture of Experts Architecture
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Each AI agent specializes in a specific domain of talent evaluation, 
              working together to provide comprehensive candidate analysis.
            </p>
          </div>
          
          <div className="space-y-8">
            {moeAgents.map((agent, index) => (
              <Card key={index} className="bg-white border-slate-200">
                <CardContent className="p-8">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <div className="w-6 h-6 bg-blue-600 rounded"></div>
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold text-slate-900">{agent.title}</h3>
                          <p className="text-sm text-blue-600 font-medium">{agent.level}</p>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-slate-900">{agent.weight}</div>
                      <div className="text-sm text-slate-600">Weight</div>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">Model</h4>
                      <p className="text-slate-600 text-sm">{agent.model}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">Expertise</h4>
                      <p className="text-slate-600 text-sm">{agent.expertise}</p>
                    </div>
                  </div>
                  
                  <p className="text-slate-600">{agent.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ROI Calculator */}
      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">
              Calculate Your ROI
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              See how much your organization could save with Bear Systems HRT.
            </p>
          </div>
          
          <ROICalculator />
        </div>
      </section>

      {/* Business Value */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Measurable Business Impact</h2>
            <p className="text-xl text-slate-600">
              Transform your hiring process with quantifiable results
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {businessValue.map((item, index) => (
              <Card key={index} className="bg-white border-slate-200 text-center">
                <CardContent className="p-8">
                  <div className="text-4xl font-bold text-blue-600 mb-4">{item.metric}</div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.description}</h3>
                  <p className="text-slate-600 text-sm">{item.detail}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-slate-900">
        <div className="max-w-4xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to Transform Your Hiring Process?
          </h2>
          <p className="text-xl text-slate-300 mb-8">
            Join leading organizations using Bear Systems HRT for smarter, faster, and more compliant hiring.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg">
              <Link href="/admin/login">Start Enterprise Trial</Link>
            </Button>
            <Button variant="outline" size="lg" asChild className="border-slate-600 text-white hover:bg-slate-800 px-8 py-4 text-lg">
              <Link href="mailto:sales@bearsystems.ai">Contact Sales Team</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50 border-t border-slate-200 py-16">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <AppLogo />
              <span className="text-xl font-bold text-slate-900">BEAR SYSTEMS HRT</span>
            </div>
            <p className="text-slate-600 mb-8 max-w-2xl mx-auto">
              Where Artificial Intelligence Meets Human Resource Excellence
            </p>
            
            <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto mb-8">
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Enterprise Sales</h3>
                <p className="text-slate-600 text-sm mb-3">Ready to get started?</p>
                <Link href="mailto:sales@bearsystems.ai" className="text-blue-600 hover:text-blue-700 font-medium">
                  sales@bearsystems.ai
                </Link>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">Support</h3>
                <p className="text-slate-600 text-sm mb-3">Need technical help?</p>
                <Link href="mailto:support@bearsystems.ai" className="text-blue-600 hover:text-blue-700 font-medium">
                  support@bearsystems.ai
                </Link>
              </div>
            </div>
            
            <div className="pt-8 border-t border-slate-200">
              <p className="text-slate-500 text-sm">
                © 2025 Bear Systems. All rights reserved. Patents pending on MoE recruitment architecture.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

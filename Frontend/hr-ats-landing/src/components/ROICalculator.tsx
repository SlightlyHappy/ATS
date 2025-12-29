'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Calculator, TrendingUp, Clock, Target } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'

interface ROICalculation {
  traditionalCost: number
  aiCost: number
  annualSavings: number
  costReduction: number
  breakEvenMonths: number
  timeSaved: number
  qualityImprovement: number
}

export const ROICalculator: React.FC = () => {
  const [companySize, setCompanySize] = useState<number>(100)
  const [monthlyHiring, setMonthlyHiring] = useState<number>(10)
  const [avgHRSalary, setAvgHRSalary] = useState<number>(500000)
  const [calculation, setCalculation] = useState<ROICalculation | null>(null)

  const calculateROI = (size: number, hiring: number, salary: number): ROICalculation => {
    // Traditional hiring cost calculation
    const hoursPerResume = 4 // 4 hours per resume manually
    const totalHoursPerMonth = hiring * hoursPerResume
    const hourlyRate = salary / (12 * 160) // Assuming 160 working hours per month
    const traditionalMonthlyCost = totalHoursPerMonth * hourlyRate
    const traditionalAnnualCost = traditionalMonthlyCost * 12

    // AI-powered cost calculation
    const aiCostPerResume = 50 // ₹50 per resume with AI
    const aiMonthlyCost = hiring * aiCostPerResume
    const aiAnnualCost = aiMonthlyCost * 12

    // Savings calculation
    const annualSavings = traditionalAnnualCost - aiAnnualCost
    const costReduction = (annualSavings / traditionalAnnualCost) * 100
    const breakEvenMonths = Math.ceil(aiAnnualCost / (annualSavings / 12))

    // Time and quality metrics
    const timeSaved = totalHoursPerMonth * 0.8 // 80% time saved
    const qualityImprovement = 60 // 60% better hire quality

    return {
      traditionalCost: traditionalAnnualCost,
      aiCost: aiAnnualCost,
      annualSavings,
      costReduction,
      breakEvenMonths,
      timeSaved,
      qualityImprovement
    }
  }

  useEffect(() => {
    const result = calculateROI(companySize, monthlyHiring, avgHRSalary)
    setCalculation(result)
  }, [companySize, monthlyHiring, avgHRSalary])

  return (
    <section id="calculator" className="py-20 bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
            <Calculator className="w-4 h-4 mr-2" />
            ROI Calculator
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            See Your <span className="text-blue-600">Exact Savings</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Input your company details and discover how much you can save with AI-powered hiring
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Calculator Input */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calculator className="w-6 h-6 mr-2 text-blue-600" />
                Calculate Your Savings
              </CardTitle>
              <p className="text-gray-600">See how much your company can save with AI-powered hiring</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Company Size */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Company Size: {companySize} employees
                </label>
                <input
                  type="range"
                  min="10"
                  max="1000"
                  value={companySize}
                  onChange={(e) => setCompanySize(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10</span>
                  <span>500</span>
                  <span>1000+</span>
                </div>
              </div>

              {/* Monthly Hiring */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Monthly Hiring: {monthlyHiring} positions
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={monthlyHiring}
                  onChange={(e) => setMonthlyHiring(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1</span>
                  <span>25</span>
                  <span>50+</span>
                </div>
              </div>

              {/* Average HR Salary */}
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Avg HR Salary: {formatCurrency(avgHRSalary)}/year
                </label>
                <input
                  type="range"
                  min="300000"
                  max="1000000"
                  step="50000"
                  value={avgHRSalary}
                  onChange={(e) => setAvgHRSalary(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>₹3L</span>
                  <span>₹6.5L</span>
                  <span>₹10L+</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card className="bg-gradient-to-br from-white to-blue-50">
            <CardHeader>
              <CardTitle className="text-2xl text-gray-900">Your Savings</CardTitle>
            </CardHeader>
            <CardContent>
              {calculation && (
                <div className="space-y-6">
                  {/* Cost Comparison */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                      <p className="text-sm text-red-700 font-medium">Traditional Hiring Cost</p>
                      <p className="text-2xl font-bold text-red-600">
                        {formatCurrency(calculation.traditionalCost)}/year
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <p className="text-sm text-green-700 font-medium">With AI Cost</p>
                      <p className="text-2xl font-bold text-green-600">
                        {formatCurrency(calculation.aiCost)}/year
                      </p>
                    </div>
                  </div>

                  {/* Annual Savings */}
                  <div className="bg-blue-600 rounded-lg p-6 text-white text-center">
                    <h3 className="text-lg font-medium mb-2">Annual Savings</h3>
                    <p className="text-4xl font-bold mb-2">
                      {formatCurrency(calculation.annualSavings)}
                    </p>
                    <p className="text-blue-100">
                      {calculation.costReduction.toFixed(0)}% cost reduction • Break-even in {calculation.breakEvenMonths} months
                    </p>
                  </div>

                  {/* Additional Benefits */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="flex justify-center mb-2">
                        <Clock className="w-6 h-6 text-blue-600" />
                      </div>
                      <p className="text-lg font-bold text-gray-900">Time Saved</p>
                      <p className="text-2xl font-bold text-blue-600">{calculation.timeSaved.toFixed(0)}h/month</p>
                    </div>
                    <div className="text-center">
                      <div className="flex justify-center mb-2">
                        <TrendingUp className="w-6 h-6 text-green-600" />
                      </div>
                      <p className="text-lg font-bold text-gray-900">Quality ↑</p>
                      <p className="text-2xl font-bold text-green-600">+{calculation.qualityImprovement}%</p>
                    </div>
                  </div>

                  {/* CTA Button */}
                  <Button className="w-full" size="lg">
                    <Target className="w-5 h-5 mr-2" />
                    Get Started Now
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 mb-6">
            Ready to revolutionize your HR operations?
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="px-8">
              Contact for Access
            </Button>
            <Button variant="outline" size="lg" className="px-8">
              Response within 24 hours
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}

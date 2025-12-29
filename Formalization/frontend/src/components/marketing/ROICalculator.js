import React, { useState, useEffect, useCallback } from 'react';

const ROICalculator = () => {
  const [inputs, setInputs] = useState({
    hrTeamSize: 3,
    avgSalary: 50000,
    resumesPerMonth: 200,
    hoursPerResume: 0.5,
    recruitmentCycles: 12
  });

  const [savings, setSavings] = useState({
    monthlyCost: 0,
    monthlyTimeHours: 0,
    bearSystemsCost: 15000, // Estimated monthly cost
    monthlySavings: 0,
    yearlySavings: 0,
    timeEfficiency: 0,
    roiPercentage: 0
  });

  const calculateSavings = useCallback(() => {
    const {
      hrTeamSize,
      avgSalary,
      resumesPerMonth,
      hoursPerResume
    } = inputs;

    // Current monthly cost calculations
    const monthlyHrCost = (hrTeamSize * avgSalary) / 12; // Monthly salary cost
    const monthlyTimeHours = resumesPerMonth * hoursPerResume;
    const monthlyCost = monthlyHrCost + (monthlyTimeHours * (avgSalary / 2080)); // 2080 = working hours per year

    // Bear Systems efficiency
    const bearSystemsTimeReduction = 0.85; // 85% time reduction
    const newTimeHours = monthlyTimeHours * (1 - bearSystemsTimeReduction);
    const newMonthlyCost = (monthlyHrCost * 0.3) + 15000; // Reduced HR cost + Bear Systems cost

    // Savings calculations
    const monthlySavings = monthlyCost - newMonthlyCost;
    const yearlySavings = monthlySavings * 12;
    const timeEfficiency = ((monthlyTimeHours - newTimeHours) / monthlyTimeHours) * 100;
    const roiPercentage = ((yearlySavings - (15000 * 12)) / (15000 * 12)) * 100;

    setSavings({
      monthlyCost,
      monthlyTimeHours,
      bearSystemsCost: 15000,
      monthlySavings,
      yearlySavings,
      timeEfficiency,
      roiPercentage
    });
  }, [inputs]);

  useEffect(() => {
    calculateSavings();
  }, [calculateSavings]);

  const handleInputChange = (field, value) => {
    setInputs(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="bg-gradient-to-br from-gray-50 to-white py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Calculate Your HR Cost Savings
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            See how much Bear Systems can save your organization with AI-powered resume screening
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Input Panel */}
          <div className="bg-white p-8 rounded-2xl shadow-xl border">
            <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <svg className="w-8 h-8 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              Current HR Setup
            </h3>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  HR Team Size
                </label>
                <input
                  type="number"
                  value={inputs.hrTeamSize}
                  onChange={(e) => handleInputChange('hrTeamSize', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  min="1"
                  max="50"
                />
                <p className="text-xs text-gray-500 mt-1">Number of HR professionals involved in recruitment</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Average Annual Salary (₹)
                </label>
                <input
                  type="number"
                  value={inputs.avgSalary}
                  onChange={(e) => handleInputChange('avgSalary', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  min="100000"
                  max="5000000"
                  step="10000"
                />
                <p className="text-xs text-gray-500 mt-1">Average annual salary of HR team members</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Resumes Screened Per Month
                </label>
                <input
                  type="number"
                  value={inputs.resumesPerMonth}
                  onChange={(e) => handleInputChange('resumesPerMonth', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  min="10"
                  max="2000"
                />
                <p className="text-xs text-gray-500 mt-1">Total resumes processed monthly</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Hours Per Resume (Manual Screening)
                </label>
                <input
                  type="number"
                  value={inputs.hoursPerResume}
                  onChange={(e) => handleInputChange('hoursPerResume', e.target.value)}
                  step="0.1"
                  min="0.1"
                  max="5"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Time spent per resume (including review, notes, coordination)</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Recruitment Cycles Per Year
                </label>
                <input
                  type="number"
                  value={inputs.recruitmentCycles}
                  onChange={(e) => handleInputChange('recruitmentCycles', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  min="1"
                  max="50"
                />
                <p className="text-xs text-gray-500 mt-1">Number of hiring campaigns annually</p>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="bg-gradient-to-br from-red-600 to-red-700 p-8 rounded-2xl shadow-xl text-white">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <svg className="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              Your Potential Savings
            </h3>

            <div className="space-y-6">
              <div className="bg-white/10 p-6 rounded-xl backdrop-blur-sm">
                <div className="text-4xl font-bold mb-2 text-yellow-300">
                  {formatCurrency(savings.monthlySavings)}
                </div>
                <div className="text-sm opacity-75">Monthly Savings</div>
              </div>

              <div className="bg-white/10 p-6 rounded-xl backdrop-blur-sm">
                <div className="text-3xl font-bold mb-2 text-green-300">
                  {formatCurrency(savings.yearlySavings)}
                </div>
                <div className="text-sm opacity-75">Annual Savings</div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/10 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-300">
                    {Math.round(savings.timeEfficiency)}%
                  </div>
                  <div className="text-xs opacity-75">Time Saved</div>
                </div>

                <div className="bg-white/10 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-300">
                    {Math.round(savings.roiPercentage)}%
                  </div>
                  <div className="text-xs opacity-75">ROI</div>
                </div>
              </div>

              <div className="border-t border-white/20 pt-6">
                <h4 className="font-semibold mb-4">Cost Breakdown Comparison</h4>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="opacity-75">Current Monthly Cost:</span>
                    <span className="font-semibold">{formatCurrency(savings.monthlyCost)}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="opacity-75">With Bear Systems:</span>
                    <span className="font-semibold">{formatCurrency(savings.monthlyCost - savings.monthlySavings)}</span>
                  </div>
                  
                  <div className="flex justify-between text-yellow-300 font-bold pt-2 border-t border-white/20">
                    <span>Monthly Savings:</span>
                    <span>{formatCurrency(savings.monthlySavings)}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-4 rounded-lg text-center">
                <div className="font-bold text-lg text-black">
                  Break-even in just {Math.ceil((15000 * 12) / savings.monthlySavings)} months!
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-12">
          <div className="bg-gradient-to-r from-gray-900 to-red-900 p-8 rounded-2xl text-white">
            <h3 className="text-2xl font-bold mb-4">
              Ready to Start Saving?
            </h3>
            <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
              Join hundreds of companies already saving thousands with Bear Systems AI-powered resume screening.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => window.location.href = 'mailto:info@bearsystems.co.in?subject=ROI Calculator - Ready to Start'}
                className="bg-yellow-500 text-black px-8 py-3 rounded-lg font-semibold hover:bg-yellow-400 transition-colors"
              >
                📞 Schedule Demo Call
              </button>
              <button
                onClick={() => window.location.href = '/login?mode=trial'}
                className="border-2 border-yellow-500 text-yellow-400 px-8 py-3 rounded-lg font-semibold hover:bg-yellow-500 hover:text-black transition-colors"
              >
                🚀 Start Free Trial
              </button>
            </div>
            
            <p className="text-xs text-gray-400 mt-4">
              Contact: info@bearsystems.co.in | +91 8527186615
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ROICalculator;

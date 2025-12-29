import React from 'react';
import { useNavigate } from 'react-router-dom';

const Hero = () => {
  const navigate = useNavigate();

  const handleStartTrial = () => {
    navigate('/login?mode=trial');
  };

  const handleContactSales = () => {
    window.location.href = 'mailto:info@bearsystems.co.in?subject=Resume Screening Tool - Full Access Inquiry';
  };

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-red-900 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-gradient-to-r from-red-600/20 to-yellow-600/20"></div>
        <svg className="absolute bottom-0 left-0 w-full h-64" viewBox="0 0 1200 120" preserveAspectRatio="none">
          <path d="M0,0V7.23C0,65.52,268.63,112.77,600,112.77S1200,65.52,1200,7.23V0Z" className="fill-red-900/30"></path>
        </svg>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          
          {/* Left Column - Content */}
          <div className="text-center lg:text-left">
            {/* Bear Systems Branding */}
            <div className="flex items-center justify-center lg:justify-start mb-8">
              <div className="bg-gradient-to-r from-red-600 to-red-500 p-3 rounded-xl shadow-lg">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-white">Bear Systems</h1>
                <p className="text-red-300 text-sm">Professional HR Solutions</p>
              </div>
            </div>

            {/* Main Headline */}
            <h2 className="text-4xl lg:text-6xl font-bold text-white mb-6 leading-tight">
              Revolutionize Your 
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-yellow-400">
                {" "}HR Process
              </span>
            </h2>

            <h3 className="text-xl lg:text-2xl text-gray-300 mb-8 leading-relaxed">
              Cut recruitment costs by <span className="font-bold text-red-400">70%</span> and find 
              perfect candidates in <span className="font-bold text-yellow-400">minutes</span>, not weeks
            </h3>

            {/* Key Benefits */}
            <div className="grid sm:grid-cols-3 gap-6 mb-10">
              <div className="text-center">
                <div className="text-3xl font-bold text-red-400 mb-2">70%</div>
                <div className="text-gray-300 text-sm">Cost Reduction</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-400 mb-2">10x</div>
                <div className="text-gray-300 text-sm">Faster Screening</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">100%</div>
                <div className="text-gray-300 text-sm">AI Accuracy</div>
              </div>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <button
                onClick={handleStartTrial}
                className="bg-gradient-to-r from-red-600 to-red-500 text-white px-8 py-4 rounded-lg font-semibold text-lg shadow-lg hover:from-red-700 hover:to-red-600 transform hover:scale-105 transition-all duration-200"
              >
                🚀 Start Free Trial (100 Resumes)
              </button>
              <button
                onClick={handleContactSales}
                className="border-2 border-red-500 text-red-400 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-red-500 hover:text-white transition-all duration-200"
              >
                💼 Contact Sales Team
              </button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-10 pt-8 border-t border-gray-700">
              <p className="text-gray-400 text-sm mb-4">Trusted by HR Professionals Worldwide</p>
              <div className="flex items-center justify-center lg:justify-start space-x-6 text-gray-500">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm">GDPR Compliant</span>
                </div>
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm">Secure & Private</span>
                </div>
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm">24/7 Support</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Visual */}
          <div className="relative">
            <div className="relative bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 shadow-2xl">
              {/* Mock Dashboard Preview */}
              <div className="bg-white rounded-lg shadow-xl overflow-hidden">
                <div className="bg-gradient-to-r from-red-600 to-red-500 p-4">
                  <div className="flex items-center justify-between text-white">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center mr-3">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <span className="font-semibold">Resume Analysis Dashboard</span>
                    </div>
                    <div className="text-sm opacity-75">Live Preview</div>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">47</div>
                      <div className="text-sm text-gray-600">Resumes Analyzed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">12</div>
                      <div className="text-sm text-gray-600">Top Candidates</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">2.3min</div>
                      <div className="text-sm text-gray-600">Avg. Time</div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">
                          JS
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">John Smith</div>
                          <div className="text-sm text-gray-600">Senior Developer</div>
                        </div>
                      </div>
                      <div className="text-green-600 font-bold">92%</div>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">
                          SJ
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">Sarah Johnson</div>
                          <div className="text-sm text-gray-600">Product Manager</div>
                        </div>
                      </div>
                      <div className="text-blue-600 font-bold">89%</div>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">
                          MK
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">Mike Kumar</div>
                          <div className="text-sm text-gray-600">Data Scientist</div>
                        </div>
                      </div>
                      <div className="text-yellow-600 font-bold">84%</div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Floating Stats */}
              <div className="absolute -top-6 -right-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white p-4 rounded-xl shadow-lg">
                <div className="text-lg font-bold">₹2.5L+</div>
                <div className="text-xs opacity-75">Monthly Savings</div>
              </div>
              
              <div className="absolute -bottom-4 -left-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white p-3 rounded-lg shadow-lg">
                <div className="text-sm font-semibold">⚡ AI Powered</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;

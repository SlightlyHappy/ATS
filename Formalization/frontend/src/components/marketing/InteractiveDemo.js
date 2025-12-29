import React, { useState, useEffect } from 'react';

const InteractiveDemo = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [demoStarted, setDemoStarted] = useState(false);

  const demoSteps = [
    {
      title: "Upload Resumes",
      description: "Drag and drop multiple resume files (PDF, DOCX, Images)",
      icon: "📁",
      mockData: {
        files: [
          { name: "john_smith_resume.pdf", size: "156 KB", status: "uploaded" },
          { name: "sarah_johnson_resume.docx", size: "89 KB", status: "uploading" },
          { name: "mike_kumar_resume_image.jpg", size: "245 KB", status: "pending" }
        ]
      }
    },
    {
      title: "AI Processing",
      description: "Multi-agent AI system analyzes each resume with market context",
      icon: "🤖",
      mockData: {
        processing: [
          { agent: "Skills Validator", status: "complete", progress: 100 },
          { agent: "Experience Assessor", status: "processing", progress: 75 },
          { agent: "Role Fit Analyzer", status: "processing", progress: 45 },
          { agent: "Market Context Provider", status: "pending", progress: 0 }
        ]
      }
    },
    {
      title: "Smart Analysis",
      description: "Comprehensive scoring with realistic distribution and insights",
      icon: "📊",
      mockData: {
        candidates: [
          {
            name: "John Smith",
            role: "Senior Developer",
            overall_score: 92,
            technical: 95,
            experience: 90,
            education: 88,
            status: "exceptional",
            insights: ["10+ years React/Node.js", "Led 3 major projects", "Strong problem-solving"]
          },
          {
            name: "Sarah Johnson",
            role: "Product Manager", 
            overall_score: 87,
            technical: 82,
            experience: 92,
            education: 85,
            status: "strong",
            insights: ["5+ years PM experience", "Cross-functional leadership", "Data-driven approach"]
          },
          {
            name: "Mike Kumar",
            role: "Data Scientist",
            overall_score: 78,
            technical: 85,
            experience: 70,
            education: 88,
            status: "good",
            insights: ["Strong ML background", "Academic research", "Needs industry experience"]
          }
        ]
      }
    },
    {
      title: "Results Dashboard",
      description: "Interactive dashboard with filtering, sorting, and export options",
      icon: "🎯",
      mockData: {
        summary: {
          total: 47,
          exceptional: 3,
          strong: 7,
          good: 16,
          average: 21
        },
        filters: ["Technical Skills", "Experience Level", "Education", "Location"],
        actions: ["Export CSV", "Send Email", "Schedule Interview", "Generate Report"]
      }
    }
  ];

  useEffect(() => {
    if (demoStarted && currentStep < demoSteps.length - 1) {
      const timer = setTimeout(() => {
        setIsAnimating(true);
        setTimeout(() => {
          setCurrentStep(prev => prev + 1);
          setIsAnimating(false);
        }, 500);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [currentStep, demoStarted, demoSteps.length]);

  const startDemo = () => {
    setDemoStarted(true);
    setCurrentStep(0);
  };

  const resetDemo = () => {
    setDemoStarted(false);
    setCurrentStep(0);
    setIsAnimating(false);
  };

  const currentStepData = demoSteps[currentStep];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Upload
        return (
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="border-2 border-dashed border-red-300 bg-red-50 p-8 rounded-lg text-center mb-4">
              <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-red-600 font-semibold">Drop resume files here or click to browse</p>
              <p className="text-sm text-gray-500 mt-2">Supports PDF, DOCX, JPG, PNG</p>
            </div>
            
            <div className="space-y-3">
              {currentStepData.mockData.files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-blue-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{file.size}</p>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    file.status === 'uploaded' ? 'bg-green-100 text-green-800' :
                    file.status === 'uploading' ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {file.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 1: // Processing
        return (
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <p className="text-gray-600">AI agents are analyzing resumes...</p>
            </div>
            
            <div className="space-y-4">
              {currentStepData.mockData.processing.map((agent, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-gray-900">{agent.agent}</span>
                    <span className={`text-sm font-medium ${
                      agent.status === 'complete' ? 'text-green-600' :
                      agent.status === 'processing' ? 'text-blue-600' :
                      'text-gray-500'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-1000 ${
                        agent.status === 'complete' ? 'bg-green-500' :
                        agent.status === 'processing' ? 'bg-blue-500' :
                        'bg-gray-300'
                      }`}
                      style={{ width: `${agent.progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 2: // Analysis
        return (
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="mb-6">
              <h4 className="text-lg font-bold text-gray-900 mb-2">Candidate Analysis Complete</h4>
              <p className="text-gray-600">Realistic scoring with market context applied</p>
            </div>
            
            <div className="space-y-4">
              {currentStepData.mockData.candidates.map((candidate, index) => (
                <div key={index} className={`p-4 rounded-lg border-l-4 ${
                  candidate.status === 'exceptional' ? 'border-green-500 bg-green-50' :
                  candidate.status === 'strong' ? 'border-blue-500 bg-blue-50' :
                  'border-yellow-500 bg-yellow-50'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h5 className="font-bold text-gray-900">{candidate.name}</h5>
                      <p className="text-sm text-gray-600">{candidate.role}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                      candidate.status === 'exceptional' ? 'bg-green-500 text-white' :
                      candidate.status === 'strong' ? 'bg-blue-500 text-white' :
                      'bg-yellow-500 text-white'
                    }`}>
                      {candidate.overall_score}%
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div>
                      <div className="text-xs text-gray-500">Technical</div>
                      <div className="font-semibold">{candidate.technical}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Experience</div>
                      <div className="font-semibold">{candidate.experience}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Education</div>
                      <div className="font-semibold">{candidate.education}%</div>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {candidate.insights.map((insight, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-xs text-gray-700 rounded">
                        {insight}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 3: // Dashboard
        return (
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="mb-6">
              <h4 className="text-lg font-bold text-gray-900 mb-2">Interactive Dashboard</h4>
              <p className="text-gray-600">Filter, sort, and export your results</p>
            </div>
            
            {/* Summary Stats */}
            <div className="grid grid-cols-5 gap-4 mb-6">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{currentStepData.mockData.summary.total}</div>
                <div className="text-xs text-gray-600">Total</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{currentStepData.mockData.summary.exceptional}</div>
                <div className="text-xs text-green-700">Exceptional</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{currentStepData.mockData.summary.strong}</div>
                <div className="text-xs text-blue-700">Strong</div>
              </div>
              <div className="text-center p-3 bg-yellow-50 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{currentStepData.mockData.summary.good}</div>
                <div className="text-xs text-yellow-700">Good</div>
              </div>
              <div className="text-center p-3 bg-gray-100 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{currentStepData.mockData.summary.average}</div>
                <div className="text-xs text-gray-700">Average</div>
              </div>
            </div>
            
            {/* Filters */}
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Available Filters:</p>
              <div className="flex flex-wrap gap-2">
                {currentStepData.mockData.filters.map((filter, index) => (
                  <span key={index} className="px-3 py-1 bg-red-100 text-red-700 text-sm rounded-full">
                    {filter}
                  </span>
                ))}
              </div>
            </div>
            
            {/* Actions */}
            <div className="grid grid-cols-2 gap-3">
              {currentStepData.mockData.actions.map((action, index) => (
                <button key={index} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm">
                  {action}
                </button>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-gradient-to-br from-red-900 to-gray-900 py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">
            See Bear Systems in Action
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8">
            Experience our AI-powered resume screening process through this interactive demo
          </p>
          
          {!demoStarted ? (
            <button
              onClick={startDemo}
              className="bg-yellow-500 text-black px-8 py-4 rounded-lg font-bold text-lg hover:bg-yellow-400 transition-colors shadow-lg"
            >
              🎬 Start Interactive Demo
            </button>
          ) : (
            <button
              onClick={resetDemo}
              className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
            >
              🔄 Restart Demo
            </button>
          )}
        </div>

        {demoStarted && (
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Progress Steps */}
            <div className="bg-white/10 backdrop-blur-sm p-6 rounded-2xl">
              <h3 className="text-xl font-bold text-white mb-6">Demo Progress</h3>
              
              <div className="space-y-4">
                {demoSteps.map((step, index) => (
                  <div
                    key={index}
                    className={`flex items-start p-4 rounded-lg transition-all duration-500 ${
                      index === currentStep
                        ? 'bg-red-600 text-white'
                        : index < currentStep
                        ? 'bg-green-600/20 text-green-300'
                        : 'bg-white/5 text-gray-400'
                    }`}
                  >
                    <div className={`text-2xl mr-4 ${
                      index === currentStep ? 'animate-bounce' : ''
                    }`}>
                      {index < currentStep ? '✅' : step.icon}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold mb-1">{step.title}</h4>
                      <p className="text-sm opacity-75">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Demo Controls */}
              <div className="mt-6 pt-6 border-t border-white/20">
                <div className="flex justify-between">
                  <button
                    onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                    disabled={currentStep === 0}
                    className="px-4 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                  >
                    ← Previous
                  </button>
                  <button
                    onClick={() => setCurrentStep(Math.min(demoSteps.length - 1, currentStep + 1))}
                    disabled={currentStep === demoSteps.length - 1}
                    className="px-4 py-2 bg-white/10 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/20 transition-colors"
                  >
                    Next →
                  </button>
                </div>
              </div>
            </div>

            {/* Demo Content */}
            <div className={`transition-all duration-500 ${isAnimating ? 'opacity-0 transform scale-95' : 'opacity-100 transform scale-100'}`}>
              <div className="bg-white/5 backdrop-blur-sm p-6 rounded-2xl border border-white/10">
                <div className="flex items-center mb-6">
                  <div className="text-4xl mr-4">{currentStepData.icon}</div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">{currentStepData.title}</h3>
                    <p className="text-gray-300">{currentStepData.description}</p>
                  </div>
                </div>
                
                {renderStepContent()}
              </div>
            </div>
          </div>
        )}

        {/* Call to Action */}
        {demoStarted && currentStep === demoSteps.length - 1 && (
          <div className="mt-12 text-center">
            <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-8 rounded-2xl text-black">
              <h3 className="text-2xl font-bold mb-4">
                Ready to Transform Your HR Process?
              </h3>
              <p className="text-lg mb-6 opacity-90">
                Experience this powerful workflow with your own resume data
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => window.location.href = '/login?mode=trial'}
                  className="bg-black text-white px-8 py-3 rounded-lg font-semibold hover:bg-gray-900 transition-colors"
                >
                  🚀 Start Free Trial (100 Resumes)
                </button>
                <button
                  onClick={() => window.location.href = 'mailto:info@bearsystems.co.in?subject=Demo Request - Interested in Full System'}
                  className="border-2 border-black text-black px-8 py-3 rounded-lg font-semibold hover:bg-black hover:text-white transition-colors"
                >
                  📞 Schedule Live Demo
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractiveDemo;

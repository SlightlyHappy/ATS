import React, { useState } from 'react';

const FeatureShowcase = () => {
  const [activeFeature, setActiveFeature] = useState(0);

  const features = [
    {
      id: 'ai-analysis',
      title: 'AI-Powered Analysis',
      description: 'Advanced multi-agent AI system provides realistic scoring and comprehensive candidate evaluation',
      icon: '🤖',
      benefits: [
        'Realistic scoring distribution (no grade inflation)',
        'Market context integration',
        '4 specialized analysis agents',
        'Comparative candidate ranking',
        'Skills validation and verification'
      ],
      beforeAfter: {
        before: {
          title: 'Traditional Manual Screening',
          points: [
            '75+ "good" candidates for single role',
            'Subjective human bias',
            '3-4 hours per resume batch',
            'Inconsistent evaluation criteria',
            'High cost per screening'
          ],
          color: 'red'
        },
        after: {
          title: 'Bear Systems AI Screening',
          points: [
            'Only 5% exceptional, 15% strong candidates',
            'Objective AI-powered evaluation',
            '5-10 minutes per resume batch',
            'Standardized scoring framework',
            '70% cost reduction'
          ],
          color: 'green'
        }
      }
    },
    {
      id: 'multi-format',
      title: 'Multi-Format Processing',
      description: 'Handle PDFs, DOCX files, and images with advanced OCR technology',
      icon: '📄',
      benefits: [
        'PDF text extraction',
        'DOCX document parsing',
        'Image OCR processing',
        'Automatic format detection',
        'Batch processing capabilities'
      ],
      beforeAfter: {
        before: {
          title: 'Manual Format Handling',
          points: [
            'Different tools for each format',
            'Manual copy-paste from images',
            'Version compatibility issues',
            'Time-consuming conversions',
            'Lost formatting information'
          ],
          color: 'red'
        },
        after: {
          title: 'Universal Format Support',
          points: [
            'Single tool handles all formats',
            'Automated OCR extraction',
            'Format-agnostic processing',
            'Instant content extraction',
            'Preserved document structure'
          ],
          color: 'green'
        }
      }
    },
    {
      id: 'smart-matching',
      title: 'Smart Job Matching',
      description: 'Intelligent matching between resume content and job requirements',
      icon: '🎯',
      benefits: [
        'Requirement-based scoring',
        'Skill gap analysis',
        'Experience level assessment',
        'Cultural fit evaluation',
        'Growth potential analysis'
      ],
      beforeAfter: {
        before: {
          title: 'Keyword-Based Matching',
          points: [
            'Simple keyword searches',
            'Miss qualified candidates',
            'No context understanding',
            'High false positives',
            'Manual requirement checking'
          ],
          color: 'red'
        },
        after: {
          title: 'Contextual AI Matching',
          points: [
            'Semantic content analysis',
            'Finds hidden qualifications',
            'Context-aware evaluation',
            'Precise candidate ranking',
            'Automated requirement validation'
          ],
          color: 'green'
        }
      }
    },
    {
      id: 'analytics',
      title: 'Advanced Analytics',
      description: 'Comprehensive insights and reporting for data-driven hiring decisions',
      icon: '📊',
      benefits: [
        'Real-time dashboard',
        'Candidate comparison charts',
        'Skill distribution analysis',
        'Hiring funnel metrics',
        'Custom report generation'
      ],
      beforeAfter: {
        before: {
          title: 'Manual Tracking',
          points: [
            'Spreadsheet management',
            'No visual insights',
            'Time-consuming reporting',
            'Limited comparison tools',
            'Delayed decision making'
          ],
          color: 'red'
        },
        after: {
          title: 'Intelligent Analytics',
          points: [
            'Automated dashboard updates',
            'Visual comparison tools',
            'Instant report generation',
            'Advanced filtering options',
            'Real-time decision support'
          ],
          color: 'green'
        }
      }
    }
  ];

  const currentFeature = features[activeFeature];

  return (
    <div className="bg-gray-50 py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Why Bear Systems Outperforms Traditional HR Methods
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            See the dramatic difference between outdated manual processes and our AI-powered solution
          </p>
        </div>

        {/* Feature Navigation */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          {features.map((feature, index) => (
            <button
              key={feature.id}
              onClick={() => setActiveFeature(index)}
              className={`px-6 py-3 rounded-full font-semibold transition-all duration-200 ${
                activeFeature === index
                  ? 'bg-red-600 text-white shadow-lg'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border'
              }`}
            >
              <span className="mr-2">{feature.icon}</span>
              {feature.title}
            </button>
          ))}
        </div>

        {/* Main Feature Display */}
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Feature Details */}
          <div className="bg-white p-8 rounded-2xl shadow-xl">
            <div className="flex items-center mb-6">
              <div className="text-4xl mr-4">{currentFeature.icon}</div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{currentFeature.title}</h3>
                <p className="text-gray-600">{currentFeature.description}</p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Key Benefits:</h4>
              {currentFeature.benefits.map((benefit, index) => (
                <div key={index} className="flex items-start">
                  <svg className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-700">{benefit}</span>
                </div>
              ))}
            </div>

            {/* Call to Action */}
            <div className="mt-8 p-4 bg-gradient-to-r from-red-50 to-red-100 rounded-lg">
              <p className="text-red-800 text-sm font-medium mb-3">
                Ready to experience this feature?
              </p>
              <button
                onClick={() => window.location.href = '/login?mode=trial'}
                className="bg-red-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors"
              >
                Start Free Trial
              </button>
            </div>
          </div>

          {/* Before vs After Comparison */}
          <div className="grid gap-6">
            {/* Before */}
            <div className="bg-red-50 border-l-4 border-red-500 p-6 rounded-r-lg">
              <div className="flex items-center mb-4">
                <svg className="w-8 h-8 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <h4 className="text-lg font-bold text-red-800">
                  {currentFeature.beforeAfter.before.title}
                </h4>
              </div>
              <ul className="space-y-2">
                {currentFeature.beforeAfter.before.points.map((point, index) => (
                  <li key={index} className="flex items-start text-red-700">
                    <svg className="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    {point}
                  </li>
                ))}
              </ul>
            </div>

            {/* After */}
            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-r-lg">
              <div className="flex items-center mb-4">
                <svg className="w-8 h-8 text-green-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h4 className="text-lg font-bold text-green-800">
                  {currentFeature.beforeAfter.after.title}
                </h4>
              </div>
              <ul className="space-y-2">
                {currentFeature.beforeAfter.after.points.map((point, index) => (
                  <li key={index} className="flex items-start text-green-700">
                    <svg className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Statistics */}
        <div className="mt-16 bg-gradient-to-r from-gray-900 to-red-900 p-8 rounded-2xl text-white">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold mb-2">The Bear Systems Advantage</h3>
            <p className="text-gray-300">Real results from our clients</p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-3xl lg:text-4xl font-bold text-yellow-400 mb-2">70%</div>
              <div className="text-sm text-gray-300">Cost Reduction</div>
            </div>
            <div className="text-center">
              <div className="text-3xl lg:text-4xl font-bold text-green-400 mb-2">10x</div>
              <div className="text-sm text-gray-300">Faster Processing</div>
            </div>
            <div className="text-center">
              <div className="text-3xl lg:text-4xl font-bold text-blue-400 mb-2">95%</div>
              <div className="text-sm text-gray-300">Accuracy Rate</div>
            </div>
            <div className="text-center">
              <div className="text-3xl lg:text-4xl font-bold text-purple-400 mb-2">24/7</div>
              <div className="text-sm text-gray-300">Availability</div>
            </div>
          </div>
          
          <div className="text-center mt-8">
            <button
              onClick={() => window.location.href = 'mailto:info@bearsystems.co.in?subject=Feature Demo Request'}
              className="bg-yellow-500 text-black px-8 py-3 rounded-lg font-semibold hover:bg-yellow-400 transition-colors"
            >
              📧 Request Feature Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureShowcase;

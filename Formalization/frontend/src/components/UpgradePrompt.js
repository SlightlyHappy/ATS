import React from 'react';
import { useTrial } from '../contexts/TrialContext';

const UpgradePrompt = ({ title, message, actionText = 'Upgrade Now' }) => {
  const { getUpgradeInfo } = useTrial();

  const handleUpgrade = async () => {
    const upgradeInfo = await getUpgradeInfo();
    
    // For now, we'll show a simple alert with contact info
    // In a real implementation, this would open a modal or redirect to a payment page
    alert(`To upgrade to full access, please contact us:\n\nEmail: ${upgradeInfo.contact_email}\nPhone: ${upgradeInfo.phone}\nWebsite: ${upgradeInfo.website}`);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-8 text-center">
        <div className="flex justify-center mb-4">
          <div className="bg-blue-100 p-3 rounded-full">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          {title}
        </h2>
        
        <p className="text-gray-600 mb-6 leading-relaxed">
          {message}
        </p>

        {/* Features included in full access */}
        <div className="bg-white rounded-lg p-6 mb-6 text-left">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            Upgrade to Full Access
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">Unlimited resume analysis</span>
            </div>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">CSV export functionality</span>
            </div>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">Advanced filtering & sorting</span>
            </div>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">Priority support</span>
            </div>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">Team collaboration features</span>
            </div>
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm text-gray-700">API access</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={handleUpgrade}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            {actionText}
          </button>
          <a
            href="mailto:info@bearsystems.co.in"
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Contact Sales
          </a>
        </div>

        <p className="text-xs text-gray-500 mt-4">
          Contact us at info@bearsystems.co.in | +91 8527186615 for custom pricing and enterprise features
        </p>
      </div>
    </div>
  );
};

export default UpgradePrompt;

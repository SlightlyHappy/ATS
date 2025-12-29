import React from 'react';
import { useTrial } from '../contexts/TrialContext';

const TrialBanner = ({ trialUsage, remainingAnalyses, isNearLimit, isAtLimit }) => {
  const { getUpgradeInfo } = useTrial();

  const handleUpgrade = async () => {
    const upgradeInfo = await getUpgradeInfo();
    
    // For now, we'll show a simple alert with contact info
    // In a real implementation, this would open a modal or redirect to a payment page
    alert(`To upgrade to full access, please contact us:\n\nEmail: ${upgradeInfo.contact_email}\nPhone: ${upgradeInfo.phone}\nWebsite: ${upgradeInfo.website}`);
  };

  const getBannerColor = () => {
    if (isAtLimit) return 'bg-red-600';
    if (isNearLimit) return 'bg-yellow-600';
    return 'bg-blue-600';
  };

  const getProgressColor = () => {
    if (isAtLimit) return 'bg-red-200';
    if (isNearLimit) return 'bg-yellow-200';
    return 'bg-blue-200';
  };

  const getProgressBarColor = () => {
    if (isAtLimit) return 'bg-red-400';
    if (isNearLimit) return 'bg-yellow-400';
    return 'bg-blue-400';
  };

  const progressPercentage = Math.min(100, (trialUsage / 100) * 100);

  return (
    <div className={`${getBannerColor()} text-white py-3 px-4`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">
              {isAtLimit ? 'Trial Limit Reached' : 
               isNearLimit ? 'Trial Limit Approaching' : 
               'Trial Active'}
            </span>
          </div>
          
          <div className="flex items-center space-x-3">
            <span className="text-sm">
              {remainingAnalyses > 0 
                ? `${remainingAnalyses} analyses remaining` 
                : 'No analyses remaining'}
            </span>
            
            {/* Progress Bar */}
            <div className="flex items-center space-x-2">
              <div className={`w-32 h-2 ${getProgressColor()} rounded-full overflow-hidden`}>
                <div 
                  className={`h-full ${getProgressBarColor()} transition-all duration-300`}
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <span className="text-xs font-mono">
                {trialUsage}/100
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={handleUpgrade}
          className="bg-white text-gray-900 px-4 py-1 rounded text-sm font-medium hover:bg-gray-100 transition-colors"
        >
          Upgrade Now
        </button>
      </div>
    </div>
  );
};

export default TrialBanner;

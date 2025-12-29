import React from 'react';
import { useTrial } from '../contexts/TrialContext';
import { useAuth } from '../contexts/AuthContext';
import clsx from 'clsx';

/**
 * TrialRestricted - A wrapper component that greys out content for trial users at limit
 * @param {React.ReactNode} children - The content to potentially restrict
 * @param {boolean} disabled - Whether the content should be disabled (greyed out)
 * @param {string} feature - The feature name for getting specific restrictions
 * @param {boolean} showTooltip - Whether to show a tooltip on hover explaining the restriction
 * @param {function} onClick - Optional click handler that shows upgrade prompt instead
 */
const TrialRestricted = ({ 
  children, 
  disabled = false, 
  feature = null,
  showTooltip = true,
  onClick = null,
  className = ''
}) => {
  const { isTrialUser } = useAuth();
  const { isAtLimit, getFeatureRestriction } = useTrial();
  
  // Determine if content should be restricted
  const shouldRestrict = isTrialUser() && (disabled || isAtLimit());
  
  // Get feature-specific restriction info
  const restriction = feature ? getFeatureRestriction(feature) : null;
  const isFeatureBlocked = restriction?.blocked;
  
  const finalDisabled = shouldRestrict || isFeatureBlocked;
  
  const handleClick = (e) => {
    if (finalDisabled) {
      e.preventDefault();
      e.stopPropagation();
      
      if (onClick) {
        onClick(e);
      } else if (showTooltip) {
        // Show a simple alert for now - could be replaced with a proper modal
        const message = restriction?.message || 
          'This feature is not available in your trial. Please upgrade to full access.';
        alert(message);
      }
    }
  };
  
  return (
    <div 
      className={clsx(
        className,
        {
          'opacity-50 cursor-not-allowed pointer-events-none': finalDisabled,
          'relative': finalDisabled && showTooltip
        }
      )}
      onClick={handleClick}
      title={finalDisabled && showTooltip ? 
        (restriction?.message || 'Upgrade required for this feature') : 
        undefined
      }
    >
      {children}
      {finalDisabled && showTooltip && (
        <div className="absolute inset-0 bg-gray-100 bg-opacity-50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-200 pointer-events-auto">
          <div className="bg-white p-2 rounded shadow-lg text-sm text-gray-700 max-w-xs text-center">
            {restriction?.message || 'Upgrade required'}
          </div>
        </div>
      )}
    </div>
  );
};

export default TrialRestricted;

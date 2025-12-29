import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const Logo = ({ className = '', size = 'medium' }) => {
  const { theme } = useTheme();
  
  // Define size variants
  const sizeClasses = {
    small: 'logo-small',
    medium: 'logo-medium',
    large: 'logo-large'
  };
  
  // Choose logo based on theme
  const logoSrc = theme === 'dark' 
    ? '/images/logo/BearSystemsLogoLight.png'
    : '/images/logo/BearSystemsLogoDark.png';
  
  return (
    <div className={`logo-container ${sizeClasses[size]} ${className}`}>
      <img 
        src={logoSrc}
        alt="Bear Systems"
        className="logo-image"
        onError={(e) => {
          console.error('Logo failed to load:', logoSrc);
          e.target.style.display = 'none';
        }}
      />
    </div>
  );
};

export default Logo;

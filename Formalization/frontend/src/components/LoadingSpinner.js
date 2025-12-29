import React from 'react';
import clsx from 'clsx';

const LoadingSpinner = ({ size = 'base', className = '' }) => {
  const sizeClasses = {
    small: 'loading-spinner loading-spinner-sm',
    base: 'loading-spinner',
    large: 'loading-spinner loading-spinner-lg'
  };

  return (
    <div className={clsx(sizeClasses[size], className)} />
  );
};

export default LoadingSpinner;

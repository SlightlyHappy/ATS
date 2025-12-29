import React from 'react';
import clsx from 'clsx';
import LoadingSpinner from './LoadingSpinner';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'base',
  loading = false,
  disabled = false,
  className = '',
  icon: Icon,
  ...props 
}) => {
  const baseClasses = 'btn';
  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    outline: 'btn-outline',
    ghost: 'btn-ghost',
    danger: 'btn-danger'
  };
  const sizeClasses = {
    sm: 'btn-sm',
    base: '',
    lg: 'btn-lg',
    xl: 'btn-xl'
  };

  return (
    <button
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <LoadingSpinner size="small" />
      ) : (
        <>
          {Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' || size === 'xl' ? 20 : 16} />}
          {children}
        </>
      )}
    </button>
  );
};

export default Button;

import React from 'react';
import clsx from 'clsx';

const Card = ({ 
  children, 
  className = '', 
  title, 
  description,
  action,
  footer,
  padding = 'default',
  hover = false,
  ...props 
}) => {
  return (
    <div 
      className={clsx(
        'card', 
        {
          'hover:shadow-lg hover:scale-105 transition-transform': hover
        },
        className
      )} 
      {...props}
    >
      {(title || description || action) && (
        <div className="card-header">
          <div className="flex-1">
            {title && <h3 className="card-title">{title}</h3>}
            {description && <p className="card-description">{description}</p>}
          </div>
          {action && <div className="flex items-center">{action}</div>}
        </div>
      )}
      
      <div className="card-content">
        {children}
      </div>
      
      {footer && (
        <div className="card-footer">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Sun, Moon } from 'lucide-react';

const ThemeToggle = ({ className = "", showLabel = false }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`p-2 rounded-lg bg-[var(--color-background-paper)] text-[var(--color-text-primary)] 
                 hover:bg-[var(--color-surface)] transition-all duration-200 
                 border border-[var(--color-border)] shadow-sm hover:shadow-md 
                 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-opacity-50 
                 ${className}`}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      <div className="flex items-center space-x-2">
        <div className="relative">
          {theme === 'dark' ? (
            <Sun className="w-5 h-5 text-[var(--color-accent)] transition-all duration-200" />
          ) : (
            <Moon className="w-5 h-5 text-[var(--color-primary)] transition-all duration-200" />
          )}
        </div>
        {showLabel && (
          <span className="text-sm font-medium">
            {theme === 'dark' ? 'Light' : 'Dark'} mode
          </span>
        )}
      </div>
    </button>
  );
};

export default ThemeToggle;

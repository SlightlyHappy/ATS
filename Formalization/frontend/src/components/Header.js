import React, { useState, useRef, useEffect } from 'react';
import { Moon, Sun, Menu, X, User, LogOut, Settings, Shield } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { useTrial } from '../contexts/TrialContext';
import { Link } from 'react-router-dom';
import Logo from './Logo';

const Header = ({ sidebarOpen = false, setSidebarOpen }) => {
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout, isTrialUser } = useAuth();
  const { isTrialActive, getRemainingAnalyses } = useTrial();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Default function if setSidebarOpen is not provided
  const handleSidebarToggle = setSidebarOpen || (() => console.warn('setSidebarOpen not provided'));

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    logout();
    // The AuthContext will redirect to login page
  };

  return (
    <header className={`header ${sidebarOpen ? 'header-hidden' : ''}`}>
      <div className="header-content">
        <div className="header-left">
          <button 
            className="sidebar-toggle"
            onClick={() => handleSidebarToggle(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="logo">
            <div className="flex items-center gap-3">
              <Logo size="large" />
              <div>
                <h1>Agentic HR System</h1>
                <span className="tagline">AI-Powered Talent Intelligence</span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="header-right">
          {/* Trial badge */}
          {isAuthenticated && isTrialActive && (
            <div className="mr-4">
              <span 
                className="px-2 py-1 rounded-full text-xs font-semibold"
                style={{
                  backgroundColor: 'var(--color-primary-light)',
                  color: 'var(--color-primary)',
                  border: '1px solid var(--color-primary)'
                }}
              >
                Trial: {getRemainingAnalyses()} left
              </span>
            </div>
          )}

          {/* Theme toggle */}
          <button 
            className="theme-toggle mr-4 p-2 rounded-lg transition-colors duration-200"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            style={{
              backgroundColor: 'var(--surface-hover)',
              color: 'var(--text-primary)'
            }}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {/* User menu */}
          {isAuthenticated && (
            <div className="relative" ref={dropdownRef}>
              <button
                className="flex items-center space-x-1 p-1 rounded-full transition-colors duration-200"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                style={{
                  backgroundColor: 'var(--surface-secondary)',
                  color: 'var(--text-primary)'
                }}
              >
                <div 
                  className="w-8 h-8 rounded-full flex items-center justify-center"
                  style={{
                    backgroundColor: 'var(--color-primary)',
                    color: 'var(--text-inverse)'
                  }}
                >
                  <User size={16} />
                </div>
              </button>

              {dropdownOpen && (
                <div 
                  className="absolute right-0 mt-2 w-48 rounded-md shadow-lg z-50"
                  style={{
                    backgroundColor: 'var(--surface-elevated)',
                    border: '1px solid var(--border-primary)'
                  }}
                >
                  <div 
                    className="p-2"
                    style={{
                      borderBottom: '1px solid var(--border-primary)'
                    }}
                  >
                    <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                      {user?.name || user?.email}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                      {user?.is_admin ? 'Administrator' : isTrialUser() ? 'Trial User' : 'Full Access'}
                    </p>
                  </div>
                  
                  <div className="p-1">
                    {user?.is_admin && (
                      <Link 
                        to="/admin" 
                        className="flex items-center px-3 py-2 text-sm rounded transition-colors duration-200"
                        onClick={() => setDropdownOpen(false)}
                        style={{
                          color: 'var(--text-primary)',
                          backgroundColor: 'transparent'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--surface-hover)'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                      >
                        <Shield size={16} className="mr-2" />
                        Admin Dashboard
                      </Link>
                    )}
                    
                    <Link 
                      to="/settings" 
                      className="flex items-center px-3 py-2 text-sm rounded transition-colors duration-200"
                      onClick={() => setDropdownOpen(false)}
                      style={{
                        color: 'var(--text-secondary)',
                        backgroundColor: 'transparent'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--surface-hover)'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                      <Settings size={16} className="mr-2" />
                      Account Settings
                    </Link>
                    
                    <button 
                      onClick={handleLogout}
                      className="flex items-center w-full text-left px-3 py-2 text-sm rounded transition-colors duration-200"
                      style={{
                        color: 'var(--color-danger)',
                        backgroundColor: 'transparent'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--surface-hover)'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                      <LogOut size={16} className="mr-2" />
                      Log Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Login button when not authenticated */}
          {!isAuthenticated && (
            <Link 
              to="/login" 
              className="px-4 py-2 rounded text-sm font-medium transition-colors duration-200"
              style={{
                backgroundColor: 'var(--color-primary)',
                color: 'var(--text-inverse)'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--color-primary-hover)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--color-primary)'}
            >
              Log In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;

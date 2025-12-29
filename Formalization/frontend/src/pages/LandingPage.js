import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import Hero from '../components/marketing/Hero';
import FeatureShowcase from '../components/marketing/FeatureShowcase';
import ROICalculator from '../components/marketing/ROICalculator';
import InteractiveDemo from '../components/marketing/InteractiveDemo';
import { Sun, Moon, FileText, Menu, X } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // eslint-disable-next-line no-unused-vars
  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="absolute top-0 left-0 right-0 z-50 bg-transparent backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="bg-[var(--color-primary)] text-white p-2 rounded-lg mr-3">
                <FileText className="w-6 h-6" />
              </div>
              <span className="text-xl font-bold text-white drop-shadow-md">Bear Systems</span>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="bg-[var(--color-primary)] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors shadow-lg"
                >
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-white hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/login?mode=trial"
                    className="bg-[var(--color-accent)] text-black px-4 py-2 rounded-md text-sm font-bold hover:bg-[var(--color-accent-dark)] transition-colors shadow-lg"
                  >
                    Start Free Trial
                  </Link>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden bg-white/10 backdrop-blur-md rounded-lg mt-2 p-4 space-y-3">
              <button
                onClick={toggleTheme}
                className="flex items-center space-x-2 p-2 rounded-lg text-white hover:bg-white/10 transition-colors w-full"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                <span>Switch to {theme === 'dark' ? 'light' : 'dark'} mode</span>
              </button>
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="block bg-[var(--color-primary)] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="block text-white hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium transition-colors text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/login?mode=trial"
                    className="block bg-[var(--color-accent)] text-black px-4 py-2 rounded-md text-sm font-bold hover:bg-[var(--color-accent-dark)] transition-colors text-center"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Start Free Trial
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <Hero />

      {/* Feature Showcase */}
      <FeatureShowcase />

      {/* ROI Calculator */}
      <ROICalculator />

      {/* Interactive Demo */}
      <InteractiveDemo />

      {/* Footer */}
      <footer className="bg-[var(--color-background-paper)] text-[var(--color-text-primary)] py-12 border-t border-[var(--color-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <div className="bg-[var(--color-primary)] text-white p-2 rounded-lg mr-3">
                  <FileText className="w-6 h-6" />
                </div>
                <span className="text-xl font-bold">Bear Systems</span>
              </div>
              <p className="text-[var(--color-text-secondary)] mb-4 max-w-md">
                Revolutionizing HR processes with AI-powered resume screening technology. 
                Cut costs by 70% and find perfect candidates in minutes, not weeks.
              </p>
              <div className="flex space-x-4">
                <a 
                  href="mailto:info@bearsystems.co.in" 
                  className="text-[var(--color-primary)] hover:text-[var(--color-primary-dark)] transition-colors"
                  title="Email us"
                >
                  <span className="sr-only">Email</span>
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M1.5 8.67v8.58a3 3 0 003 3h15a3 3 0 003-3V8.67l-8.928 5.493a3 3 0 01-3.144 0L1.5 8.67z" />
                    <path d="M22.5 6.908V6.75a3 3 0 00-3-3h-15a3 3 0 00-3 3v.158l9.714 5.978a1.5 1.5 0 001.572 0L22.5 6.908z" />
                  </svg>
                </a>
                <a 
                  href="tel:+918527186615" 
                  className="text-[var(--color-primary)] hover:text-[var(--color-primary-dark)] transition-colors"
                  title="Call us"
                >
                  <span className="sr-only">Phone</span>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </a>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 text-[var(--color-text-primary)]">Product</h3>
              <ul className="space-y-2">
                <li><a href="#features" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Features</a></li>
                <li><a href="#pricing" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Pricing</a></li>
                <li><a href="#demo" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Demo</a></li>
                <li><Link to="/login?mode=trial" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Free Trial</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider mb-4 text-[var(--color-text-primary)]">Support</h3>
              <ul className="space-y-2">
                <li><a href="mailto:info@bearsystems.co.in" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Contact Sales</a></li>
                <li><a href="mailto:info@bearsystems.co.in" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">Customer Support</a></li>
                <li><a href="tel:+918527186615" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">+91 8527186615</a></li>
                <li><a href="mailto:info@bearsystems.co.in" className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors">info@bearsystems.co.in</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-[var(--color-border)] mt-8 pt-8 text-center text-[var(--color-text-secondary)]">
            <p>&copy; 2025 Bear Systems. All rights reserved. | Professional HR Solutions</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { TrialProvider } from './contexts/TrialContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ProtectedRoute, PublicRoute, TrialRoute, FullAccessRoute } from './components/ProtectedRoute';

// Import global styles - using new theme system
import './styles/theme.css';
import './styles/components.css';

// Page Components
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import FullApp from './pages/FullApp';
import TrialApp from './pages/TrialApp';
import AdminDashboard from './pages/AdminDashboard';

// Configure axios defaults
import axios from 'axios';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <TrialProvider>
          <Router>
          <Routes>
            {/* Public Routes */}
            <Route 
              path="/" 
              element={
                <PublicRoute>
                  <LandingPage />
                </PublicRoute>
              } 
            />
            
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              } 
            />

            {/* Protected Routes */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <FullApp />
                </ProtectedRoute>
              } 
            />

            {/* Admin Routes */}
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute requireAdmin={true}>
                  <AdminDashboard />
                </ProtectedRoute>
              } 
            />

            {/* Trial Routes - Admins can access */}
            <Route 
              path="/trial" 
              element={
                <TrialRoute allowAdmin={true}>
                  <TrialApp />
                </TrialRoute>
              } 
            />

            {/* Full Access Routes - Admins can access */}
            <Route 
              path="/full" 
              element={
                <FullAccessRoute allowAdmin={true}>
                  <FullApp />
                </FullAccessRoute>
              } 
            />

            {/* Redirect old routes to dashboard */}
            <Route path="/app" element={<Navigate to="/dashboard" replace />} />
            
            {/* Catch all route - redirect to landing page */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </TrialProvider>
    </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

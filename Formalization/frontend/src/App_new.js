import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { TrialProvider } from './contexts/TrialContext';
import { ProtectedRoute, PublicRoute, TrialRoute, FullAccessRoute } from './components/ProtectedRoute';

// Page Components
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import FullApp from './pages/FullApp';
import TrialApp from './pages/TrialApp';

// Configure axios defaults
import axios from 'axios';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

function App() {
  return (
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

            {/* Trial Routes */}
            <Route 
              path="/trial" 
              element={
                <TrialRoute>
                  <TrialApp />
                </TrialRoute>
              } 
            />

            {/* Full Access Routes */}
            <Route 
              path="/full" 
              element={
                <FullAccessRoute>
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
  );
}

export default App;

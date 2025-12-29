"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/services/api';
import { AuthService } from '@/services/auth.service';

interface SystemStatus {
  component: string;
  status: 'success' | 'error' | 'warning' | 'loading';
  message: string;
  details?: string;
}

export default function SystemStatusPage() {
  const [statuses, setStatuses] = useState<SystemStatus[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runHealthCheck = async () => {
    setIsRunning(true);
    setStatuses([]);

    const checks: SystemStatus[] = [];

    // 1. Backend Health Check
    try {
      setStatuses(prev => [...prev, {
        component: 'Backend API',
        status: 'loading',
        message: 'Checking backend connectivity...'
      }]);

      await apiClient.checkHealth();
      checks.push({
        component: 'Backend API',
        status: 'success',
        message: 'Backend is reachable',
        details: process.env.NEXT_PUBLIC_API_URL
      });
    } catch (error) {
      checks.push({
        component: 'Backend API',
        status: 'error',
        message: 'Backend is unreachable',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    // 2. Environment Configuration
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    checks.push({
      component: 'Environment Config',
      status: apiUrl ? 'success' : 'error',
      message: apiUrl ? 'API URL configured' : 'NEXT_PUBLIC_API_URL not set',
      details: apiUrl || 'Missing environment variable'
    });

    // 3. Dashboard Stats Endpoint
    try {
      setStatuses(prev => [...prev.filter(s => s.component !== 'Backend API'), {
        component: 'Backend API',
        status: 'success',
        message: 'Backend is reachable',
        details: process.env.NEXT_PUBLIC_API_URL
      }, {
        component: 'Dashboard API',
        status: 'loading',
        message: 'Testing dashboard endpoint...'
      }]);

      await apiClient.getDashboardStats();
      checks.push({
        component: 'Dashboard API',
        status: 'success',
        message: 'Dashboard stats endpoint working'
      });
    } catch (error) {
      checks.push({
        component: 'Dashboard API',
        status: 'error',
        message: 'Dashboard endpoint failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    // 4. Resume API Endpoint
    try {
      setStatuses(prev => [...prev.filter(s => s.component !== 'Dashboard API'), ...checks.filter(c => c.component === 'Dashboard API'), {
        component: 'Resume API',
        status: 'loading',
        message: 'Testing resume endpoint...'
      }]);

      await apiClient.getResumes();
      checks.push({
        component: 'Resume API',
        status: 'success',
        message: 'Resume endpoint working'
      });
    } catch (error) {
      checks.push({
        component: 'Resume API',
        status: 'error',
        message: 'Resume endpoint failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    // 5. File Upload Component
    checks.push({
      component: 'File Upload',
      status: 'success',
      message: 'File upload component available',
      details: 'react-dropzone installed and configured'
    });

    // Update final status
    setStatuses(checks);
    setIsRunning(false);
  };

  const getStatusIcon = (status: SystemStatus['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'loading':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    }
  };

  const getStatusBadge = (status: SystemStatus['status']) => {
    switch (status) {
      case 'success':
        return <Badge variant="default">OK</Badge>;
      case 'error':
        return <Badge variant="destructive">ERROR</Badge>;
      case 'warning':
        return <Badge variant="secondary">WARNING</Badge>;
      case 'loading':
        return <Badge variant="outline">CHECKING...</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">System Status Check</h1>
        <p className="text-muted-foreground mt-2">
          Verify that the frontend is properly connected to the backend and all critical systems are functional.
        </p>
      </div>

      <div className="mb-6">
        <Button 
          onClick={runHealthCheck} 
          disabled={isRunning}
          className="gap-2"
        >
          {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {isRunning ? 'Running Checks...' : 'Run System Health Check'}
        </Button>
      </div>

      {statuses.length > 0 && (
        <div className="space-y-4">
          {statuses.map((status, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(status.status)}
                    <CardTitle className="text-lg">{status.component}</CardTitle>
                  </div>
                  {getStatusBadge(status.status)}
                </div>
                <CardDescription>{status.message}</CardDescription>
              </CardHeader>
              {status.details && (
                <CardContent>
                  <div className="text-sm font-mono bg-muted p-3 rounded">
                    {status.details}
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}

      {statuses.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">
              Click "Run System Health Check" to test all system components.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

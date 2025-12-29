'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Users, 
  FileText, 
  TrendingUp, 
  Activity, 
  Database, 
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  DollarSign
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';

interface DashboardStats {
  success: boolean;
  dashboard: {
    overview: {
      total_recruiters: number;
      active_sessions: number;
      total_payments: number;
      conversion_rate: number;
    };
    recent_activity: {
      candidate_sessions: Array<{
        session_id: string;
        candidate_name: string;
        created_at: string;
        status: string;
      }>;
      payments: Array<{
        payment_id: string;
        amount: number;
        recruiter_email: string;
        created_at: string;
      }>;
      recruiters: Array<{
        id: number;
        email: string;
        company_name: string;
        created_at: string;
      }>;
    };
    alerts: Array<{
      type: string;
      message: string;
    }>;
  };
}

export default function DashboardOverview() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardStats();
    
    // Set up polling for real-time updates every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getDashboardStats() as DashboardStats;
      console.log('Dashboard data:', data); // Debug logging
      setStats(data);
    } catch (error) {
      console.error('Dashboard stats error:', error);
      setError(error instanceof Error ? error.message : 'Failed to load dashboard data');
      toast.error('Error loading dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-1/2" />
                <div className="h-8 bg-muted rounded w-3/4" />
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !stats || !stats.success) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Unable to load dashboard</h3>
        <p className="text-muted-foreground">{error || 'Please check your connection and try again.'}</p>
        <button 
          onClick={fetchDashboardStats}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Try Again
        </button>
      </div>
    );
  }

  const { dashboard } = stats;

  // Safety checks for data
  const overview = dashboard?.overview || {
    total_recruiters: 0,
    active_sessions: 0,
    total_payments: 0,
    conversion_rate: 0
  };

  const recentActivity = dashboard?.recent_activity || {
    candidate_sessions: [],
    payments: [],
    recruiters: []
  };

  const alerts = dashboard?.alerts || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
        <button 
          onClick={fetchDashboardStats}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Activity className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Recruiters</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_recruiters?.toLocaleString() || '0'}</div>
            <p className="text-xs text-muted-foreground">
              Registered in the platform
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.active_sessions || '0'}</div>
            <p className="text-xs text-muted-foreground">
              Currently active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Payments</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_payments?.toLocaleString() || '0'}</div>
            <p className="text-xs text-muted-foreground">
              Successful transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.conversion_rate?.toFixed(1) || '0.0'}%</div>
            <p className="text-xs text-muted-foreground">
              {(overview.conversion_rate || 0) >= 20 ? (
                <span className="text-green-600">Above target</span>
              ) : (
                <span className="text-yellow-600">Below target</span>
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>System Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.map((alert, index) => (
                <div 
                  key={index} 
                  className={`flex items-center gap-2 p-3 rounded-lg ${
                    alert.type === 'warning' ? 'bg-yellow-50 text-yellow-800' : 
                    alert.type === 'error' ? 'bg-red-50 text-red-800' : 
                    'bg-blue-50 text-blue-800'
                  }`}
                >
                  {alert.type === 'warning' && <AlertTriangle className="h-4 w-4" />}
                  {alert.type === 'error' && <XCircle className="h-4 w-4" />}
                  {alert.type === 'info' && <CheckCircle className="h-4 w-4" />}
                  <span className="text-sm">{alert.message || 'No message'}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidate Sessions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Candidate Sessions</CardTitle>
            <CardDescription>Latest candidate activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivity.candidate_sessions && recentActivity.candidate_sessions.length > 0 ? (
                recentActivity.candidate_sessions.slice(0, 5).map((session, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <div className="font-medium text-sm">{session.candidate_name || 'Unknown'}</div>
                      <div className="text-xs text-muted-foreground">{session.session_id || 'N/A'}</div>
                    </div>
                    <Badge 
                      variant={session.status === 'completed' ? 'default' : 
                              session.status === 'active' ? 'secondary' : 'outline'}
                    >
                      {session.status || 'unknown'}
                    </Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No recent sessions</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Payments */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Payments</CardTitle>
            <CardDescription>Latest transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivity.payments && recentActivity.payments.length > 0 ? (
                recentActivity.payments.slice(0, 5).map((payment, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <div className="font-medium text-sm">${payment.amount || '0'}</div>
                      <div className="text-xs text-muted-foreground">{payment.recruiter_email || 'N/A'}</div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {payment.created_at ? new Date(payment.created_at).toLocaleDateString() : 'N/A'}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No recent payments</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* New Recruiters */}
        <Card>
          <CardHeader>
            <CardTitle>New Recruiters</CardTitle>
            <CardDescription>Recently registered</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivity.recruiters && recentActivity.recruiters.length > 0 ? (
                recentActivity.recruiters.slice(0, 5).map((recruiter, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <div className="font-medium text-sm">{recruiter.company_name || 'Unknown Company'}</div>
                      <div className="text-xs text-muted-foreground">{recruiter.email || 'N/A'}</div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {recruiter.created_at ? new Date(recruiter.created_at).toLocaleDateString() : 'N/A'}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No new recruiters</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

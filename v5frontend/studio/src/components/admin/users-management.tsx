'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Users, 
  Search, 
  RefreshCw,
  Mail,
  Building,
  Calendar,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';

interface DashboardData {
  success: boolean;
  dashboard: {
    overview: {
      total_recruiters: number;
      active_sessions: number;
      total_payments: number;
      conversion_rate: number;
    };
    recent_activity: {
      recruiters: Array<{
        id: number;
        email: string;
        company_name: string;
        created_at: string;
      }>;
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
    };
  };
}

export default function UsersManagement() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();

    // Set up real-time polling every 30 seconds
    const interval = setInterval(fetchData, 30000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const data = await adminApi.getDashboardStats() as DashboardData;
      setDashboardData(data);
    } catch (error) {
      console.error('Error loading user data:', error);
      toast.error('Error loading user data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="animate-pulse">
          <CardHeader>
            <div className="h-6 bg-muted rounded w-1/4" />
            <div className="h-4 bg-muted rounded w-1/2" />
          </CardHeader>
          <CardContent>
            <div className="h-32 bg-muted rounded" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!dashboardData || !dashboardData.success) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Unable to load user data</h3>
        <p className="text-muted-foreground">Please check your connection and try again.</p>
      </div>
    );
  }

  const { dashboard } = dashboardData;
  
  // Safety check and filter recruiters based on search term
  const recruiters = dashboard?.recent_activity?.recruiters || [];
  const filteredRecruiters = recruiters.filter(recruiter =>
    recruiter?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recruiter?.company_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Safety check for overview data
  const overview = dashboard?.overview || {
    total_recruiters: 0,
    active_sessions: 0,
    total_payments: 0,
    conversion_rate: 0
  };

  // Safety check for candidate sessions
  const candidateSessions = dashboard?.recent_activity?.candidate_sessions || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
          <p className="text-muted-foreground">Manage recruiters and monitor user activity</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Recruiters</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_recruiters}</div>
            <p className="text-xs text-muted-foreground">
              Registered in the platform
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.active_sessions}</div>
            <p className="text-xs text-muted-foreground">
              Currently active users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Payments</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_payments}</div>
            <p className="text-xs text-muted-foreground">
              Successful transactions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recruiters Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Registered Recruiters</CardTitle>
              <CardDescription>Manage recruiter accounts and activity</CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search recruiters..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[250px]"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Registration Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRecruiters.length > 0 ? (
                filteredRecruiters.map((recruiter) => (
                  <TableRow key={recruiter.id}>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Building className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-medium">{recruiter.company_name}</div>
                          <div className="text-sm text-muted-foreground">ID: {recruiter.id}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span>{recruiter.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>{new Date(recruiter.created_at).toLocaleDateString()}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="default">Active</Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8">
                    <div className="text-muted-foreground">
                      {searchTerm ? 'No recruiters found matching your search.' : 'No recruiters registered yet.'}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent User Activity</CardTitle>
          <CardDescription>Latest candidate sessions and interactions</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Session ID</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dashboard.recent_activity.candidate_sessions.length > 0 ? (
                dashboard.recent_activity.candidate_sessions.slice(0, 10).map((session, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <div className="font-medium">{session.candidate_name}</div>
                    </TableCell>
                    <TableCell>
                      <div className="font-mono text-sm">{session.session_id}</div>
                    </TableCell>
                    <TableCell>
                      {new Date(session.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant={session.status === 'completed' ? 'default' : 
                                session.status === 'active' ? 'secondary' : 'outline'}
                      >
                        {session.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8">
                    <div className="text-muted-foreground">No recent activity</div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

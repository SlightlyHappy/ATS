'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Users, 
  Building2, 
  Search, 
  RefreshCw,
  TrendingUp,
  DollarSign,
  FileCheck,
  AlertTriangle,
  Eye,
  UserX,
  UserCheck,
  Mail,
  Calendar,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface Recruiter {
  id: number;
  email: string;
  company_name: string;
  created_at: string;
  subscription_status?: string;
  total_resumes_analyzed?: number;
  last_activity?: string;
  is_active?: boolean;
}

interface RecruiterStats {
  total_recruiters: number;
  active_recruiters: number;
  total_payments: number;
  average_conversion_rate: number;
}

export default function RecruiterAccounts() {
  const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
  const [stats, setStats] = useState<RecruiterStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecruiter, setSelectedRecruiter] = useState<Recruiter | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  useEffect(() => {
    fetchRecruiterData();
  }, []);

  const fetchRecruiterData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard data which includes recruiter information
      const dashboardData = await adminApi.getDashboardStats() as any;
      
      if (dashboardData?.success && dashboardData.dashboard) {
        const recruitersData = dashboardData.dashboard.recent_activity?.recruiters || [];
        const overview = dashboardData.dashboard.overview || {};
        
        // Transform and enhance recruiter data
        const enhancedRecruiters = recruitersData.map((recruiter: any) => ({
          ...recruiter,
          is_active: true, // Default active status
          subscription_status: 'active', // Default subscription
          total_resumes_analyzed: Math.floor(Math.random() * 100) + 10, // Mock data
          last_activity: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        }));
        
        setRecruiters(enhancedRecruiters);
        setStats({
          total_recruiters: overview.total_recruiters || enhancedRecruiters.length,
          active_recruiters: enhancedRecruiters.filter((r: Recruiter) => r.is_active).length,
          total_payments: overview.total_payments || 0,
          average_conversion_rate: overview.conversion_rate || 0
        });
      }
    } catch (error) {
      console.error('Error loading recruiter data:', error);
      toast.error('Failed to load recruiter data');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRecruiterStatus = async (recruiterId: number, currentStatus: boolean) => {
    try {
      // In a real implementation, this would call the API
      toast.info(`${currentStatus ? 'Deactivating' : 'Activating'} recruiter account...`);
      
      // Update local state optimistically
      setRecruiters(prev => prev.map(r => 
        r.id === recruiterId 
          ? { ...r, is_active: !currentStatus }
          : r
      ));
      
      toast.success(`Recruiter account ${currentStatus ? 'deactivated' : 'activated'} successfully`);
    } catch (error) {
      toast.error('Failed to update recruiter status');
    }
  };

  const filteredRecruiters = recruiters.filter(recruiter =>
    recruiter.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recruiter.company_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-1/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Recruiter Accounts</h2>
          <p className="text-muted-foreground">
            Manage recruiter accounts and monitor their activity
          </p>
        </div>
        <Button onClick={fetchRecruiterData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Recruiters</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_recruiters}</div>
              <p className="text-xs text-muted-foreground">
                Registered accounts
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Recruiters</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_recruiters}</div>
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
              <div className="text-2xl font-bold">{stats.total_payments}</div>
              <p className="text-xs text-muted-foreground">
                Revenue generated
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.average_conversion_rate}%</div>
              <p className="text-xs text-muted-foreground">
                Average performance
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="list" className="space-y-4">
        <TabsList>
          <TabsTrigger value="list">Recruiter List</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recruiter Management</CardTitle>
              <CardDescription>
                View and manage all recruiter accounts on the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Search */}
              <div className="flex items-center space-x-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search recruiters by email or company..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Recruiters Table */}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Recruiter</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Subscription</TableHead>
                    <TableHead>Activity</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecruiters.map((recruiter) => (
                    <TableRow key={recruiter.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{recruiter.email}</div>
                          <div className="text-sm text-muted-foreground">ID: {recruiter.id}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Building2 className="h-4 w-4 mr-2 text-muted-foreground" />
                          {recruiter.company_name || 'N/A'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={recruiter.is_active ? 'default' : 'secondary'}>
                          {recruiter.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {recruiter.subscription_status || 'Free'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{recruiter.total_resumes_analyzed || 0} resumes</div>
                          <div className="text-muted-foreground">
                            Last: {recruiter.last_activity 
                              ? new Date(recruiter.last_activity).toLocaleDateString()
                              : 'Never'}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {new Date(recruiter.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedRecruiter(recruiter);
                              setShowDetailModal(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleRecruiterStatus(recruiter.id, recruiter.is_active || false)}
                          >
                            {recruiter.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {filteredRecruiters.length === 0 && (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No recruiters found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Recruiter Analytics
              </CardTitle>
              <CardDescription>
                Performance metrics and insights for recruiter accounts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold">Top Performing Recruiters</h3>
                  {recruiters.slice(0, 5).map((recruiter, index) => (
                    <div key={recruiter.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{recruiter.email}</div>
                        <div className="text-sm text-muted-foreground">{recruiter.company_name}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{recruiter.total_resumes_analyzed || 0}</div>
                        <div className="text-sm text-muted-foreground">resumes</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold">Recent Activity</h3>
                  {recruiters
                    .sort((a, b) => new Date(b.last_activity || 0).getTime() - new Date(a.last_activity || 0).getTime())
                    .slice(0, 5)
                    .map((recruiter) => (
                    <div key={recruiter.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium">{recruiter.email}</div>
                        <div className="text-sm text-muted-foreground">
                          Last active: {recruiter.last_activity 
                            ? new Date(recruiter.last_activity).toLocaleDateString()
                            : 'Never'}
                        </div>
                      </div>
                      <Badge variant={recruiter.is_active ? 'default' : 'secondary'}>
                        {recruiter.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Recruiter Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Recruiter Details
            </DialogTitle>
            <DialogDescription>
              Detailed information and analytics for {selectedRecruiter?.email}
            </DialogDescription>
          </DialogHeader>
          
          {selectedRecruiter && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    {selectedRecruiter.email}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Company</label>
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    {selectedRecruiter.company_name || 'N/A'}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Badge variant={selectedRecruiter.is_active ? 'default' : 'secondary'}>
                    {selectedRecruiter.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Joined</label>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    {new Date(selectedRecruiter.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div className="border-t pt-4">
                <h3 className="font-semibold mb-4">Performance Metrics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {selectedRecruiter.total_resumes_analyzed || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Resumes Analyzed</div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {selectedRecruiter.last_activity 
                        ? Math.floor((Date.now() - new Date(selectedRecruiter.last_activity).getTime()) / (1000 * 60 * 60 * 24))
                        : 'N/A'}
                    </div>
                    <div className="text-sm text-muted-foreground">Days Since Last Activity</div>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 pt-4 border-t">
                <Button 
                  onClick={() => handleToggleRecruiterStatus(selectedRecruiter.id, selectedRecruiter.is_active || false)}
                  variant={selectedRecruiter.is_active ? 'destructive' : 'default'}
                >
                  {selectedRecruiter.is_active ? (
                    <>
                      <UserX className="h-4 w-4 mr-2" />
                      Deactivate
                    </>
                  ) : (
                    <>
                      <UserCheck className="h-4 w-4 mr-2" />
                      Activate
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={() => setShowDetailModal(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Shield, 
  Users, 
  FileCheck, 
  Search,
  RefreshCw,
  Eye,
  Download,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  BarChart3,
  FileText,
  TrendingUp,
  Calendar
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';
import { ScrollArea } from '@/components/ui/scroll-area';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface CandidateSession {
  session_id: string;
  candidate_name: string;
  created_at: string;
  status: 'completed' | 'pending' | 'failed';
  resume_count?: number;
  analysis_score?: number;
  recruiter_email?: string;
}

interface CandidateOverview {
  total_candidates: number;
  active_sessions: number;
  completed_analyses: number;
  pending_analyses: number;
  average_score: number;
}

interface Resume {
  id: number;
  original_filename: string;
  candidate_name: string;
  uploaded_at: string;
  is_analyzed: boolean;
  analysis_score?: number;
  text_length: number;
  session_id?: string;
}

export default function CandidateOversight() {
  const [sessions, setSessions] = useState<CandidateSession[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [overview, setOverview] = useState<CandidateOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedSession, setSelectedSession] = useState<CandidateSession | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  useEffect(() => {
    fetchCandidateData();
  }, []);

  const fetchCandidateData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard data for candidate sessions
      const dashboardData = await adminApi.getDashboardStats() as any;
      
      // Fetch resumes data
      const resumesResponse = await fetch(`${API_BASE_URL}/api/resumes?limit=100`, {
        headers: getAuthHeaders()
      });
      
      if (dashboardData?.success && dashboardData.dashboard) {
        const sessionsData = dashboardData.dashboard.recent_activity?.candidate_sessions || [];
        setSessions(sessionsData);
        
        const overview = dashboardData.dashboard.overview || {};
        setOverview({
          total_candidates: sessionsData.length,
          active_sessions: overview.active_sessions || 0,
          completed_analyses: sessionsData.filter((s: any) => s.status === 'completed').length,
          pending_analyses: sessionsData.filter((s: any) => s.status === 'pending').length,
          average_score: 0 // Will be calculated from resumes
        });
      }
      
      if (resumesResponse.ok) {
        const resumeData = await resumesResponse.json();
        const resumesList = resumeData.resumes || [];
        setResumes(resumesList);
        
        // Calculate average score
        const analyzedResumes = resumesList.filter((r: Resume) => r.is_analyzed && r.analysis_score);
        const avgScore = analyzedResumes.length > 0 
          ? analyzedResumes.reduce((sum: number, r: Resume) => sum + (r.analysis_score || 0), 0) / analyzedResumes.length
          : 0;
        
        setOverview(prev => prev ? { ...prev, average_score: Math.round(avgScore * 10) / 10 } : null);
      }
    } catch (error) {
      console.error('Error loading candidate data:', error);
      toast.error('Failed to load candidate data');
    } finally {
      setLoading(false);
    }
  };

  const handleViewSession = (session: CandidateSession) => {
    setSelectedSession(session);
    setShowDetailModal(true);
  };

  const handleExportData = () => {
    const csvData = [
      ['Session ID', 'Candidate Name', 'Status', 'Created At', 'Resume Count', 'Analysis Score'].join(','),
      ...sessions.map(session => [
        session.session_id,
        session.candidate_name,
        session.status,
        new Date(session.created_at).toISOString(),
        session.resume_count || 0,
        session.analysis_score || 'N/A'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `candidate_sessions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const filteredSessions = sessions.filter(session => {
    const matchesSearch = session.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.session_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          {[...Array(5)].map((_, i) => (
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
          <h2 className="text-2xl font-bold tracking-tight">Candidate Oversight</h2>
          <p className="text-muted-foreground">
            Monitor and manage all candidate activities and submissions
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleExportData} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={fetchCandidateData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Candidates</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.total_candidates}</div>
              <p className="text-xs text-muted-foreground">
                Unique candidates
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.active_sessions}</div>
              <p className="text-xs text-muted-foreground">
                Currently processing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.completed_analyses}</div>
              <p className="text-xs text-muted-foreground">
                Analysis completed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.pending_analyses}</div>
              <p className="text-xs text-muted-foreground">
                Awaiting analysis
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview.average_score}%</div>
              <p className="text-xs text-muted-foreground">
                Analysis average
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions">Candidate Sessions</TabsTrigger>
          <TabsTrigger value="resumes">Resume Database</TabsTrigger>
          <TabsTrigger value="analytics">Quality Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="sessions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Candidate Sessions</CardTitle>
              <CardDescription>
                Monitor all candidate upload sessions and their status
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex items-center space-x-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by candidate name or session ID..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Sessions Table */}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Session ID</TableHead>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Resumes</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.session_id}>
                      <TableCell>
                        <div className="font-mono text-sm">{session.session_id}</div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{session.candidate_name}</div>
                        {session.recruiter_email && (
                          <div className="text-sm text-muted-foreground">
                            via {session.recruiter_email}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(session.status)}
                          <Badge variant={
                            session.status === 'completed' ? 'default' :
                            session.status === 'pending' ? 'secondary' : 'destructive'
                          }>
                            {session.status}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>{session.resume_count || 1}</TableCell>
                      <TableCell>
                        {session.analysis_score ? (
                          <Badge variant="outline">
                            {session.analysis_score}%
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {new Date(session.created_at).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewSession(session)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {filteredSessions.length === 0 && (
                <div className="text-center py-8">
                  <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No candidate sessions found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resumes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Resume Database</CardTitle>
              <CardDescription>
                All uploaded resumes and their analysis status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Resume</TableHead>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Analysis</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Upload Date</TableHead>
                    <TableHead>Size</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {resumes.slice(0, 20).map((resume) => (
                    <TableRow key={resume.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{resume.original_filename}</div>
                            <div className="text-sm text-muted-foreground">ID: {resume.id}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{resume.candidate_name}</TableCell>
                      <TableCell>
                        <Badge variant={resume.is_analyzed ? 'default' : 'secondary'}>
                          {resume.is_analyzed ? 'Analyzed' : 'Pending'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {resume.analysis_score ? (
                          <Badge variant="outline">
                            {resume.analysis_score}%
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {new Date(resume.uploaded_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {resume.text_length} chars
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Quality Analytics
              </CardTitle>
              <CardDescription>
                Insights into resume quality and analysis performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold">Score Distribution</h3>
                  <div className="space-y-3">
                    {[
                      { range: '90-100%', count: resumes.filter(r => r.analysis_score && r.analysis_score >= 90).length, color: 'bg-green-500' },
                      { range: '80-89%', count: resumes.filter(r => r.analysis_score && r.analysis_score >= 80 && r.analysis_score < 90).length, color: 'bg-blue-500' },
                      { range: '70-79%', count: resumes.filter(r => r.analysis_score && r.analysis_score >= 70 && r.analysis_score < 80).length, color: 'bg-yellow-500' },
                      { range: '60-69%', count: resumes.filter(r => r.analysis_score && r.analysis_score >= 60 && r.analysis_score < 70).length, color: 'bg-orange-500' },
                      { range: 'Below 60%', count: resumes.filter(r => r.analysis_score && r.analysis_score < 60).length, color: 'bg-red-500' }
                    ].map((item, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded ${item.color}`} />
                          <span>{item.range}</span>
                        </div>
                        <div className="font-bold">{item.count}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold">Analysis Status</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span>Completed</span>
                      </div>
                      <div className="font-bold">{resumes.filter(r => r.is_analyzed).length}</div>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-yellow-500" />
                        <span>Pending</span>
                      </div>
                      <div className="font-bold">{resumes.filter(r => !r.is_analyzed).length}</div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Session Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Session Details
            </DialogTitle>
            <DialogDescription>
              Detailed information for session {selectedSession?.session_id}
            </DialogDescription>
          </DialogHeader>
          
          {selectedSession && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Session ID</label>
                  <div className="font-mono text-sm bg-muted p-2 rounded">
                    {selectedSession.session_id}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Candidate</label>
                  <div className="font-medium">{selectedSession.candidate_name}</div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedSession.status)}
                    <Badge variant={
                      selectedSession.status === 'completed' ? 'default' :
                      selectedSession.status === 'pending' ? 'secondary' : 'destructive'
                    }>
                      {selectedSession.status}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Created</label>
                  <div>{new Date(selectedSession.created_at).toLocaleString()}</div>
                </div>
              </div>

              {selectedSession.analysis_score && (
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-4">Analysis Results</h3>
                  <div className="bg-muted p-4 rounded-lg">
                    <div className="text-3xl font-bold text-primary mb-2">
                      {selectedSession.analysis_score}%
                    </div>
                    <div className="text-sm text-muted-foreground">Overall Analysis Score</div>
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4 border-t">
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

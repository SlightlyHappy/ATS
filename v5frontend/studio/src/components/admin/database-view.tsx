'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Database, 
  RefreshCw,
  FileText,
  Search,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  BarChart3,
  Eye
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface Resume {
  id: number;
  original_filename: string;
  candidate_name: string;
  uploaded_at: string;
  is_analyzed: boolean;
  analysis_score?: number;
  text_length: number;
}

interface ResumesResponse {
  resumes: Resume[];
  total: number;
}

interface SystemHealth {
  success: boolean;
  status: string;
  database_status: string;
  timestamp: string;
}

export default function DatabaseView() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalResumes, setTotalResumes] = useState(0);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [selectedResume, setSelectedResume] = useState<any>(null);
  const [showResumeModal, setShowResumeModal] = useState(false);
  const pageSize = 50;

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  useEffect(() => {
    fetchResumes();
    fetchSystemHealth();
  }, [currentPage]);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getResumes({
        skip: currentPage * pageSize,
        limit: pageSize,
        search: searchTerm || undefined
      }) as ResumesResponse;
      
      setResumes(data.resumes || []);
      setTotalResumes(data.total || 0);
    } catch (error) {
      console.error('Error loading resumes:', error);
      toast.error('Error loading resume data');
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const health = await adminApi.getSystemHealth() as SystemHealth;
      setSystemHealth(health);
    } catch (error) {
      console.error('Error loading system health:', error);
    }
  };

  const handleSearch = () => {
    setCurrentPage(0);
    fetchResumes();
  };

  const handleViewResume = async (resumeId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/resumes/${resumeId}`, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const resumeData = await response.json();
        setSelectedResume(resumeData);
        setShowResumeModal(true);
      } else {
        toast.error('Failed to load resume details');
      }
    } catch (error) {
      console.error('Error loading resume:', error);
      toast.error('Failed to load resume details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (resume: Resume) => {
    if (!resume.is_analyzed) {
      return <Badge variant="outline"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
    }
    
    const score = resume.analysis_score || 0;
    if (score >= 80) return <Badge variant="default"><CheckCircle className="h-3 w-3 mr-1" />Excellent</Badge>;
    if (score >= 60) return <Badge variant="secondary"><CheckCircle className="h-3 w-3 mr-1" />Good</Badge>;
    return <Badge variant="outline"><AlertTriangle className="h-3 w-3 mr-1" />Needs Review</Badge>;
  };

  const totalPages = Math.ceil(totalResumes / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Database Management</h2>
          <p className="text-muted-foreground">Monitor and manage resume data</p>
        </div>
        <Button onClick={() => { fetchResumes(); fetchSystemHealth(); }} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="resumes">Resume Data</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalResumes.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">Documents in database</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Analyzed</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {resumes.filter(r => r.is_analyzed).length.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">AI analysis completed</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {resumes.filter(r => !r.is_analyzed).length.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">Awaiting analysis</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Score</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {resumes.filter(r => r.analysis_score).length > 0
                    ? (
                        resumes
                          .filter(r => r.analysis_score)
                          .reduce((sum, r) => sum + (r.analysis_score || 0), 0) /
                        resumes.filter(r => r.analysis_score).length
                      ).toFixed(1)
                    : 'N/A'}
                </div>
                <p className="text-xs text-muted-foreground">Analysis score</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resumes" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Resume Database</CardTitle>
                  <CardDescription>All uploaded resumes and their analysis status</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search resumes..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-[250px]"
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                  </div>
                  <Button onClick={handleSearch} size="sm">
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center space-x-4 animate-pulse">
                      <div className="h-4 bg-muted rounded flex-1" />
                      <div className="h-4 bg-muted rounded w-24" />
                      <div className="h-4 bg-muted rounded w-16" />
                    </div>
                  ))}
                </div>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Candidate / Filename</TableHead>
                        <TableHead>Upload Date</TableHead>
                        <TableHead>Text Length</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {resumes.length > 0 ? (
                        resumes.map((resume) => (
                          <TableRow key={resume.id}>
                            <TableCell>
                              <div>
                                <div className="font-medium">
                                  {resume.candidate_name || 'Unknown Candidate'}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                  {resume.original_filename}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              {new Date(resume.uploaded_at).toLocaleDateString()}
                            </TableCell>
                            <TableCell>
                              {resume.text_length.toLocaleString()} chars
                            </TableCell>
                            <TableCell>
                              {getStatusBadge(resume)}
                            </TableCell>
                            <TableCell>
                              {resume.analysis_score ? (
                                <span className="font-medium">
                                  {resume.analysis_score.toFixed(1)}
                                </span>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewResume(resume.id)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8">
                            <div className="text-muted-foreground">
                              {searchTerm ? 'No resumes found matching your search.' : 'No resumes in database.'}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between mt-4">
                      <div className="text-sm text-muted-foreground">
                        Showing {currentPage * pageSize + 1} to {Math.min((currentPage + 1) * pageSize, totalResumes)} of {totalResumes} results
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                          disabled={currentPage === 0}
                        >
                          Previous
                        </Button>
                        <span className="text-sm">
                          Page {currentPage + 1} of {totalPages}
                        </span>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                          disabled={currentPage === totalPages - 1}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Real-time system status and database health</CardDescription>
            </CardHeader>
            <CardContent>
              {systemHealth ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-2">
                        <Database className="h-5 w-5 text-muted-foreground" />
                        <span className="font-medium">Database Status</span>
                      </div>
                      <Badge 
                        variant={systemHealth.database_status === 'connected' ? 'default' : 'destructive'}
                      >
                        {systemHealth.database_status}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-muted-foreground" />
                        <span className="font-medium">Overall Status</span>
                      </div>
                      <Badge 
                        variant={systemHealth.status === 'healthy' ? 'default' : 'destructive'}
                      >
                        {systemHealth.status}
                      </Badge>
                    </div>
                  </div>

                  <div className="text-sm text-muted-foreground">
                    Last checked: {new Date(systemHealth.timestamp).toLocaleString()}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Unable to load system health</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Resume Detail Modal */}
      <Dialog open={showResumeModal} onOpenChange={setShowResumeModal}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Resume Details: {selectedResume?.candidate_name}
            </DialogTitle>
            <DialogDescription>
              {selectedResume?.original_filename} • Uploaded: {selectedResume?.uploaded_at ? new Date(selectedResume.uploaded_at).toLocaleDateString() : 'N/A'}
            </DialogDescription>
          </DialogHeader>
          
          {selectedResume && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-6">
                {/* Resume Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {selectedResume.analysis_score ? `${selectedResume.analysis_score}%` : 'N/A'}
                    </div>
                    <div className="text-sm text-muted-foreground">Analysis Score</div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-2xl font-bold text-primary">{selectedResume.text_length || 0}</div>
                    <div className="text-sm text-muted-foreground">Text Length</div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <Badge variant={selectedResume.is_analyzed ? 'default' : 'secondary'}>
                      {selectedResume.is_analyzed ? 'Analyzed' : 'Pending'}
                    </Badge>
                    <div className="text-sm text-muted-foreground mt-1">Status</div>
                  </div>
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-2xl font-bold text-primary">
                      {selectedResume.analysis_results?.agent_results ? Object.keys(selectedResume.analysis_results.agent_results).length : 0}
                    </div>
                    <div className="text-sm text-muted-foreground">Analysis Sections</div>
                  </div>
                </div>

                {/* Analysis Results */}
                {selectedResume.analysis_results && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Analysis Results</h3>
                    
                    {selectedResume.analysis_results.agent_results && Object.entries(selectedResume.analysis_results.agent_results).map(([section, data]: [string, any]) => (
                      <Card key={section}>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base capitalize flex items-center justify-between">
                            {section.replace('_', ' ')}
                            <Badge variant="outline">{data.score}/100</Badge>
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          {data.insights && data.insights.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="font-medium text-sm">Key Insights:</h4>
                              <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                                {data.insights.map((insight: string, index: number) => (
                                  <li key={index}>{insight}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {data.extracted_data && (
                            <div className="mt-4 space-y-2">
                              <h4 className="font-medium text-sm">Extracted Data:</h4>
                              <div className="bg-muted p-3 rounded text-sm">
                                <pre className="whitespace-pre-wrap">{JSON.stringify(data.extracted_data, null, 2)}</pre>
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t">
                  <Button 
                    variant="outline" 
                    onClick={async () => {
                      try {
                        const response = await fetch(`${API_BASE_URL}/api/analyze/${selectedResume.id}`, {
                          method: 'POST',
                          headers: getAuthHeaders(),
                          body: JSON.stringify({ force_reanalyze: true })
                        });
                        
                        if (response.ok) {
                          toast.success('Reanalysis queued successfully');
                          setShowResumeModal(false);
                          fetchResumes();
                        } else {
                          toast.error('Failed to queue reanalysis');
                        }
                      } catch (error) {
                        toast.error('Failed to queue reanalysis');
                      }
                    }}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reanalyze
                  </Button>
                  
                  <Button 
                    variant="outline"
                    onClick={() => {
                      const resumeData = JSON.stringify(selectedResume, null, 2);
                      const blob = new Blob([resumeData], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `resume_${selectedResume.id}_analysis.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

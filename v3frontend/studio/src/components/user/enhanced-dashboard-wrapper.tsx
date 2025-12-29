"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { UserService, type UserDashboardData } from "@/services/user.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
// Temporarily disabled WebSocket import to prevent connection errors
// import { useWebSocket, useResumeUpdates } from "@/services/websocket.service";
import {
  FileText,
  Upload,
  BarChart3,
  TrendingUp,
  Clock,
  Star,
  ArrowRight,
  Eye,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Plus,
  Target,
  Award,
  Calendar,
  Activity,
  Info,
  Zap,
  Users,
  BookOpen
} from "lucide-react";
import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function EnhancedUserDashboard() {
  const { user } = useAuth();
  const { toast } = useToast();
  // Temporarily disable WebSocket to prevent connection errors
  // const webSocket = useWebSocket();
  const [data, setData] = useState<UserDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket integration for real-time updates - Temporarily disabled
  const resumeIds = data?.recentResumes.map(r => r.id) || [];
  // const resumeUpdates = useResumeUpdates(resumeIds);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('📊 Enhanced User Dashboard: Fetching dashboard data...');
      const response = await UserService.getDashboardData();
      
      if (response.success && response.data) {
        console.log('✅ Enhanced User Dashboard: Data loaded successfully');
        setData(response.data);
      } else {
        const errorMsg = response.error || 'Failed to load dashboard data';
        setError(errorMsg);
        
        // Set empty data structure for better UX
        const emptyData: UserDashboardData = {
          stats: {
            totalResumes: 0,
            pendingAnalysis: 0,
            completedAnalysis: 0,
            averageScore: 0,
          },
          recentResumes: [],
          trialInfo: user?.is_trial ? {
            resumesUsed: 0,
            resumeLimit: 5,
            legalUsed: 0,
            legalLimit: 3,
          } : undefined,
        };
        setData(emptyData);
      }
    } catch (error) {
      console.error('❌ Enhanced User Dashboard: Error loading data:', error);
      const errorMsg = error instanceof Error ? error.message : 'Failed to load dashboard data';
      setError(errorMsg);
      
      // Set empty data on error
      const emptyData: UserDashboardData = {
        stats: { totalResumes: 0, pendingAnalysis: 0, completedAnalysis: 0, averageScore: 0 },
        recentResumes: [],
        trialInfo: user?.is_trial ? { resumesUsed: 0, resumeLimit: 5, legalUsed: 0, legalLimit: 3 } : undefined,
      };
      setData(emptyData);
      
      toast({
        title: "Connection Error",
        description: errorMsg,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadDashboardData();
    setIsRefreshing(false);
    
    if (!error) {
      toast({
        title: "Success",
        description: "Dashboard refreshed successfully.",
      });
    }
  };

  useEffect(() => {
    loadDashboardData();

    // WebSocket notifications - Temporarily disabled
    // const handleNotification = (notification: any) => {
    //   toast({
    //     title: notification.title,
    //     description: notification.message,
    //     variant: notification.type === 'error' ? 'destructive' : 'default',
    //   });
    // };

    // webSocket.on('notification', handleNotification);

    // return () => {
    //   webSocket.off('notification', handleNotification);
    // };
  }, [user]);

  // Handle real-time resume updates - Temporarily disabled
  // useEffect(() => {
  //   if (resumeUpdates && data?.recentResumes) {
  //     const updatedResumes = data.recentResumes.map(resume => {
  //       const update = resumeUpdates[resume.id];
  //       if (update) {
  //         return {
  //           ...resume,
  //           status: update.status,
  //           score: update.analysis_result?.score || resume.score
  //         };
  //       }
  //       return resume;
  //     });

  //     if (JSON.stringify(updatedResumes) !== JSON.stringify(data.recentResumes)) {
  //       setData(prev => prev ? { ...prev, recentResumes: updatedResumes } : null);
        
  //       // Show notification for completed resumes
  //       Object.values(resumeUpdates).forEach(update => {
  //         if (update.status === 'completed') {
  //           toast({
  //             title: "Resume Analysis Complete",
  //             description: `Your resume has been analyzed with a score of ${update.analysis_result?.score || 'N/A'}`,
  //           });
  //         }
  //       });
  //     }
  //   }
  // }, [resumeUpdates, data?.recentResumes]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Completed
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="secondary" className="gap-1">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Processing
          </Badge>
        );
      case 'pending':
        return (
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getScoreBadge = (score?: number) => {
    if (!score) return null;
    
    if (score >= 80) {
      return <Badge variant="default" className="bg-green-100 text-green-800">{score}/100</Badge>;
    } else if (score >= 60) {
      return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">{score}/100</Badge>;
    } else {
      return <Badge variant="destructive" className="bg-red-100 text-red-800">{score}/100</Badge>;
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Dashboard"
          description="Welcome to your HR toolkit dashboard"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Dashboard"
          description="Welcome to your HR toolkit dashboard"
        />
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard data. Please try refreshing the page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back, ${user?.name || 'User'}!`}
        description="Here's your comprehensive dashboard overview and analytics"
        actions={
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleRefresh} 
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button asChild className="gap-2">
              <Link href="/user/submit">
                <Upload className="h-4 w-4" />
                Upload Resume
              </Link>
            </Button>
          </div>
        }
      />

      {/* Connection Status Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error} - Showing cached data or empty state.
          </AlertDescription>
        </Alert>
      )}

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.totalResumes}</div>
            <p className="text-xs text-muted-foreground">
              {data.stats.pendingAnalysis > 0 && (
                <span className="text-yellow-600">
                  {data.stats.pendingAnalysis} pending analysis
                </span>
              )}
              {data.stats.pendingAnalysis === 0 && data.stats.totalResumes > 0 && (
                <span className="text-green-600">All analyzed</span>
              )}
              {data.stats.totalResumes === 0 && (
                <span className="text-gray-600">Get started by uploading</span>
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Analysis</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.completedAnalysis}</div>
            <p className="text-xs text-muted-foreground">
              Success rate: {data.stats.totalResumes > 0 
                ? Math.round((data.stats.completedAnalysis / data.stats.totalResumes) * 100)
                : 0}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.stats.averageScore > 0 ? `${data.stats.averageScore}/100` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {data.stats.averageScore >= 80 && "Excellent performance"}
              {data.stats.averageScore >= 60 && data.stats.averageScore < 80 && "Good progress"}
              {data.stats.averageScore > 0 && data.stats.averageScore < 60 && "Room for improvement"}
              {data.stats.averageScore === 0 && "No scores yet"}
            </p>
          </CardContent>
        </Card>

        {/* Trial Info Card - Hidden for now */}
        {/* {data.trialInfo && (
          <Card className="border-orange-200 bg-orange-50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trial Usage</CardTitle>
              <Target className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Resumes</span>
                    <span>{data.trialInfo.resumesUsed}/{data.trialInfo.resumeLimit}</span>
                  </div>
                  <Progress 
                    value={(data.trialInfo.resumesUsed / data.trialInfo.resumeLimit) * 100} 
                    className="h-2"
                  />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span>Legal Queries</span>
                    <span>{data.trialInfo.legalUsed}/{data.trialInfo.legalLimit}</span>
                  </div>
                  <Progress 
                    value={(data.trialInfo.legalUsed / data.trialInfo.legalLimit) * 100} 
                    className="h-2"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )} */}
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="resumes">Recent Resumes</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Recent Resumes Quick View */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Recent Activity
                </div>
                {data.recentResumes.length > 0 && (
                  <Button variant="outline" size="sm" asChild>
                    <Link href="/user/my-resumes">
                      View All <ArrowRight className="h-4 w-4 ml-1" />
                    </Link>
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {data.recentResumes.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No resumes yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Upload your first resume to get started with AI-powered analysis
                  </p>
                  <Button asChild>
                    <Link href="/user/submit">
                      <Plus className="h-4 w-4 mr-2" />
                      Upload Resume
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.recentResumes.slice(0, 5).map((resume) => (
                    <div key={resume.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-full bg-blue-100">
                          <FileText className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{resume.filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(resume.uploadDate).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {resume.score && getScoreBadge(resume.score)}
                        {getStatusBadge(resume.status)}
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resumes" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>All Resumes</CardTitle>
              <CardDescription>
                Manage and view analysis results for all your uploaded resumes
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.recentResumes.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No resumes uploaded yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Filename</TableHead>
                      <TableHead>Upload Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.recentResumes.map((resume) => (
                      <TableRow key={resume.id}>
                        <TableCell className="font-medium">{resume.filename}</TableCell>
                        <TableCell>{new Date(resume.uploadDate).toLocaleDateString()}</TableCell>
                        <TableCell>{getStatusBadge(resume.status)}</TableCell>
                        <TableCell>{resume.score ? getScoreBadge(resume.score) : 'N/A'}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Performance Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {data.stats.averageScore > 0 ? (
                  <>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Average Score</span>
                        <span className="text-sm font-medium">{data.stats.averageScore}/100</span>
                      </div>
                      <Progress 
                        value={data.stats.averageScore} 
                        className={`h-2 ${getProgressColor(data.stats.averageScore)}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Completion Rate</span>
                        <span className="text-sm font-medium">
                          {Math.round((data.stats.completedAnalysis / data.stats.totalResumes) * 100)}%
                        </span>
                      </div>
                      <Progress 
                        value={(data.stats.completedAnalysis / data.stats.totalResumes) * 100} 
                        className="h-2"
                      />
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4" />
                    <p>Analytics will appear after you upload and analyze resumes</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button asChild className="w-full justify-start">
                  <Link href="/user/submit">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload New Resume
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link href="/user/my-resumes">
                    <FileText className="h-4 w-4 mr-2" />
                    View All Resumes
                  </Link>
                </Button>
                <Button variant="outline" asChild className="w-full justify-start">
                  <Link href="/user/profile">
                    <Users className="h-4 w-4 mr-2" />
                    Update Profile
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

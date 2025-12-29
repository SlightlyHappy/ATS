"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  FileText,
  Upload,
  BarChart3,
  TrendingUp,
  Clock,
  Star,
  ArrowRight,
  Eye,
  ArrowUpRight,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Plus,
  Target,
  Award,
  Calendar,
  Activity
} from "lucide-react";
import Link from "next/link";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { UserService, type UserDashboardData, type Resume } from "@/services/user.service";
import { useToast } from "@/hooks/use-toast";
import { format, formatDistanceToNow } from "date-fns";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export default function UserDashboardPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [dashboardData, setDashboardData] = useState<UserDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const response = await UserService.getDashboardData();
      
      if (response.success && response.data) {
        setDashboardData(response.data);
      } else {
        // Handle API error - set empty data structure instead of mock data
        console.warn("User dashboard API returned no data or failed:", response);
        const emptyData: UserDashboardData = {
          stats: {
            totalResumes: 0,
            pendingAnalysis: 0,
            completedAnalysis: 0,
            averageScore: 0,
          },
          recentResumes: [],
          trialInfo: {
            resumesUsed: 0,
            resumeLimit: 10, // Default trial limit
            legalUsed: 0,
            legalLimit: 5,   // Default trial limit
          },
        };
        setDashboardData(emptyData);
        
        // Show user-friendly message for non-connection errors
        if (response.message && !response.message.includes('network') && !response.message.includes('connection')) {
          toast({
            title: "Welcome!",
            description: response.message || "Get started by uploading your first resume.",
            variant: "default",
          });
        }
      }
    } catch (error) {
      console.error("Error loading dashboard data:", error);
      toast({
        title: "Error",
        description: "Failed to load dashboard data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await loadDashboardData();
      toast({
        title: "Success",
        description: "Dashboard refreshed successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to refresh dashboard.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "processing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4" />;
      case "processing":
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "failed":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-800 border-green-200";
    if (score >= 60) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-red-100 text-red-800 border-red-200";
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
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-8">
        <PageHeader
          title="Dashboard"
          description="Welcome to your HR toolkit dashboard"
        />
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to Load Dashboard</h3>
              <p className="text-muted-foreground mb-4">
                Unable to load your dashboard data. Please try refreshing.
              </p>
              <Button onClick={loadDashboardData}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare chart data
  const statusData = [
    { name: 'Completed', value: dashboardData.stats.completedAnalysis, color: '#00C49F' },
    { name: 'Pending', value: dashboardData.stats.pendingAnalysis, color: '#FFBB28' },
    { name: 'Processing', value: dashboardData.stats.totalResumes - dashboardData.stats.completedAnalysis - dashboardData.stats.pendingAnalysis, color: '#0088FE' },
  ].filter(item => item.value > 0);

  const progressData = [
    { name: 'Resume Limit', used: dashboardData.trialInfo?.resumesUsed || 0, limit: dashboardData.trialInfo?.resumeLimit || 10 },
    { name: 'Legal Queries', used: dashboardData.trialInfo?.legalUsed || 0, limit: dashboardData.trialInfo?.legalLimit || 5 },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back, ${user?.name || 'User'}!`}
        description="Track your resume analysis progress and HR toolkit usage"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button asChild className="gap-2">
              <Link href="/user/submit">
                <Plus className="h-4 w-4" />
                Upload Resume
              </Link>
            </Button>
          </div>
        }
      />

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.stats.totalResumes}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData.stats.completedAnalysis} analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getScoreColor(dashboardData.stats.averageScore)}`}>
              {dashboardData.stats.averageScore.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData.stats.averageScore >= 75 ? "Excellent!" : dashboardData.stats.averageScore >= 60 ? "Good progress" : "Room for improvement"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Analysis</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.stats.pendingAnalysis}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData.stats.pendingAnalysis === 0 ? "All caught up!" : "In queue"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.stats.totalResumes > 0 
                ? Math.round((dashboardData.stats.completedAnalysis / dashboardData.stats.totalResumes) * 100)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData.stats.completedAnalysis} of {dashboardData.stats.totalResumes} resumes
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resume Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Resume Status Distribution</CardTitle>
            <CardDescription>Current status of your uploaded resumes</CardDescription>
          </CardHeader>
          <CardContent>
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[250px] text-muted-foreground">
                <div className="text-center">
                  <FileText className="h-12 w-12 mx-auto mb-2" />
                  <p>No resumes uploaded yet</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Usage Limits */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Overview</CardTitle>
            <CardDescription>Track your trial limits and usage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {progressData.map((item) => (
              <div key={item.name} className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{item.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {item.used}/{item.limit}
                  </span>
                </div>
                <Progress 
                  value={(item.used / item.limit) * 100} 
                  className={`${item.used >= item.limit ? 'bg-red-100' : ''}`}
                />
                <div className="flex justify-between items-center text-xs text-muted-foreground">
                  <span>{item.limit - item.used} remaining</span>
                  <span>{Math.round((item.used / item.limit) * 100)}% used</span>
                </div>
              </div>
            ))}
            
            {(dashboardData.trialInfo?.resumesUsed || 0) >= (dashboardData.trialInfo?.resumeLimit || 10) && (
              <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-center gap-2 text-orange-800">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm font-medium">Resume limit reached</span>
                </div>
                <p className="text-xs text-orange-700 mt-1">
                  Upgrade your account to analyze more resumes
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <Link href="/user/submit">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Upload className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <CardTitle className="text-base">Upload Resume</CardTitle>
                  <CardDescription className="text-sm">
                    Submit a new resume for analysis
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Link>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <Link href="/user/my-resumes">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <CardTitle className="text-base">View Analysis</CardTitle>
                  <CardDescription className="text-sm">
                    Review your resume analysis results
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Link>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer">
          <Link href="/user/profile">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Activity className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <CardTitle className="text-base">Profile Settings</CardTitle>
                  <CardDescription className="text-sm">
                    Manage your account preferences
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Link>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Resume Activity</CardTitle>
              <CardDescription>Your latest resume submissions and analysis results</CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href="/user/my-resumes" className="gap-2">
                View All
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {dashboardData.recentResumes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No resumes yet</h3>
              <p className="mb-4">Upload your first resume to get started with AI-powered analysis</p>
              <Button asChild>
                <Link href="/user/submit">Upload Resume</Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Resume</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboardData.recentResumes.map((resume) => (
                  <TableRow key={resume.id} className="hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-muted rounded">
                          <FileText className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-medium">{resume.filename}</div>
                          <div className="text-sm text-muted-foreground">PDF Document</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(resume.status)}
                        <Badge className={getStatusColor(resume.status)}>
                          {resume.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      {resume.score ? (
                        <Badge className={getScoreBadgeColor(resume.score)}>
                          {resume.score}%
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm">
                          {format(new Date(resume.uploadDate), "MMM dd, yyyy")}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(resume.uploadDate), { addSuffix: true })}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {resume.status === "completed" ? (
                        <Button variant="ghost" size="sm" asChild>
                          <Link href={`/user/my-resumes/${resume.id}`} className="gap-2">
                            <Eye className="h-4 w-4" />
                            View
                          </Link>
                        </Button>
                      ) : (
                        <Button variant="ghost" size="sm" disabled>
                          <Clock className="h-4 w-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
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
import {
  Users,
  FileText,
  Briefcase,
  Clock,
  ArrowUpRight,
} from "lucide-react";
import PageHeader from "@/components/page-header";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { fetchDashboardStats, apiClient } from "@/services/api";
import { DashboardCharts } from "./dashboard-charts";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { useLoading } from "@/components/loading/loading-provider";

interface DashboardData {
  stats: {
    totalResumes: number;
    totalResumesChange: string;
    newCandidates: number;
    interviewsScheduled: number;
    interviewsScheduledChange: string;
    pendingReview: number;
    // Additional backend stats
    databaseConnections: number;
    systemHealth: string;
    lastUpdated: string;
  };
  recent: {
    id: string;
    filename: string;
    user_id: string;
    status: string;
    overall_score?: number;
    upload_date: string;
  }[];
  analytics: {
    avg_scores: number;
    counts_by_status: Record<string, number>;
    top_skills: string[];
    recent_uploads_count: number;
  };
}


export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { setIsLoading: setGlobalLoading } = useLoading();

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setGlobalLoading(true);
      try {
        // Load data from multiple real endpoints as per FRONTEND_SPEC.md
        const [dashboardResponse, analyticsResponse, resumesResponse] = await Promise.all([
          apiClient.getDashboardStats(),
          apiClient.getResumeAnalytics(),
          apiClient.getResumes({ page: 1, page_size: 5 }) // Get recent 5 resumes
        ]);
        
        if (dashboardResponse.success) {
          const dashboardStats = dashboardResponse.data?.stats;
          const analyticsStats = analyticsResponse.success ? analyticsResponse.data?.stats : null;
          const recentResumes = resumesResponse.success ? (resumesResponse.data?.resumes || []).slice(0, 5) : [];
          
          // Calculate trends - ready for historical data when backend supports it
          const calculatePercentageChange = (current: number, previous?: number): string => {
            // If no historical data available, show neutral state
            if (previous === undefined || previous === null) {
              return current > 0 ? "+0%" : "0%";
            }
            
            if (previous === 0) return current > 0 ? "+100%" : "0%";
            const change = ((current - previous) / previous) * 100;
            const sign = change >= 0 ? "+" : "";
            return `${sign}${Math.round(change)}%`;
          };

          // Extract current data
          const currentTotalResumes = dashboardStats?.users?.total_analyzed || 0;
          const currentInterviews = 0; // Will be populated when interviews endpoint is added
          
          // Historical data - to be populated when backend provides it
          const previousTotalResumes = (dashboardStats as any)?.users?.total_analyzed_previous_month;
          const previousInterviews = (dashboardStats as any)?.interviews?.scheduled_previous_month;
          
          // Calculate changes with graceful fallback
          const totalResumesChange = calculatePercentageChange(currentTotalResumes, previousTotalResumes);
          const interviewsChange = calculatePercentageChange(currentInterviews, previousInterviews);

          const transformedData: DashboardData = {
            stats: {
              // Real data from /api/admin/dashboard-stats with calculated trends
              totalResumes: currentTotalResumes,
              totalResumesChange: totalResumesChange,
              newCandidates: recentResumes.length,
              interviewsScheduled: currentInterviews,
              interviewsScheduledChange: interviewsChange,
              pendingReview: dashboardStats?.users?.at_resume_limit || 0,
              // Additional real backend data
              databaseConnections: dashboardStats?.database?.connections || 0,
              systemHealth: dashboardStats?.system?.timestamp ? 'Healthy' : 'Unknown',
              lastUpdated: dashboardStats?.system?.timestamp || new Date().toISOString(),
            },
            // Real recent submissions from /api/admin/resumes
            recent: recentResumes.map((resume: any) => ({
              id: resume.id,
              filename: resume.filename,
              user_id: resume.user_id,
              status: resume.processing_status || 'pending',
              overall_score: resume.overall_score,
              upload_date: resume.upload_date,
            })),
            // Real analytics from /api/admin/resumes/analytics
            analytics: analyticsStats || {
              avg_scores: 0,
              counts_by_status: {},
              top_skills: [],
              recent_uploads_count: 0,
            }
          };
          
          setData(transformedData);
        } else {
          throw new Error('Failed to load dashboard data');
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
        // Set empty data structure on error
        setData({
          stats: {
            totalResumes: 0,
            totalResumesChange: "0%",
            newCandidates: 0,
            interviewsScheduled: 0,
            interviewsScheduledChange: "0%",
            pendingReview: 0,
            databaseConnections: 0,
            systemHealth: 'Error',
            lastUpdated: new Date().toISOString(),
          },
          recent: [],
          analytics: {
            avg_scores: 0,
            counts_by_status: {},
            top_skills: [],
            recent_uploads_count: 0,
          }
        });
      } finally {
        setIsLoading(false);
        setGlobalLoading(false);
      }
    }
    loadData();
  }, [setGlobalLoading]);

  if (isLoading || !data) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader title="Dashboard" />
        <DashboardSkeleton />
      </div>
    );
  }

  const { stats, recent, analytics } = data;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Dashboard" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Resumes
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalResumes}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totalResumesChange} from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              New Candidates
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+{stats.newCandidates}</div>
            <p className="text-xs text-muted-foreground">
              in the last 7 days
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Interviews Scheduled
            </CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.interviewsScheduled}</div>
            <p className="text-xs text-muted-foreground">
              {stats.interviewsScheduledChange} from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingReview}</div>
            <p className="text-xs text-muted-foreground">
              awaiting action
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-12 lg:col-span-4">
           <CardHeader className="flex flex-row items-center">
             <div className="grid gap-2">
              <CardTitle>Recent Submissions</CardTitle>
              <CardDescription>
                New resumes that have been submitted for review.
              </CardDescription>
            </div>
            <Button asChild size="sm" className="ml-auto gap-1">
              <Link href="/resumes">
                View All
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Candidate</TableHead>
                  <TableHead className="hidden sm:table-cell">
                    Status
                  </TableHead>
                  <TableHead className="hidden md:table-cell">
                    AI Score
                  </TableHead>
                  <TableHead className="text-right">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent.map((submission) => (
                  <TableRow key={submission.id}>
                    <TableCell>
                      <div className="flex items-center gap-4">
                        <Avatar className="hidden h-9 w-9 sm:flex">
                          <AvatarImage 
                            src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(submission.filename)}&backgroundColor=c0392b,e74c3c,9b59b6,8e44ad,2980b9,3498db,1abc9c,16a085,27ae60,2ecc71,f1c40f,f39c12,e67e22,d35400,95a5a6,7f8c8d`} 
                            alt={`Avatar for ${submission.filename}`}
                            onError={(e) => {
                              // Fallback to initials if external service fails
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                          <AvatarFallback className="bg-primary/10 text-primary font-medium">
                            {submission.filename.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="font-medium">{submission.filename}</div>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      <Badge
                        variant={
                          submission.status === "pending"
                            ? "secondary"
                            : submission.status === "completed"
                            ? "default"
                            : "destructive"
                        }
                        className="capitalize"
                      >
                        {submission.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {submission.overall_score ? `${submission.overall_score}%` : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      {new Date(submission.upload_date).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        <DashboardCharts chartData={analytics} />
      </div>
    </div>
  );
}
